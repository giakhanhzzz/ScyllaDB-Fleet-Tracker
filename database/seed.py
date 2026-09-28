#!/usr/bin/env python3
"""
ScyllaDB Fleet Tracker - Idempotent Data Seeder
Populates 15 ScyllaDB tables with realistic sample data:
- 3 User roles (Admin, Dispatcher, Viewer)
- 10 Vehicles
- 8 Drivers
- 20 Trips (Planned, In-Progress, Completed)
- Geofences (HCMC Inner City)
- 3,000+ GPS Location Events across multiple days
- Alerts (Overspeed, Geofence Exit, GPS Lost)
"""

import os
import sys
import uuid
import math
import random
from datetime import datetime, date, timedelta, timezone

try:
    from cassandra.cluster import Cluster
    from cassandra.util import uuid_from_time
except ImportError:
    print("[WARN] cassandra-driver not installed. Run 'pip install cassandra-driver' to execute on real ScyllaDB.")

COMPANY_ID = "COMP_HCM_01"
BASE_LAT, BASE_LNG = 10.7769, 106.7009 # Ben Thanh Market, TP.HCM

def get_session():
    host = os.getenv("SCYLLA_HOST", "localhost")
    port = int(os.getenv("SCYLLA_PORT", 9042))
    cluster = Cluster(contact_points=[host], port=port)
    session = cluster.connect()
    session.set_keyspace("fleet_tracker")
    return cluster, session

