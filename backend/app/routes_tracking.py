from datetime import date, datetime, timedelta, timezone
from uuid import UUID, uuid1
from fastapi import APIRouter, Depends, HTTPException, Query
from cassandra.query import BatchStatement
from app.database import db
from app.schemas import GPSIngest, AlertAction
from app.security import require_role
from app.services import as_utc, check_geofence, row_to_dict, trip_write_lock

router = APIRouter(prefix="/api/tracking", tags=["Tracking"], dependencies=[Depends(db.require_ready)])
read_role = require_role(["ADMIN", "DISPATCHER", "VIEWER"])
write_role = require_role(["ADMIN", "DISPATCHER"])
def owned_vehicle(vehicle_id, company):
    row = db.execute("SELECT * FROM vehicles_by_id WHERE vehicle_id = %s", (vehicle_id,)).one()
    if not row or row.company_id != company:
        raise HTTPException(404, "Không tìm thấy xe trong công ty")
    return row

@router.get("/latest")
def get_latest_locations(user=Depends(read_role)):
    rows = db.execute(db.prepared_statements["latest_locations"], (user["company_id"],))
    return [row_to_dict(row) for row in rows if row.event_time is not None]

@router.get("/history")
def get_vehicle_history(vehicle_id: str, date_str: date | None = None,
                        t1: datetime | None = None, t2: datetime | None = None,
                        limit: int = Query(500, ge=1, le=2000),
                        offset: int = Query(0, ge=0, le=10000), user=Depends(read_role)):
    owned_vehicle(vehicle_id, user["company_id"])
    if date_str and (t1 or t2):
        raise HTTPException(422, "Chọn ngày hoặc khoảng t1/t2")
    if date_str:
        t1 = datetime.combine(date_str, datetime.min.time(), timezone.utc)
        t2 = t1 + timedelta(days=1) - timedelta(milliseconds=1)
    if not t1 or not t2 or t1.tzinfo is None or t2.tzinfo is None:
        raise HTTPException(422, "Cần t1/t2 có timezone hoặc date_str")
    t1, t2 = as_utc(t1), as_utc(t2)
    if t2 < t1 or t2 - t1 > timedelta(days=7):
        raise HTTPException(422, "Khoảng lịch sử tối đa 7 ngày")
    points, day = [], t1.date()
    while day <= t2.date():
        rows = db.execute(
            "SELECT * FROM location_events_by_vehicle_day WHERE vehicle_id = %s AND event_date = %s "
            "AND event_time >= %s AND event_time <= %s ORDER BY event_time ASC LIMIT %s",
            (vehicle_id, day, t1, t2, offset + limit + 1),
        )
        points.extend(row_to_dict(row) for row in rows)
        day += timedelta(days=1)
    points.sort(key=lambda p: (p["event_time"], str(p["event_id"])))
    selected = points[offset:offset + limit]
    return {"points": selected, "next_offset": offset + limit if len(points) > offset + limit else None}

@router.get("/recent-moving")
def recent_moving(minutes: int = Query(15, ge=1, le=2880), user=Depends(read_role)):
    now = datetime.now(timezone.utc)
    since = now - timedelta(minutes=minutes)
    hour = since.replace(minute=0, second=0, microsecond=0)
    vehicles = {}
    while hour <= now:
        rows = db.execute(
            "SELECT event_time,vehicle_id,speed FROM vehicle_activity_by_hour "
            "WHERE company_id = %s AND activity_date = %s AND hour = %s AND event_time >= %s AND event_time <= %s",
            (user["company_id"], hour.date(), hour.hour, since, now),
        )
        for row in rows:
            if row.speed > 0 and (row.vehicle_id not in vehicles or as_utc(row.event_time) > vehicles[row.vehicle_id]["event_time"]):
                vehicles[row.vehicle_id] = row_to_dict(row)
        hour += timedelta(hours=1)
    return list(vehicles.values())

