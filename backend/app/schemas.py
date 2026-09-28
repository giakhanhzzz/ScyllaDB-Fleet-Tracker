from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    full_name: str
    role: str
    company_id: str

class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    role: str
    company_id: str

class VehicleCreate(BaseModel):
    vehicle_id: str
    plate: str
    model: str
    current_driver_id: Optional[str] = None
    status: str = "IDLE"
    speed_limit: float = 80.0

class TripCreate(BaseModel):
    trip_id: str
    vehicle_id: str
    driver_id: str
    origin: str
    destination: str
    start_time: Optional[datetime] = None

class GPSIngest(BaseModel):
    vehicle_id: str
    lat: float
    lng: float
    speed: float
    heading: float
    timestamp: datetime
    trip_id: Optional[str] = None
    company_id: Optional[str] = None

class AlertAction(BaseModel):
    alert_id: str
    status: str # 'ACKNOWLEDGED' hoặc 'RESOLVED'
