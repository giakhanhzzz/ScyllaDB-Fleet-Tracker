from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime, date, timezone
from typing import Literal
from uuid import UUID

class RequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

class LoginRequest(RequestModel):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=256)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    full_name: str
    role: str
    company_id: str

class UserCreate(RequestModel):
    username: str
    password: str
    full_name: str
    role: Literal["ADMIN", "DISPATCHER", "VIEWER"]
    company_id: str

class VehicleCreate(RequestModel):
    vehicle_id: str
    plate: str
    model: str
    current_driver_id: Optional[str] = None
    status: str = "IDLE"
    speed_limit: float = Field(default=80, gt=0, le=200)

class TripCreate(RequestModel):
    trip_id: str
    vehicle_id: str
    driver_id: str
    origin: str
    destination: str
    start_time: Optional[datetime] = None

    @field_validator("start_time")
    @classmethod
    def utc_start(cls, value):
        if value is not None:
            if value.tzinfo is None:
                raise ValueError("start_time cần có timezone")
            return value.astimezone(timezone.utc)
        return value

class GPSIngest(RequestModel):
    vehicle_id: str = Field(min_length=1, max_length=80)
    event_id: UUID
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    speed: float = Field(ge=0, le=200)
    heading: float = Field(ge=0, lt=360)
    timestamp: datetime

    @field_validator("event_id")
    @classmethod
    def timeuuid(cls, value):
        if value.version != 1:
            raise ValueError("event_id cần là UUID v1")
        return value

    @field_validator("timestamp")
    @classmethod
    def utc_timestamp(cls, value):
        if value.tzinfo is None:
            raise ValueError("timestamp cần có timezone")
        return value.astimezone(timezone.utc)

class AlertAction(RequestModel):
    alert_id: UUID
    status: Literal["ACKNOWLEDGED", "RESOLVED"]