def create_alert(company, vehicle, trip_id, alert_type, details, now):
    # Bounded demo lookup. Older unresolved alerts need persistent per-vehicle state in P6.
    for day in (now.date(), now.date() - timedelta(days=1)):
        rows = db.execute(db.prepared_statements["alerts_by_day"], (company, day))
        if any(row.vehicle_id == vehicle.vehicle_id and row.alert_type == alert_type
               and (row.status != "RESOLVED" or (now - as_utc(row.created_at)).total_seconds() < 60)
               for row in rows):
            return
    alert_id = uuid1()
    values = (company, now.date(), now, alert_id, vehicle.vehicle_id, trip_id, alert_type, "HIGH", "OPEN", details)
    batch = BatchStatement()
    batch.add("INSERT INTO alerts_by_company_day (company_id,alert_date,created_at,alert_id,vehicle_id,trip_id,alert_type,severity,status,details) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", values)
    batch.add("INSERT INTO alerts_by_id (company_id,alert_date,created_at,alert_id,vehicle_id,trip_id,alert_type,severity,status,details) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", values)
    db.execute(batch)

@router.post("/ingest")
def ingest_gps(req: GPSIngest, user=Depends(write_role)):
    company = user["company_id"]
    ev_time = req.timestamp.astimezone(timezone.utc)
    ev_time = ev_time.replace(microsecond=ev_time.microsecond // 1000 * 1000)
    now = datetime.now(timezone.utc)
    if ev_time > now + timedelta(minutes=5) or ev_time < now - timedelta(days=90):
        raise HTTPException(422, "GPS nằm ngoài khoảng thời gian cho phép")
    # Bind the ID to its canonical millisecond so retries cannot change partition keys.
    id_millis = (req.event_id.time - 0x01B21DD213814000) // 10000
    if round(ev_time.timestamp() * 1000) != id_millis:
        raise HTTPException(422, "event_id và timestamp phải cùng mốc thời gian")
    with trip_write_lock:
        vehicle = owned_vehicle(req.vehicle_id, company)
        if vehicle.status in ("INACTIVE", "MAINTENANCE"):
            raise HTTPException(409, "Xe đã ngừng hoạt động hoặc đang bảo trì")
        existing = db.execute(
            "SELECT lat,lng,speed,heading,trip_id FROM location_events_by_vehicle_day "
            "WHERE vehicle_id = %s AND event_date = %s AND event_time = %s AND event_id = %s",
            (req.vehicle_id, ev_time.date(), ev_time, req.event_id),
        ).one()
        if existing and (existing.lat, existing.lng, existing.speed, existing.heading) != (req.lat, req.lng, req.speed, req.heading):
            raise HTTPException(409, "Không được thay đổi nội dung event đã ghi")
        latest = db.execute("SELECT * FROM latest_locations_by_company WHERE company_id = %s AND vehicle_id = %s", (company, req.vehicle_id)).one()
        active_trip_id = None
        trip_id = None
        if latest and latest.trip_id:
            trip = db.execute("SELECT company_id,vehicle_id,status,start_time FROM trips_by_id WHERE trip_id = %s", (latest.trip_id,)).one()
            if trip and trip.company_id == company and trip.vehicle_id == req.vehicle_id and trip.status == "IN_PROGRESS":
                active_trip_id = latest.trip_id
                if ev_time >= as_utc(trip.start_time):
                    trip_id = active_trip_id
        if existing:
            trip_id = existing.trip_id
        db.execute(
            "INSERT INTO location_events_by_vehicle_day (vehicle_id,event_date,event_time,event_id,lat,lng,speed,heading,trip_id,company_id) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (req.vehicle_id,ev_time.date(),ev_time,req.event_id,req.lat,req.lng,req.speed,req.heading,trip_id,company),
        )
        db.execute("INSERT INTO vehicle_activity_by_hour (company_id,activity_date,hour,event_time,vehicle_id,event_id,speed) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                   (company,ev_time.date(),ev_time.hour,ev_time,req.vehicle_id,req.event_id,req.speed))
        fresh = not latest or latest.event_time is None or ev_time > as_utc(latest.event_time)
        if fresh:
            values = (ev_time,req.lat,req.lng,req.speed,req.heading,active_trip_id,"RUNNING" if req.speed > 0 else "IDLE",company,req.vehicle_id)
            if latest and latest.event_time is not None:
                result = db.execute("UPDATE latest_locations_by_company SET event_time=%s,lat=%s,lng=%s,speed=%s,heading=%s,trip_id=%s,status=%s WHERE company_id=%s AND vehicle_id=%s IF event_time < %s", values + (ev_time,)).one()
                fresh = bool(result and result.applied)
            elif latest:
                db.execute("UPDATE latest_locations_by_company SET event_time=%s,lat=%s,lng=%s,speed=%s,heading=%s,trip_id=%s,status=%s WHERE company_id=%s AND vehicle_id=%s", values)
            else:
                result = db.execute("INSERT INTO latest_locations_by_company (event_time,lat,lng,speed,heading,trip_id,status,company_id,vehicle_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) IF NOT EXISTS", values).one()
                fresh = bool(result and result.applied)
        if fresh:
            if req.speed > vehicle.speed_limit:
                create_alert(company, vehicle, trip_id, "OVERSPEED", f"Vận tốc {req.speed} > giới hạn {vehicle.speed_limit} km/h", now)
            if not check_geofence(req.vehicle_id, req.lat, req.lng):
                create_alert(company, vehicle, trip_id, "GEOFENCE_EXIT", "Xe ở ngoài bounding box cho phép", now)
    return {"status": "success", "event_id": str(req.event_id), "duplicate": existing is not None, "latest_updated": fresh}

@router.get("/alerts")
def get_alerts(date_str: date | None = None, user=Depends(read_role)):
    rows = db.execute(db.prepared_statements["alerts_by_day"], (user["company_id"], date_str or datetime.now(timezone.utc).date()))
    return [row_to_dict(row) for row in rows]

@router.post("/alerts/action")
def alert_action(req: AlertAction, user=Depends(write_role)):
    row = db.execute("SELECT * FROM alerts_by_id WHERE alert_id = %s", (req.alert_id,)).one()
    if not row or row.company_id != user["company_id"]:
        raise HTTPException(404, "Không tìm thấy cảnh báo")
    if row.status == "RESOLVED" and req.status != "RESOLVED":
        raise HTTPException(409, "Cảnh báo đã xử lý")
    now = datetime.now(timezone.utc)
    batch = BatchStatement()
    batch.add("UPDATE alerts_by_id SET status=%s,resolved_by=%s,resolved_at=%s WHERE alert_id=%s",
              (req.status,user["username"] if req.status == "RESOLVED" else None,now if req.status == "RESOLVED" else None,req.alert_id))
    batch.add("UPDATE alerts_by_company_day SET status=%s WHERE company_id=%s AND alert_date=%s AND created_at=%s AND alert_id=%s",
              (req.status,row.company_id,row.alert_date,row.created_at,req.alert_id))
    db.execute(batch)
    return {"alert_id": str(req.alert_id), "status": req.status}

@router.get("/report/monthly-driver")
def get_monthly_driver_report(driver_id: str, month_str: str = Query(pattern=r"^\d{4}-(0[1-9]|1[0-2])$"), user=Depends(read_role)):
    driver = db.execute("SELECT company_id FROM drivers_by_id WHERE driver_id = %s", (driver_id,)).one()
    if not driver or driver.company_id != user["company_id"]:
        raise HTTPException(404, "Không tìm thấy tài xế")
    rows = db.execute(db.prepared_statements["trips_by_driver_month"], (driver_id, month_str))
    trips = [row_to_dict(row) for row in rows if row.status == "COMPLETED"]
    return {"driver_id": driver_id, "year_month": month_str, "total_trips": len(trips),
            "total_distance_km": round(sum(row["distance_km"] or 0 for row in trips),2), "trips": trips}
