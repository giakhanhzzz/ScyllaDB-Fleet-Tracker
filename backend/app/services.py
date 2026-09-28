import math
from datetime import datetime, timezone
from typing import List, Tuple
from app.database import db
from app.config import settings

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Tính khoảng cách đường cong giữa 2 tọa độ theo công thức Haversine (km)"""
    R = 6371.0 # Bán kính trái đất (km)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
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

    total_distance = 0.0
    rejected_points = 0
    last_valid_point = points[0]

    for i in range(1, len(points)):
        curr_point = points[i]
        dist = haversine_km(last_valid_point[0], last_valid_point[1], curr_point[0], curr_point[1])
        time_diff_hours = (curr_point[2] - last_valid_point[2]).total_seconds() / 3600.0

        if time_diff_hours > 0:
            speed = dist / time_diff_hours
            if speed > max_speed_kmh:
                # Bước nhảy phi thực tế -> loại bỏ
                rejected_points += 1
                continue

        total_distance += dist
        last_valid_point = curr_point

    return round(total_distance, 2), rejected_points

def check_geofence(vehicle_id: str, lat: float, lng: float) -> bool:
    """Kiểm tra xe có nằm trong Bounding Box Geofence cho phép không"""
    if not db.session:
        return True
    try:
        row = db.session.execute("SELECT min_lat, max_lat, min_lng, max_lng, enabled FROM geofences_by_vehicle WHERE vehicle_id = %s", (vehicle_id,)).one()
        if row and row.enabled:
            if not (row.min_lat <= lat <= row.max_lat and row.min_lng <= lng <= row.max_lng):
                return False # Đã vượt ra ngoài vùng địa lý
    except Exception:
        pass
    return True
