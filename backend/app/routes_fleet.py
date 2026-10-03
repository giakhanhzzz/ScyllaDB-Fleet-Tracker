from datetime import date, datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from cassandra.query import BatchStatement
from app.database import db
from app.schemas import DriverCreate, DriverUpdate, TripCreate, VehicleCreate, VehicleUpdate
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

def validate_driver(driver_id: str | None, company: str):
    if driver_id is None:
        return
    row = db.execute("SELECT company_id,active FROM drivers_by_id WHERE driver_id = %s", (driver_id,)).one()
    if not row or row.company_id != company or not row.active:
        raise HTTPException(422, "Tài xế không hoạt động trong công ty")

@router.get("/vehicles/{vehicle_id}")
def get_vehicle(vehicle_id: str, user=Depends(read_role)):
    row = db.execute("SELECT * FROM vehicles_by_id WHERE vehicle_id = %s", (vehicle_id,)).one()
    if not row or row.company_id != user["company_id"]:
        raise HTTPException(404, "Không tìm thấy xe trong công ty")
    return row_to_dict(row)

@router.post("/vehicles", status_code=201)
def create_vehicle(req: VehicleCreate, user=Depends(write_role)):
    if db.execute("SELECT vehicle_id FROM vehicles_by_id WHERE vehicle_id = %s", (req.vehicle_id,)).one():
        raise HTTPException(409, "Mã xe đã tồn tại")
    company = user["company_id"]
    validate_driver(req.current_driver_id, company)
    if req.status == "RUNNING" and not req.current_driver_id:
        raise HTTPException(422, "Xe đang chạy cần tài xế")
    now = datetime.now(timezone.utc)
    batch = BatchStatement()
    batch.add("INSERT INTO vehicles_by_id (vehicle_id,company_id,plate,model,current_driver_id,status,speed_limit,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
              (req.vehicle_id,company,req.plate,req.model,req.current_driver_id,req.status,req.speed_limit,now))
    batch.add("INSERT INTO vehicles_by_status (company_id,status,vehicle_id,plate,model,current_driver_id,speed_limit) VALUES (%s,%s,%s,%s,%s,%s,%s)",
              (company,req.status,req.vehicle_id,req.plate,req.model,req.current_driver_id,req.speed_limit))
    # Same HCMC demo bounding box as seed; a configurable geofence remains a later phase.
    batch.add("INSERT INTO geofences_by_vehicle (vehicle_id,min_lat,max_lat,min_lng,max_lng,zone_name,enabled,updated_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
              (req.vehicle_id,10.65,10.90,106.55,106.85,"Vùng Nội Đô TP.HCM",True,now))
    db.execute(batch)
    return {"vehicle_id":req.vehicle_id,"status":req.status}

@router.patch("/vehicles/{vehicle_id}")
def update_vehicle(vehicle_id: str, req: VehicleUpdate, user=Depends(write_role)):
    row = db.execute("SELECT * FROM vehicles_by_id WHERE vehicle_id = %s", (vehicle_id,)).one()
    company = user["company_id"]
    if not row or row.company_id != company:
        raise HTTPException(404, "Không tìm thấy xe trong công ty")
    if not req.model_fields_set or any(getattr(req, field) is None for field in req.model_fields_set - {"current_driver_id"}):
        raise HTTPException(422, "Cần trường hợp lệ để sửa xe")
    plate = req.plate if req.plate is not None else row.plate
    model = req.model if req.model is not None else row.model
    status = req.status if req.status is not None else row.status
    speed_limit = req.speed_limit if req.speed_limit is not None else row.speed_limit
    driver_id = req.current_driver_id if "current_driver_id" in req.model_fields_set else row.current_driver_id
    validate_driver(driver_id, company)
    if status == "RUNNING" and not driver_id:
        raise HTTPException(422, "Xe đang chạy cần tài xế")
    batch = BatchStatement()
    batch.add("UPDATE vehicles_by_id SET plate=%s,model=%s,current_driver_id=%s,status=%s,speed_limit=%s WHERE vehicle_id=%s",
              (plate,model,driver_id,status,speed_limit,vehicle_id))
    if status != row.status:
        batch.add("DELETE FROM vehicles_by_status WHERE company_id=%s AND status=%s AND vehicle_id=%s",
                  (company,row.status,vehicle_id))
    batch.add("INSERT INTO vehicles_by_status (company_id,status,vehicle_id,plate,model,current_driver_id,speed_limit) VALUES (%s,%s,%s,%s,%s,%s,%s)",
              (company,status,vehicle_id,plate,model,driver_id,speed_limit))
    db.execute(batch)
    return {"vehicle_id":vehicle_id,"status":status}

