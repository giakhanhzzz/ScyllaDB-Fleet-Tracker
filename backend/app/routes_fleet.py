from fastapi import APIRouter, HTTPException, Depends
from app.schemas import VehicleCreate, TripCreate
from app.security import require_role
from app.database import db
from app.config import settings
from datetime import datetime, timezone, date

router = APIRouter(prefix="/api/fleet", tags=["Fleet Management"])

@router.get("/vehicles")
def get_vehicles(status: str = None, user=Depends(require_role(["ADMIN", "DISPATCHER", "VIEWER"]))):
    # Q4: Xe theo trạng thái
    if not db.session:
        return []
    if status:
        rows = db.session.execute(
            "SELECT vehicle_id, plate, model, current_driver_id, speed_limit FROM vehicles_by_status WHERE company_id = %s AND status = %s",
            (settings.COMPANY_ID, status)
        )
    else:
        rows = db.session.execute("SELECT * FROM vehicles_by_id")
    return [dict(r._asdict()) for r in rows]

@router.get("/drivers")
def get_drivers(user=Depends(require_role(["ADMIN", "DISPATCHER", "VIEWER"]))):
    # Q5: Danh sách tài xế
    if not db.session:
        return []
    rows = db.session.execute("SELECT driver_id, full_name, license_number, phone, active FROM drivers_by_company WHERE company_id = %s", (settings.COMPANY_ID,))
    return [dict(r._asdict()) for r in rows]

@router.get("/trips")
def get_trips(trip_date: str = None, user=Depends(require_role(["ADMIN", "DISPATCHER", "VIEWER"]))):
    # Q6: Danh sách chuyến theo ngày
    if not db.session:
        return []
    t_date = date.fromisoformat(trip_date) if trip_date else datetime.now(timezone.utc).date()
    rows = db.session.execute(
        "SELECT start_time, trip_id, vehicle_id, driver_id, origin, destination, status, distance_km FROM trips_by_company_day "
        "WHERE company_id = %s AND trip_date = %s",
        (settings.COMPANY_ID, t_date)
    )
    return [dict(r._asdict()) for r in rows]

@router.post("/trips")
def create_trip(req: TripCreate, user=Depends(require_role(["ADMIN", "DISPATCHER"]))):
    # Tạo chuyến đi mới (Admin / Dispatcher) - Denormalization 3 bảng
    if not db.session:
        return {"status": "ok", "message": "Demo mode: Chuyến đã tạo"}
    now = datetime.now(timezone.utc)
    t_date = now.date()
    st_time = req.start_time or now

    # 1. trips_by_id
    db.session.execute(
        """
        INSERT INTO trips_by_id (trip_id, company_id, vehicle_id, driver_id, origin, destination, start_time, status, distance_km, rejected_points)
        VALUES (%s, %s, %s, %s, %s, %s, %s, 'PLANNED', 0.0, 0)
        """,
        (req.trip_id, settings.COMPANY_ID, req.vehicle_id, req.driver_id, req.origin, req.destination, st_time)
    )
    # 2. trips_by_company_day
    db.session.execute(
        """
        INSERT INTO trips_by_company_day (company_id, trip_date, start_time, trip_id, vehicle_id, driver_id, origin, destination, status, distance_km)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'PLANNED', 0.0)
        """,
        (settings.COMPANY_ID, t_date, st_time, req.trip_id, req.vehicle_id, req.driver_id, req.origin, req.destination)
    )
    # 3. trips_by_driver_month
    month_str = t_date.strftime("%Y-%m")
    db.session.execute(
        """
        INSERT INTO trips_by_driver_month (driver_id, year_month, start_time, trip_id, company_id, vehicle_id, status, distance_km)
        VALUES (%s, %s, %s, %s, %s, %s, 'PLANNED', 0.0)
        """,
        (req.driver_id, month_str, st_time, req.trip_id, settings.COMPANY_ID, req.vehicle_id)
    )
    return {"status": "success", "trip_id": req.trip_id}
