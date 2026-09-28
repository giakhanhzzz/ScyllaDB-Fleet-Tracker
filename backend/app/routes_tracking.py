from fastapi import APIRouter, HTTPException, Depends
from app.schemas import GPSIngest, AlertAction
from app.security import require_role
from app.database import db
from app.config import settings
from app.services import check_geofence
from datetime import datetime, timezone, date
import uuid

try:
    from cassandra.util import uuid_from_time
except ImportError:
    uuid_from_time = lambda t: uuid.uuid4()

router = APIRouter(prefix="/api/tracking", tags=["Live Tracking & History"])

@router.get("/latest")
def get_latest_locations(user=Depends(require_role(["ADMIN", "DISPATCHER", "VIEWER"]))):
    # Q8: Vị trí mới nhất của tất cả xe
    if not db.session:
        return []
    rows = db.session.execute(db.prepared_statements["latest_locations"], (settings.COMPANY_ID,))
    return [dict(r._asdict()) for r in rows]

@router.get("/history")
def get_vehicle_history(vehicle_id: str, date_str: str, user=Depends(require_role(["ADMIN", "DISPATCHER", "VIEWER"]))):
    # Q9: Lịch sử vị trí GPS trong ngày
    if not db.session:
        return []
    t_date = date.fromisoformat(date_str)
    t_start = datetime(t_date.year, t_date.month, t_date.day, 0, 0, 0, tzinfo=timezone.utc)
    t_end = datetime(t_date.year, t_date.month, t_date.day, 23, 59, 59, tzinfo=timezone.utc)
    rows = db.session.execute(db.prepared_statements["history"], (vehicle_id, t_date, t_start, t_end))
    return [dict(r._asdict()) for r in rows]

@router.post("/ingest")
def ingest_gps(req: GPSIngest):
    """Tiếp nhận tọa độ GPS từ thiết bị / Simulator và ghi vào 3 bảng ScyllaDB"""
    if not db.session:
        return {"status": "ok", "mock": True}

    ev_time = req.timestamp
    ev_date = ev_time.date()
    ev_uuid = uuid_from_time(ev_time)
    comp_id = req.company_id or settings.COMPANY_ID

    # 1. location_events_by_vehicle_day (Q9)
    db.session.execute(
        """
        INSERT INTO location_events_by_vehicle_day (vehicle_id, event_date, event_time, event_id, lat, lng, speed, heading, trip_id, company_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (req.vehicle_id, ev_date, ev_time, ev_uuid, req.lat, req.lng, req.speed, req.heading, req.trip_id, comp_id)
    )

    # 2. vehicle_activity_by_hour (Q10)
    db.session.execute(
        """
        INSERT INTO vehicle_activity_by_hour (company_id, activity_date, hour, event_time, vehicle_id, event_id, speed)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (comp_id, ev_date, ev_time.hour, ev_time, req.vehicle_id, ev_uuid, req.speed)
    )

    # 3. latest_locations_by_company (Q8 - cập nhật vị trí mới nhất)
    db.session.execute(
        """
        INSERT INTO latest_locations_by_company (company_id, vehicle_id, event_time, lat, lng, speed, heading, trip_id, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'RUNNING')
        """,
        (comp_id, req.vehicle_id, ev_time, req.lat, req.lng, req.speed, req.heading, req.trip_id)
    )

    # 4. Kiểm tra cảnh báo (OVERSPEED & GEOFENCE)
    if req.speed > 80.0:
        db.session.execute(
            """
            INSERT INTO alerts_by_company_day (company_id, alert_date, created_at, alert_id, vehicle_id, trip_id, alert_type, severity, status, details)
            VALUES (%s, %s, %s, %s, %s, %s, 'OVERSPEED', 'HIGH', 'OPEN', %s)
            """,
            (comp_id, ev_date, ev_time, ev_uuid, req.vehicle_id, req.trip_id, f"Vận tốc {req.speed} km/h vượt ngưỡng quy định 80 km/h")
        )

    if not check_geofence(req.vehicle_id, req.lat, req.lng):
        db.session.execute(
            """
            INSERT INTO alerts_by_company_day (company_id, alert_date, created_at, alert_id, vehicle_id, trip_id, alert_type, severity, status, details)
            VALUES (%s, %s, %s, %s, %s, %s, 'GEOFENCE_EXIT', 'CRITICAL', 'OPEN', 'Xe ra khỏi vùng địa lý ảo nội đô TP.HCM')
            """,
            (comp_id, ev_date, ev_time, ev_uuid, req.vehicle_id, req.trip_id)
        )

    return {"status": "success", "event_id": str(ev_uuid)}

@router.get("/alerts")
def get_alerts(date_str: str = None, user=Depends(require_role(["ADMIN", "DISPATCHER", "VIEWER"]))):
    # Q11: Danh sách cảnh báo
    if not db.session:
        return []
    t_date = date.fromisoformat(date_str) if date_str else datetime.now(timezone.utc).date()
    rows = db.session.execute(db.prepared_statements["alerts_by_day"], (settings.COMPANY_ID, t_date))
    return [dict(r._asdict()) for r in rows]

@router.get("/report/monthly-driver")
def get_monthly_driver_report(driver_id: str, month_str: str, user=Depends(require_role(["ADMIN", "DISPATCHER", "VIEWER"]))):
    # Q14: Báo cáo tổng km & chuyến đi theo tài xế/tháng
    if not db.session:
        return {"driver_id": driver_id, "year_month": month_str, "total_trips": 0, "total_distance_km": 0.0}
    rows = db.session.execute(db.prepared_statements["trips_by_driver_month"], (driver_id, month_str))
    trips = [dict(r._asdict()) for r in rows]
    total_km = sum(t["distance_km"] or 0.0 for t in trips)
    return {
        "driver_id": driver_id,
        "year_month": month_str,
        "total_trips": len(trips),
        "total_distance_km": round(total_km, 2),
        "trips": trips
    }
