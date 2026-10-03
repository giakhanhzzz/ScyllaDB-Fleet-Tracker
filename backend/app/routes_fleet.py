from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from app.database import db
from app.schemas import TripCreate
from app.security import require_role
from app.services import row_to_dict

router = APIRouter(prefix="/api/fleet", tags=["Fleet Management"], dependencies=[Depends(db.require_ready)])
read_role = require_role(["ADMIN", "DISPATCHER", "VIEWER"])
write_role = require_role(["ADMIN", "DISPATCHER"])
VEHICLE_STATUSES = ("IDLE", "RUNNING", "MAINTENANCE", "INACTIVE")

@router.get("/vehicles")
def get_vehicles(status: str | None = None, user=Depends(read_role)):
    if status and status not in VEHICLE_STATUSES:
        raise HTTPException(422, "Trạng thái xe không hợp lệ")
    result = []
    for value in ([status] if status else VEHICLE_STATUSES):
        rows = db.execute("SELECT * FROM vehicles_by_status WHERE company_id = %s AND status = %s", (user["company_id"], value))
        result.extend(row_to_dict(row) for row in rows)
    return result

@router.get("/drivers")
def get_drivers(user=Depends(read_role)):
    rows = db.execute("SELECT driver_id,full_name,license_number,phone,active FROM drivers_by_company WHERE company_id = %s", (user["company_id"],))
    return [row_to_dict(row) for row in rows]

@router.get("/trips")
def get_trips(trip_date: date | None = None, user=Depends(read_role)):
    selected = trip_date or datetime.now(timezone.utc).date()
    rows = db.execute("SELECT * FROM trips_by_company_day WHERE company_id = %s AND trip_date = %s", (user["company_id"], selected))
    return [row_to_dict(row) for row in rows]

@router.post("/trips", status_code=201)
def create_trip(req: TripCreate, user=Depends(write_role)):
    company = user["company_id"]
    vehicle = db.execute("SELECT company_id,status FROM vehicles_by_id WHERE vehicle_id = %s", (req.vehicle_id,)).one()
    driver = db.execute("SELECT company_id,active FROM drivers_by_id WHERE driver_id = %s", (req.driver_id,)).one()
    if not vehicle or vehicle.company_id != company or vehicle.status in ("INACTIVE", "MAINTENANCE"):
        raise HTTPException(422, "Xe không khả dụng trong công ty")
    if not driver or driver.company_id != company or not driver.active:
        raise HTTPException(422, "Tài xế không khả dụng trong công ty")
    start = req.start_time or datetime.now(timezone.utc)
    # Preserve the original partition keys until the trip lifecycle is implemented.
    existing = db.execute("SELECT company_id,start_time FROM trips_by_id WHERE trip_id = %s", (req.trip_id,)).one()
    if existing:
        raise HTTPException(409, "Mã chuyến đã tồn tại")
    statements = [
        ("INSERT INTO trips_by_id (trip_id,company_id,vehicle_id,driver_id,origin,destination,start_time,status,distance_km,rejected_points) VALUES (%s,%s,%s,%s,%s,%s,%s,'PLANNED',0.0,0)",
         (req.trip_id,company,req.vehicle_id,req.driver_id,req.origin,req.destination,start)),
        ("INSERT INTO trips_by_company_day (company_id,trip_date,start_time,trip_id,vehicle_id,driver_id,origin,destination,status,distance_km) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'PLANNED',0.0)",
         (company,start.date(),start,req.trip_id,req.vehicle_id,req.driver_id,req.origin,req.destination)),
        ("INSERT INTO trips_by_driver_month (driver_id,year_month,start_time,trip_id,company_id,vehicle_id,status,distance_km) VALUES (%s,%s,%s,%s,%s,%s,'PLANNED',0.0)",
         (req.driver_id,start.strftime("%Y-%m"),start,req.trip_id,company,req.vehicle_id)),
    ]
    # A logged batch makes these small, related denormalized writes durable together.
    from cassandra.query import BatchStatement
    batch = BatchStatement()
    for cql, values in statements:
        batch.add(cql, values)
    db.execute(batch)
    return {"status": "success", "trip_id": req.trip_id}
