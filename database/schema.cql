-- ==============================================================================
-- ScyllaDB Fleet Tracker - Database Schema (15 Tables)
-- Keyspace: fleet_tracker
-- Replication: SimpleStrategy, replication_factor = 1 (Local Demo Single Node)
-- ==============================================================================

CREATE KEYSPACE IF NOT EXISTS fleet_tracker
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
} AND durable_writes = true;

USE fleet_tracker;

-- ------------------------------------------------------------------------------
-- 1. users_by_username (Q1: Login theo username)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users_by_username (
    username text,
    password_hash text,
    full_name text,
    role text, -- 'ADMIN', 'DISPATCHER', 'VIEWER'
    company_id text,
    active boolean,
    created_at timestamp,
    PRIMARY KEY (username)
);

-- ------------------------------------------------------------------------------
-- 2. users_by_company (Q2: Danh sách & Quản trị user theo công ty)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users_by_company (
    company_id text,
    username text,
    full_name text,
    role text,
    active boolean,
    created_at timestamp,
    PRIMARY KEY ((company_id), username)
);

-- ------------------------------------------------------------------------------
-- 3. vehicles_by_id (Q3: Chi tiết xe theo ID)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vehicles_by_id (
    vehicle_id text,
    company_id text,
    plate text,
    model text,
    current_driver_id text,
    status text, -- 'IDLE', 'RUNNING', 'MAINTENANCE', 'INACTIVE'
    speed_limit double,
    created_at timestamp,
    PRIMARY KEY (vehicle_id)
);

-- ------------------------------------------------------------------------------
-- 4. vehicles_by_status (Q4: Danh sách xe lọc theo trạng thái)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vehicles_by_status (
    company_id text,
    status text,
    vehicle_id text,
    plate text,
    model text,
    current_driver_id text,
    speed_limit double,
    PRIMARY KEY ((company_id, status), vehicle_id)
);

-- ------------------------------------------------------------------------------
-- 5. drivers_by_id (Q3: Chi tiết tài xế theo ID)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS drivers_by_id (
    driver_id text,
    company_id text,
    full_name text,
    license_number text,
    phone text,
    active boolean,
    created_at timestamp,
    PRIMARY KEY (driver_id)
);

-- ------------------------------------------------------------------------------
-- 6. drivers_by_company (Q5: Danh sách tài xế theo công ty)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS drivers_by_company (
    company_id text,
    driver_id text,
    full_name text,
    license_number text,
    phone text,
    active boolean,
    PRIMARY KEY ((company_id), driver_id)
);

-- ------------------------------------------------------------------------------
-- 7. trips_by_id (Q3: Chi tiết chuyến đi theo ID)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trips_by_id (
    trip_id text,
    company_id text,
    vehicle_id text,
    driver_id text,
    origin text,
    destination text,
    start_time timestamp,
    end_time timestamp,
    status text, -- 'PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED'
    distance_km double,
    rejected_points int,
    notes text,
    PRIMARY KEY (trip_id)
);

-- ------------------------------------------------------------------------------
-- 8. trips_by_company_day (Q6: Chuyến đi theo công ty trong ngày)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trips_by_company_day (
    company_id text,
    trip_date date,
    start_time timestamp,
    trip_id text,
    vehicle_id text,
    driver_id text,
    origin text,
    destination text,
    status text,
    distance_km double,
    PRIMARY KEY ((company_id, trip_date), start_time, trip_id)
) WITH CLUSTERING ORDER BY (start_time DESC, trip_id ASC);

-- ------------------------------------------------------------------------------
-- 9. trips_by_driver_month (Q7 & Q14: Chuyến đi của tài xế theo tháng & Báo cáo)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trips_by_driver_month (
    driver_id text,
    year_month text, -- Format: 'YYYY-MM', ví dụ '2026-09'
    start_time timestamp,
    trip_id text,
    company_id text,
    vehicle_id text,
    status text,
    distance_km double,
    PRIMARY KEY ((driver_id, year_month), start_time, trip_id)
) WITH CLUSTERING ORDER BY (start_time DESC, trip_id ASC);

-- ------------------------------------------------------------------------------
-- 10. geofences_by_vehicle (Q13: Thiết lập vùng địa lý ảo cho xe)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS geofences_by_vehicle (
    vehicle_id text,
    min_lat double,
    max_lat double,
    min_lng double,
    max_lng double,
    zone_name text,
    enabled boolean,
    updated_at timestamp,
    PRIMARY KEY (vehicle_id)
);

-- ------------------------------------------------------------------------------
-- 11. location_events_by_vehicle_day (Q9: Time-series lịch sử GPS [t1, t2])
-- TTL 90 ngày (7,776,000 giây)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS location_events_by_vehicle_day (
    vehicle_id text,
    event_date date,
    event_time timestamp,
    event_id timeuuid,
    lat double,
    lng double,
    speed double,
    heading double,
    trip_id text,
    company_id text,
    PRIMARY KEY ((vehicle_id, event_date), event_time, event_id)
) WITH CLUSTERING ORDER BY (event_time DESC, event_id ASC)
  AND default_time_to_live = 7776000;

-- ------------------------------------------------------------------------------
-- 12. latest_locations_by_company (Q8: Vị trí mới nhất của tất cả/từng xe)
-- Không đặt TTL ngắn (giữ vị trí mới nhất cho mỗi xe)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS latest_locations_by_company (
    company_id text,
    vehicle_id text,
    event_time timestamp,
    lat double,
    lng double,
    speed double,
    heading double,
    trip_id text,
    status text,
    PRIMARY KEY ((company_id), vehicle_id)
);

-- ------------------------------------------------------------------------------
-- 13. vehicle_activity_by_hour (Q10: Xe có hoạt động gần đây theo bucket giờ)
-- TTL 48 giờ (172,800 giây)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS vehicle_activity_by_hour (
    company_id text,
    activity_date date,
    hour int,
    event_time timestamp,
    vehicle_id text,
    event_id timeuuid,
    speed double,
    PRIMARY KEY ((company_id, activity_date, hour), event_time, vehicle_id, event_id)
) WITH CLUSTERING ORDER BY (event_time DESC, vehicle_id ASC, event_id ASC)
  AND default_time_to_live = 172800;

-- ------------------------------------------------------------------------------
-- 14. alerts_by_company_day (Q11: Danh sách cảnh báo trong ngày)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alerts_by_company_day (
    company_id text,
    alert_date date,
    created_at timestamp,
    alert_id timeuuid,
    vehicle_id text,
    trip_id text,
    alert_type text, -- 'OVERSPEED', 'GEOFENCE_EXIT', 'GPS_LOST'
    severity text,   -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    status text,     -- 'OPEN', 'ACKNOWLEDGED', 'RESOLVED'
    details text,
    PRIMARY KEY ((company_id, alert_date), created_at, alert_id)
) WITH CLUSTERING ORDER BY (created_at DESC, alert_id ASC);

-- ------------------------------------------------------------------------------
-- 15. alerts_by_id (Q12: Tra cứu & cập nhật chi tiết alert)
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alerts_by_id (
    alert_id timeuuid,
    company_id text,
    alert_date date,
    created_at timestamp,
    vehicle_id text,
    trip_id text,
    alert_type text,
    severity text,
    status text,
    details text,
    resolved_by text,
    resolved_at timestamp,
    PRIMARY KEY (alert_id)
);
