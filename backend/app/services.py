import math
from threading import Lock
from datetime import datetime, timezone
from typing import List, Tuple
from cassandra.util import Date as CQLDate
from app.database import db

# ponytail: one FastAPI worker serializes trip transitions and GPS writes; use
# a database-backed active-trip claim before running multiple API workers.
trip_write_lock = Lock()

def as_utc(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)

def row_to_dict(row):
    """Cassandra timestamps are naive UTC; expose explicit UTC to browsers."""
    values = dict(row._asdict())
    for key, value in values.items():
        if isinstance(value, datetime):
            values[key] = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
        elif isinstance(value, CQLDate):
            values[key] = str(value)
    return values

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Tính khoảng cách đường cong giữa 2 tọa độ theo công thức Haversine (km)"""
    R = 6371.0 # Bán kính trái đất (km)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    a = min(1.0, max(0.0, a))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_trip_distance(points: List[Tuple[float, float, datetime]], max_speed_kmh: float = 140.0) -> Tuple[float, int]:
    """
    Tính tổng quãng đường của chuỗi điểm GPS theo thời gian:
    - Loại bỏ các bước nhảy GPS phi thực tế (tốc độ > 140 km/h)
    - Trả về (tổng km, số điểm bị loại)
    """
    if len(points) < 2:
        return 0.0, 0

    points = sorted(points, key=lambda point: point[2])

    total_distance = 0.0
    rejected_points = 0
    last_valid_point = points[0]

    for i in range(1, len(points)):
        curr_point = points[i]
        dist = haversine_km(last_valid_point[0], last_valid_point[1], curr_point[0], curr_point[1])
        time_diff_hours = (curr_point[2] - last_valid_point[2]).total_seconds() / 3600.0

        if time_diff_hours <= 0:
            rejected_points += 1
            continue
        speed = dist / time_diff_hours
        if speed > max_speed_kmh:
            rejected_points += 1
            continue

        total_distance += dist
        last_valid_point = curr_point

    return round(total_distance, 2), rejected_points

def check_geofence(vehicle_id: str, lat: float, lng: float) -> bool:
    """Kiểm tra xe có nằm trong Bounding Box Geofence cho phép không"""
    row = db.execute("SELECT min_lat,max_lat,min_lng,max_lng,enabled FROM geofences_by_vehicle WHERE vehicle_id = %s", (vehicle_id,)).one()
    return not row or not row.enabled or (row.min_lat <= lat <= row.max_lat and row.min_lng <= lng <= row.max_lng)