@router.get("/drivers")
def get_drivers(user=Depends(read_role)):
    rows = db.execute("SELECT driver_id,full_name,license_number,phone,active FROM drivers_by_company WHERE company_id = %s", (user["company_id"],))
    return [row_to_dict(row) for row in rows]

@router.get("/drivers/{driver_id}")
def get_driver(driver_id: str, user=Depends(read_role)):
    row = db.execute("SELECT * FROM drivers_by_id WHERE driver_id = %s", (driver_id,)).one()
    if not row or row.company_id != user["company_id"]:
        raise HTTPException(404, "Không tìm thấy tài xế trong công ty")
    return row_to_dict(row)

@router.post("/drivers", status_code=201)
def create_driver(req: DriverCreate, user=Depends(write_role)):
    if db.execute("SELECT driver_id FROM drivers_by_id WHERE driver_id = %s", (req.driver_id,)).one():
        raise HTTPException(409, "Mã tài xế đã tồn tại")
    company = user["company_id"]
    batch = BatchStatement()
    batch.add("INSERT INTO drivers_by_id (driver_id,company_id,full_name,license_number,phone,active,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
              (req.driver_id,company,req.full_name,req.license_number,req.phone,True,datetime.now(timezone.utc)))
    batch.add("INSERT INTO drivers_by_company (company_id,driver_id,full_name,license_number,phone,active) VALUES (%s,%s,%s,%s,%s,%s)",
              (company,req.driver_id,req.full_name,req.license_number,req.phone,True))
    db.execute(batch)
    return {"driver_id":req.driver_id,"active":True}

@router.patch("/drivers/{driver_id}")
def update_driver(driver_id: str, req: DriverUpdate, user=Depends(write_role)):
    row = db.execute("SELECT * FROM drivers_by_id WHERE driver_id = %s", (driver_id,)).one()
    company = user["company_id"]
    if not row or row.company_id != company:
        raise HTTPException(404, "Không tìm thấy tài xế trong công ty")
    if not req.model_fields_set or any(getattr(req, field) is None for field in req.model_fields_set):
        raise HTTPException(422, "Cần trường hợp lệ để sửa tài xế")
    full_name = req.full_name if req.full_name is not None else row.full_name
    license_number = req.license_number if req.license_number is not None else row.license_number
    phone = req.phone if req.phone is not None else row.phone
    active = req.active if req.active is not None else row.active
    if not active:
        # ponytail: bounded demo scan of four company-status partitions; index assignments for large fleets.
        for status in VEHICLE_STATUSES:
            vehicles = db.execute("SELECT vehicle_id,current_driver_id FROM vehicles_by_status WHERE company_id = %s AND status = %s",
                                  (company,status))
            if any(vehicle.current_driver_id == driver_id for vehicle in vehicles):
                raise HTTPException(409, "Tài xế còn được phân công cho xe")
    batch = BatchStatement()
    batch.add("UPDATE drivers_by_id SET full_name=%s,license_number=%s,phone=%s,active=%s WHERE driver_id=%s",
              (full_name,license_number,phone,active,driver_id))
    batch.add("UPDATE drivers_by_company SET full_name=%s,license_number=%s,phone=%s,active=%s WHERE company_id=%s AND driver_id=%s",
              (full_name,license_number,phone,active,company,driver_id))
    db.execute(batch)
    return {"driver_id":driver_id,"active":active}

@router.get("/trips")
def get_trips(trip_date: date | None = None, user=Depends(read_role)):
    selected = trip_date or datetime.now(timezone.utc).date()
    rows = db.execute("SELECT * FROM trips_by_company_day WHERE company_id = %s AND trip_date = %s", (user["company_id"], selected))
    return [row_to_dict(row) for row in rows]

@router.post("/trips", status_code=201)
def create_trip(req: TripCreate, user=Depends(write_role)):
    company = user["company_id"]
    vehicle = db.execute("SELECT company_id,status,current_driver_id FROM vehicles_by_id WHERE vehicle_id = %s", (req.vehicle_id,)).one()
    driver = db.execute("SELECT company_id,active FROM drivers_by_id WHERE driver_id = %s", (req.driver_id,)).one()
    if not vehicle or vehicle.company_id != company or vehicle.status in ("INACTIVE", "MAINTENANCE"):
        raise HTTPException(422, "Xe không khả dụng trong công ty")
    if not driver or driver.company_id != company or not driver.active:
        raise HTTPException(422, "Tài xế không khả dụng trong công ty")
    if vehicle.current_driver_id != req.driver_id:
        raise HTTPException(422, "Tài xế của chuyến chưa được gán cho xe")
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
    batch = BatchStatement()
    for cql, values in statements:
        batch.add(cql, values)
    db.execute(batch)
    return {"status": "success", "trip_id": req.trip_id}
