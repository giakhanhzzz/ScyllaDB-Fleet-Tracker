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
    username: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=256)
    full_name: str = Field(min_length=1, max_length=120)
    role: Literal["ADMIN", "DISPATCHER", "VIEWER"]

class UserUpdate(RequestModel):
    password: str | None = Field(default=None, min_length=8, max_length=256)
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    role: Literal["ADMIN", "DISPATCHER", "VIEWER"] | None = None
    active: bool | None = None

class VehicleCreate(RequestModel):
    vehicle_id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")
    plate: str = Field(min_length=1, max_length=30)
    model: str = Field(min_length=1, max_length=120)
    current_driver_id: str | None = Field(default=None, min_length=1, max_length=80)
    status: Literal["IDLE", "RUNNING", "MAINTENANCE", "INACTIVE"] = "IDLE"
    speed_limit: float = Field(default=80, gt=0, le=200)

class VehicleUpdate(RequestModel):
    plate: str | None = Field(default=None, min_length=1, max_length=30)
    model: str | None = Field(default=None, min_length=1, max_length=120)
    current_driver_id: str | None = Field(default=None, min_length=1, max_length=80)
    status: Literal["IDLE", "RUNNING", "MAINTENANCE", "INACTIVE"] | None = None
    speed_limit: float | None = Field(default=None, gt=0, le=200)

class DriverCreate(RequestModel):
    driver_id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")
    full_name: str = Field(min_length=1, max_length=120)
    license_number: str = Field(min_length=1, max_length=80)
    phone: str = Field(min_length=1, max_length=32)

class DriverUpdate(RequestModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    license_number: str | None = Field(default=None, min_length=1, max_length=80)
    phone: str | None = Field(default=None, min_length=1, max_length=32)
    active: bool | None = None

class TripCreate(RequestModel):
    trip_id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_.-]+$")
    vehicle_id: str = Field(min_length=1, max_length=80)
    driver_id: str = Field(min_length=1, max_length=80)
    origin: str = Field(min_length=1, max_length=200)
    destination: str = Field(min_length=1, max_length=200)
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
