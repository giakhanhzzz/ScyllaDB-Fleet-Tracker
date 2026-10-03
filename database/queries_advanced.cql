-- ==============================================================================
-- ScyllaDB Fleet Tracker - Advanced Queries (Q9 - Q14)
-- Time-Series Range Query, Activity Bucketing, Alert Resolution & Monthly Aggregation
-- ==============================================================================

USE fleet_tracker;

-- ------------------------------------------------------------------------------
-- Q9: Truy vấn lịch sử vị trí GPS của một xe trong khoảng thời gian [t1, t2] trong ngày
-- Phục vụ: Vẽ hành trình polyline trên bản đồ Leaflet, phát hiện bất thường
-- ------------------------------------------------------------------------------
SELECT event_time, event_id, lat, lng, speed, heading, trip_id 
FROM location_events_by_vehicle_day 
WHERE vehicle_id = 'VEH_001' 
  AND event_date = '2026-09-28' 
  AND event_time >= '2026-09-28 00:00:00+0000' 
  AND event_time <= '2026-09-28 23:59:59+0000';

-- ------------------------------------------------------------------------------
-- Q10: Danh sách xe có tín hiệu di chuyển trong một khung giờ cụ thể (Activity Bucket)
-- Phục vụ: Giám sát đội xe hoạt động N phút gần đây mà không cần quét toàn bộ bảng
-- ------------------------------------------------------------------------------
SELECT event_time, vehicle_id, event_id, speed 
FROM vehicle_activity_by_hour 
WHERE company_id = 'COMP_HCM_01' 
  AND activity_date = '2026-09-28' 
  AND hour = 3;

-- ------------------------------------------------------------------------------
-- Q11: Danh sách cảnh báo của công ty trong ngày (sắp xếp giảm dần theo thời gian)
-- Phục vụ: Trung tâm kiểm soát cảnh báo theo thời gian thực (Overspeed, Geofence, Lost Signal)
-- ------------------------------------------------------------------------------
SELECT created_at, alert_id, vehicle_id, trip_id, alert_type, severity, status, details 
FROM alerts_by_company_day 
WHERE company_id = 'COMP_HCM_01' 
  AND alert_date = '2026-09-28';

-- ------------------------------------------------------------------------------
-- Q12: Tra cứu chi tiết cảnh báo theo alert_id và cập nhật trạng thái xử lý
-- Phục vụ: Dispatcher/Admin xác nhận (ACKNOWLEDGED) hoặc xử lý xong (RESOLVED)
-- ------------------------------------------------------------------------------
SELECT alert_id, company_id, alert_date, created_at, vehicle_id, trip_id, alert_type, severity, status, details 
FROM alerts_by_id 
WHERE alert_id = 09100600-bb32-11f1-8000-000000000001;

-- Cập nhật trạng thái xử lý cảnh báo trong bảng alerts_by_id:
UPDATE alerts_by_id 
SET status = 'RESOLVED', resolved_by = 'vu_dispatcher', resolved_at = toTimestamp(now())
WHERE alert_id = 09100600-bb32-11f1-8000-000000000001;

-- Keep the day projection consistent with the lookup table.
UPDATE alerts_by_company_day SET status = 'RESOLVED'
WHERE company_id = 'COMP_HCM_01' AND alert_date = '2026-09-28'
  AND created_at = '2026-09-28 11:45:00+0000'
  AND alert_id = 09100600-bb32-11f1-8000-000000000001;

-- ------------------------------------------------------------------------------
-- Q13: Lấy thông tin Geofence (vùng địa lý ảo) của một xe
-- Phục vụ: Kiểm tra xe có vượt ra ngoài ranh giới cho phép (Bounding Box)
-- ------------------------------------------------------------------------------
SELECT vehicle_id, min_lat, max_lat, min_lng, max_lng, zone_name, enabled 
FROM geofences_by_vehicle 
WHERE vehicle_id = 'VEH_001';

-- ------------------------------------------------------------------------------
-- Q14: Báo cáo tổng hợp số chuyến đi và tổng km của tài xế theo tháng
-- Logic: Đọc danh sách các chuyến trong partition tháng của tài xế từ trips_by_driver_month,
-- sau đó Backend Python tính toán tổng hợp (COUNT trips, SUM distance_km).
-- ------------------------------------------------------------------------------
SELECT trip_id, start_time, status, distance_km 
FROM trips_by_driver_month 
WHERE driver_id = 'DRV_001' 
  AND year_month = '2026-09';
