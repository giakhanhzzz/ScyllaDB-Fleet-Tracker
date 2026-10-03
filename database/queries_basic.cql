-- ==============================================================================
-- ScyllaDB Fleet Tracker - Basic Queries (Q1 - Q8)
-- Không quét toàn bảng, không ALLOW FILTERING, tuân thủ đúng Partition Key
-- ==============================================================================

USE fleet_tracker;

-- ------------------------------------------------------------------------------
-- Q1: Login theo username
-- Phục vụ: Authentication, kiểm tra password_hash và trạng thái active
-- ------------------------------------------------------------------------------
SELECT username, password_hash, full_name, role, company_id, active 
FROM users_by_username 
WHERE username = 'khanh_admin';

-- ------------------------------------------------------------------------------
-- Q2: Liệt kê tất cả người dùng thuộc một công ty
-- Phục vụ: Màn hình quản trị người dùng của Admin
-- ------------------------------------------------------------------------------
SELECT username, full_name, role, active, created_at 
FROM users_by_company 
WHERE company_id = 'COMP_HCM_01';

-- ------------------------------------------------------------------------------
-- Q3: Tra cứu chi tiết một xe theo vehicle_id
-- Phục vụ: Xem thông tin xe, biển số, tốc độ tối đa, tài xế hiện thời
-- ------------------------------------------------------------------------------
SELECT vehicle_id, company_id, plate, model, current_driver_id, status, speed_limit 
FROM vehicles_by_id 
WHERE vehicle_id = 'VEH_001';

-- ------------------------------------------------------------------------------
-- Q3 (b): Tra cứu chi tiết tài xế theo driver_id
-- ------------------------------------------------------------------------------
SELECT driver_id, company_id, full_name, license_number, phone, active 
FROM drivers_by_id 
WHERE driver_id = 'DRV_001';

-- ------------------------------------------------------------------------------
-- Q3 (c): Tra cứu chi tiết chuyến đi theo trip_id
-- ------------------------------------------------------------------------------
SELECT trip_id, company_id, vehicle_id, driver_id, origin, destination, 
       start_time, end_time, status, distance_km, rejected_points, notes 
FROM trips_by_id 
WHERE trip_id = 'TRIP_202609_001';

-- ------------------------------------------------------------------------------
-- Q4: Liệt kê các xe theo trạng thái hoạt động trong công ty
-- Phục vụ: Lọc danh sách xe 'RUNNING', 'IDLE', 'MAINTENANCE'
-- ------------------------------------------------------------------------------
SELECT vehicle_id, plate, model, current_driver_id, speed_limit 
FROM vehicles_by_status 
WHERE company_id = 'COMP_HCM_01' AND status = 'RUNNING';

-- ------------------------------------------------------------------------------
-- Q5: Liệt kê danh sách tài xế của một công ty
-- Phục vụ: Phân công lái xe, chọn tài xế khi lập chuyến
-- ------------------------------------------------------------------------------
SELECT driver_id, full_name, license_number, phone, active 
FROM drivers_by_company 
WHERE company_id = 'COMP_HCM_01';

-- ------------------------------------------------------------------------------
-- Q6: Danh sách chuyến đi trong một ngày của công ty (sắp xếp mới nhất trước)
-- Phục vụ: Điều phối viên theo dõi tiến độ chuyến đi theo ca/ngày
-- ------------------------------------------------------------------------------
SELECT start_time, trip_id, vehicle_id, driver_id, origin, destination, status, distance_km 
FROM trips_by_company_day 
WHERE company_id = 'COMP_HCM_01' AND trip_date = '2026-09-28';

-- ------------------------------------------------------------------------------
-- Q7: Danh sách chuyến đi của một tài xế trong tháng
-- Phục vụ: Lịch sử chuyến đi của tài xế
-- ------------------------------------------------------------------------------
SELECT start_time, trip_id, vehicle_id, status, distance_km 
FROM trips_by_driver_month 
WHERE driver_id = 'DRV_001' AND year_month = '2026-09';

-- ------------------------------------------------------------------------------
-- Q8: Vị trí mới nhất của toàn bộ xe thuộc công ty (Hiển thị thời gian thực trên bản đồ)
-- Phục vụ: Màn hình giám sát trực tiếp trên Leaflet Map
-- ------------------------------------------------------------------------------
SELECT vehicle_id, event_time, lat, lng, speed, heading, trip_id, status 
FROM latest_locations_by_company 
WHERE company_id = 'COMP_HCM_01';