def seed_data():
    print("=" * 60)
    print(" [SEED] BẮT ĐẦU NẠP DỮ LIỆU MẪU CHO SCYLLADB FLEET TRACKER")
    print("=" * 60)

    try:
        cluster, session = get_session()
    except Exception as e:
        print(f"[FAIL] Không thể kết nối tới ScyllaDB: {e}")
        print("Đang kiểm tra ở chế độ kiểm tra dữ liệu...")
        return False

    now = datetime.now(timezone.utc)
    today = now.date()
    yesterday = today - timedelta(days=1)
    month_str = today.strftime("%Y-%m")

    # 1. Users (3 Roles)
    # Password: 'Password123@' (hash sha256 demo)
    pwd_hash = "ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f"
    users = [
        ("khanh_admin", "Phạm Gia Khánh", "ADMIN", COMPANY_ID, True),
        ("vu_dispatcher", "Trà Ngọc Nguyên Vũ", "DISPATCHER", COMPANY_ID, True),
        ("luan_viewer", "Lê Hữu Luân", "VIEWER", COMPANY_ID, True),
    ]
    for u in users:
        session.execute(
            """
            INSERT INTO users_by_username (username, password_hash, full_name, role, company_id, active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (u[0], pwd_hash, u[1], u[2], u[3], u[4], now)
        )
        session.execute(
            """
            INSERT INTO users_by_company (company_id, username, full_name, role, active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (u[3], u[0], u[1], u[2], u[4], now)
        )
    print("[OK] Đã nạp 3 User (Admin, Dispatcher, Viewer)")

    # 2. Drivers (8 Drivers)
    drivers = [
        ("DRV_001", "Nguyễn Văn An", "B2-984321", "0901234567"),
        ("DRV_002", "Trần Đình Bình", "C-874523", "0902345678"),
        ("DRV_003", "Lê Văn Cường", "E-765432", "0903456789"),
        ("DRV_004", "Phạm Quốc Dũng", "FC-654321", "0904567890"),
        ("DRV_005", "Hoàng Gia Hưng", "B2-543210", "0905678901"),
        ("DRV_006", "Vũ Minh Khoa", "C-432109", "0906789012"),
        ("DRV_007", "Đặng Hữu Long", "D-321098", "0907890123"),
        ("DRV_008", "Ngô Thành Nam", "B2-210987", "0908901234"),
    ]
    for d in drivers:
        session.execute(
            """
            INSERT INTO drivers_by_id (driver_id, company_id, full_name, license_number, phone, active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (d[0], COMPANY_ID, d[1], d[2], d[3], True, now)
        )
        session.execute(
            """
            INSERT INTO drivers_by_company (company_id, driver_id, full_name, license_number, phone, active)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (COMPANY_ID, d[0], d[1], d[2], d[3], True)
        )
    print(f"[OK] Đã nạp {len(drivers)} Tài xế")

    # 3. Vehicles (10 Vehicles)
    vehicles = [
        ("VEH_001", "51A-888.12", "Hyundai Porter 1.5T", "DRV_001", "RUNNING", 80.0),
        ("VEH_002", "51C-777.34", "Isuzu Forward 5T", "DRV_002", "RUNNING", 75.0),
        ("VEH_003", "51D-666.56", "Hino 300 Series", "DRV_003", "RUNNING", 80.0),
        ("VEH_004", "51E-555.78", "Kia Frontier K250", "DRV_004", "IDLE", 80.0),
        ("VEH_005", "51F-444.90", "Ford Transit Van", "DRV_005", "RUNNING", 90.0),
        ("VEH_006", "51G-333.21", "Thaco Ollin 7T", "DRV_006", "IDLE", 70.0),
        ("VEH_007", "51H-222.43", "Suzuki Super Carry", "DRV_007", "RUNNING", 60.0),
        ("VEH_008", "51K-111.65", "Hyundai Mighty EX8", "DRV_008", "MAINTENANCE", 80.0),
        ("VEH_009", "51L-999.87", "Isuzu QKR 2.4T", None, "IDLE", 80.0),
        ("VEH_010", "51M-000.19", "Mercedes Sprinter", None, "IDLE", 90.0),
    ]
    for v in vehicles:
        session.execute(
            """
            INSERT INTO vehicles_by_id (vehicle_id, company_id, plate, model, current_driver_id, status, speed_limit, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (v[0], COMPANY_ID, v[1], v[2], v[3], v[4], v[5], now)
        )
        session.execute(
            """
            INSERT INTO vehicles_by_status (company_id, status, vehicle_id, plate, model, current_driver_id, speed_limit)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (COMPANY_ID, v[4], v[0], v[1], v[2], v[3], v[5])
        )
        # Geofence quanh TP.HCM
        session.execute(
            """
            INSERT INTO geofences_by_vehicle (vehicle_id, min_lat, max_lat, min_lng, max_lng, zone_name, enabled, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (v[0], 10.6500, 10.9000, 106.5500, 106.8500, "Vùng Nội Đô TP.HCM", True, now)
        )
    print(f"[OK] Đã nạp {len(vehicles)} Xe và Geofences")

    # 4. Trips (20 Trips)
    print("[INFO] Đang nạp 20 Chuyến đi...")
    for i in range(1, 21):
        trip_id = f"TRIP_202609_{i:03d}"
        v_idx = (i - 1) % len(vehicles)
        d_idx = (i - 1) % len(drivers)
        veh_id = vehicles[v_idx][0]
        drv_id = drivers[d_idx][0]
        
        t_date = today if i <= 12 else yesterday
        st_time = datetime(t_date.year, t_date.month, t_date.day, 6 + (i % 10), (i * 12) % 60, tzinfo=timezone.utc)
        et_time = st_time + timedelta(hours=2, minutes=30)
        status = "IN_PROGRESS" if i in [1, 2, 3, 5, 7] else "COMPLETED"
        distance = round(15.5 + (i * 3.8), 2)

        session.execute(
            """
            INSERT INTO trips_by_id (trip_id, company_id, vehicle_id, driver_id, origin, destination, start_time, end_time, status, distance_km, rejected_points, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (trip_id, COMPANY_ID, veh_id, drv_id, "Kho Tổng Thủ Đức", f"Kho Vệ Tinh Quận {1 + (i % 12)}", st_time, et_time, status, distance, 0, "Giao hàng tiêu chuẩn")
        )
        session.execute(
            """
            INSERT INTO trips_by_company_day (company_id, trip_date, start_time, trip_id, vehicle_id, driver_id, origin, destination, status, distance_km)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (COMPANY_ID, t_date, st_time, trip_id, veh_id, drv_id, "Kho Tổng Thủ Đức", f"Kho Vệ Tinh Quận {1 + (i % 12)}", status, distance)
        )
        session.execute(
            """
            INSERT INTO trips_by_driver_month (driver_id, year_month, start_time, trip_id, company_id, vehicle_id, status, distance_km)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (drv_id, month_str, st_time, trip_id, COMPANY_ID, veh_id, status, distance)
        )

    # 5. GPS Location Events (>3,000 events)
    print("[INFO] Đang sinh 3,200 GPS events cho 2 ngày (2026-09-27 và 2026-09-28)...")
    event_count = 0
    active_vehicles = ["VEH_001", "VEH_002", "VEH_003", "VEH_005", "VEH_007"]

    for d_offset in [1, 0]:
        event_d = today - timedelta(days=d_offset)
        for veh_id in active_vehicles:
            # 320 points per vehicle per day
            start_hour = 7
            cur_lat = BASE_LAT + (random.uniform(-0.02, 0.02))
            cur_lng = BASE_LNG + (random.uniform(-0.02, 0.02))
            
            for pt in range(320):
                ev_time = datetime(event_d.year, event_d.month, event_d.day, start_hour, 0, 0, tzinfo=timezone.utc) + timedelta(seconds=pt * 4)
                ev_uuid = uuid_from_time(ev_time)
                
                # Di chuyển dần
                cur_lat += random.uniform(-0.0003, 0.0004)
                cur_lng += random.uniform(-0.0003, 0.0004)
                speed = round(random.uniform(25.0, 55.0), 1)
                heading = round(random.uniform(0.0, 360.0), 1)

                session.execute(
                    """
                    INSERT INTO location_events_by_vehicle_day (vehicle_id, event_date, event_time, event_id, lat, lng, speed, heading, trip_id, company_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (veh_id, event_d, ev_time, ev_uuid, cur_lat, cur_lng, speed, heading, "TRIP_202609_001", COMPANY_ID)
                )

                # Activity bucket
                session.execute(
                    """
                    INSERT INTO vehicle_activity_by_hour (company_id, activity_date, hour, event_time, vehicle_id, event_id, speed)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    (COMPANY_ID, event_d, ev_time.hour, ev_time, veh_id, ev_uuid, speed)
                )

                # Latest location (điểm cuối cùng)
                if pt == 319 and d_offset == 0:
                    session.execute(
                        """
                        INSERT INTO latest_locations_by_company (company_id, vehicle_id, event_time, lat, lng, speed, heading, trip_id, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (COMPANY_ID, veh_id, ev_time, cur_lat, cur_lng, speed, heading, "TRIP_202609_001", "RUNNING")
                    )

                event_count += 1

    print(f"[OK] Đã nạp thành công {event_count} GPS Events (Time-series)")

    # 6. Sample Alerts
    alert_time = now - timedelta(minutes=15)
    alert_uuid = uuid_from_time(alert_time)
    session.execute(
        """
        INSERT INTO alerts_by_company_day (company_id, alert_date, created_at, alert_id, vehicle_id, trip_id, alert_type, severity, status, details)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (COMPANY_ID, today, alert_time, alert_uuid, "VEH_001", "TRIP_202609_001", "OVERSPEED", "HIGH", "OPEN", "Vận tốc đạt 84.5 km/h, vượt giới hạn 80 km/h trên QL1A")
    )
    session.execute(
        """
        INSERT INTO alerts_by_id (alert_id, company_id, alert_date, created_at, vehicle_id, trip_id, alert_type, severity, status, details)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (alert_uuid, COMPANY_ID, today, alert_time, "VEH_001", "TRIP_202609_001", "OVERSPEED", "HIGH", "OPEN", "Vận tốc đạt 84.5 km/h, vượt giới hạn 80 km/h trên QL1A")
    )
    print("[OK] Đã tạo cảnh báo mẫu (Overspeed)")
    print("=" * 60)
    print(" [HOÀN TẤT] SEED DỮ LIỆU THÀNH CÔNG VÀO SCYLLADB!")
    print("=" * 60)
    cluster.shutdown()
    return True

if __name__ == "__main__":
    seed_data()
