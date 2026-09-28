# Kịch Bản Trình Chiếu Demo (DEMO_SCRIPT.md)

Tài liệu này hướng dẫn chi tiết kịch bản thuyết trình và chạy thử đồ án **ScyllaDB Fleet Tracker** theo đúng thang điểm 10 của giảng viên.

---

## 1. Phân Chia Thời Gian & Vai Trò Trình Bày

| Thành Viên | Thời Lượng | Nội Dung Trình Bày |
| :--- | :--- | :--- |
| **Phạm Gia Khánh** | 5 phút | - Giới thiệu đề tài, kiến trúc ScyllaDB & Column Family.<br>- Mô hình 15 bảng theo 14 Access Patterns.<br>- Demo GUI DBeaver/NoSQL Manager kết nối cổng 9042, chạy CQL cơ bản/nâng cao.<br>- Demo Backup & Restore / Export CSV. |
| **Trà Ngọc Nguyên Vũ** | 5 phút | - Kiến trúc Backend FastAPI + cassandra-driver.<br>- Cơ chế phân quyền RBAC (Admin, Dispatcher, Viewer).<br>- Quy tắc xử lý đa bảng nhất quán (Denormalization) khi tạo chuyến.<br>- Thuật toán tính quãng đường Haversine & lọc bước nhảy GPS. |
| **Lê Hữu Luân** | 5 phút | - Giao diện người dùng Web + Leaflet Map thời gian thực.<br>- Trình diễn GPS Simulator phát tín hiệu xe di chuyển.<br>- Tái hiện 3 loại cảnh báo: Quá tốc độ, Ra khỏi vùng Geofence, Mất tín hiệu.<br>- Báo cáo tổng hợp số chuyến & km của tài xế theo tháng (Q14). |

---

## 2. Kịch Bản 8 Bước Trình Chiếu

### Bước 1: Khởi động hệ thống (Khánh)
- Mở PowerShell: `.\scripts\init_demo.ps1`.
- Chỉ ra trạng thái ScyllaDB chạy trên Docker container, mở DBeaver kết nối `localhost:9042`.
- Chạy thử query Q8 (`SELECT * FROM latest_locations_by_company`).

### Bước 2: Đăng nhập & Kiểm tra RBAC (Vũ)
- Đăng nhập bằng `khanh_admin`: Có toàn quyền quản trị, thêm xe, xem dữ liệu backup.
- Đăng xuất, đăng nhập `vu_dispatcher`: Có quyền tạo chuyến, quản lý xe/tài xế, không có quyền quản trị user.
- Đăng xuất, đăng nhập `luan_viewer`: Chế độ chỉ đọc, tất cả nút thêm/sửa/xóa và xử lý alert đều bị khóa.

### Bước 3: Quản lý Đội xe & Tạo chuyến đi mới (Vũ)
- Chọn mục **Quản lý Đội xe** -> Xem danh sách 10 xe và 8 tài xế.
- Nhấn **Tạo Chuyến Đi Mới**:
  - Mã chuyến: `TRIP_202609_999`
  - Chọn xe: `VEH_001` (Hyundai Porter 1.5T)
  - Chọn tài xế: `DRV_001` (Nguyễn Văn An)
  - Điểm đi: Kho Tổng Thủ Đức -> Điểm đến: Quận 1, TP.HCM
  - Trạng thái: `PLANNED` -> Chuyển sang `IN_PROGRESS`.
- Nhấn mạnh: Dữ liệu được ghi đồng thời vào 3 bảng (`trips_by_id`, `trips_by_company_day`, `trips_by_driver_month`).

### Bước 4: Bật GPS Simulator & Giám sát Bản đồ (Luân)
- Mở màn hình **Bản đồ Trực quan (Leaflet)**.
- Bật công tắc **GPS Simulator** (phát tín hiệu mỗi 3 giây).
- Các xe bắt đầu di chuyển trên bản đồ TP.HCM:
  - Marker xe cập nhật tọa độ liên tục.
  - Tốc độ và hướng di chuyển hiển thị trong Popup.

### Bước 5: Kích hoạt & Xử lý Cảnh Báo (Luân & Vũ)
- Trên Simulator, chọn chế độ **Kích hoạt Vượt tốc độ (Overspeed)** cho xe `VEH_003`.
- Bảng Cảnh báo hiển thị ngay alert đỏ: *Vận tốc 88.5 km/h vượt ngưỡng quy định 80 km/h*.
- Chọn chế độ **Vượt Geofence**: Xe `VEH_007` đi ra khỏi tọa độ TP.HCM -> Tạo alert *GEOFENCE_EXIT*.
- Dispatcher Vũ thao tác nhấn **Xác nhận (Acknowledge)** và **Đã xử lý (Resolve)** -> Cập nhật trạng thái alert trong ScyllaDB.

### Bước 6: Xem Lịch Sử Hành Trình (Luân)
- Chọn xe `VEH_001` và ngày hiện tại.
- Bản đồ tự động vẽ đường Polyline nối các điểm GPS theo thứ tự thời gian (`location_events_by_vehicle_day`).
- Hiển thị tổng số điểm hợp lệ và các điểm bị loại do bước nhảy GPS ảo.

### Bước 7: Báo Cáo Tài Xế Theo Tháng - Q14 (Vũ)
- Chọn tài xế `DRV_001` và tháng `2026-09`.
- Hệ thống đọc partition tháng của tài xế và tính tổng km: ví dụ `186.4 km` và `8 chuyến đi`.

### Bước 8: Sao lưu & Đối chiếu Dữ liệu (Khánh)
- Chạy `.\scripts\backup.ps1` để xuất bảng ra file CSV.
- Mở file CSV trong thư mục `docs/backups/` đối chiếu số dòng khớp với dữ liệu trên GUI DBeaver.
- Kết luận: Hệ thống đạt chuẩn 10/10 mục theo yêu cầu đồ án.
