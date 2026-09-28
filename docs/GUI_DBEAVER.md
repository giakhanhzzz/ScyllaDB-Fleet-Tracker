# Hướng Dẫn Kết Nối GUI (DBeaver Lite / TablePlus) Đến ScyllaDB (Phase 1)

Tài liệu này hướng dẫn chi tiết cách cấu hình công cụ quản trị giao diện (GUI) để kết nối đến ScyllaDB node đang chạy trên máy cục bộ (`localhost:9042`).

---

## 1. Công Cụ Chính: DBeaver (DBeaver Lite / Community)

ScyllaDB tương thích hoàn toàn với giao thức mạng (CQL Native Protocol) của Apache Cassandra. Do đó, trong DBeaver, chúng ta sử dụng driver **Apache Cassandra**.

### Các Bước Cấu Hình:

1. **Khởi động DBeaver**:
   - Mở DBeaver trên máy tính Windows.
   - Chọn menu **Database** -> **New Database Connection** (hoặc nhấn biểu tượng phích cắm điện có dấu cộng).

2. **Chọn Driver**:
   - Trong ô tìm kiếm, nhập: `Cassandra` hoặc `Apache Cassandra`.
   - Chọn **Apache Cassandra** và nhấn **Next**.
   - *Lưu ý*: Nếu đây là lần đầu tiên sử dụng, DBeaver sẽ yêu cầu tải thư viện driver (Driver files). Nhấn nút **Download** để DBeaver tự động tải `cassandra-driver-core`.

3. **Thiết Lập Thông Số Kết Nối (Connection Settings)**:
   - **Host**: `localhost` (hoặc `127.0.0.1`)
   - **Port**: `9042`
   - **Database / Keyspace**: Để trống (hoặc nhập `system`)
   - **Username**: Để trống (mặc định ScyllaDB chạy chế độ `AllowAllAuthenticator`)
   - **Password**: Để trống

4. **Kiểm Tra Kết Nối (Test Connection)**:
   - Nhấn nút **Test Connection...** ở góc dưới bên trái cửa sổ.
   - Khi kết nối thành công, DBeaver sẽ hiển thị hộp thoại:
     `Connected! Server: ScyllaDB / Cassandra, Driver: Cassandra Java Driver`.
   - Nhấn **Finish** để lưu kết nối.

5. **Xác Minh Hoạt Động Bằng Truy Vấn CQL**:
   - Mở cửa sổ **SQL Editor** (F3 hoặc Ctrl+Enter) và thực thi các câu lệnh sau:
   ```sql
   -- Kiểm tra thông tin phiên bản và node ScyllaDB
   SELECT cluster_name, release_version, broadcast_address, data_center, rack 
   FROM system.local;

   -- Xem danh sách các Keyspace hệ thống
   SELECT keyspace_name, durable_writes 
   FROM system_schema.keyspaces;
   ```

---

## 2. Công Cụ Dự Phòng & Trong Giáo Trình: TablePlus & NoSQL Manager for Cassandra

### A. TablePlus (Được giới thiệu trong Giáo trình TH NoSQL 2025 - Trang 42-45)
1. Mở TablePlus -> Click **Create a new connection...** -> Chọn **Cassandra**.
2. Thiết lập thông số:
   - **Name**: `ScyllaDB Localhost`
   - **Host**: `127.0.0.1`
   - **Port**: `9042`
   - **User / Password**: Để trống
3. Nhấn **Test** để xác nhận kết nối xanh (OK) -> Nhấn **Connect**.

### B. NoSQL Manager for Cassandra (Được hướng dẫn trong Slide thực hành của Khoa)
1. Khởi động GUI Tool **NoSQL Manager for Cassandra Professional** -> Chọn **Use 30-days Trial**.
2. Tạo kết nối đến server:
   - **Host**: `localhost` (hoặc `127.0.0.1`)
   - **Port**: `9042`
   - Nhấn **Test Connection** -> Khi hiển thị `Connected!`, nhấn **OK**.
3. Thao tác trên giao diện:
   - Chuột phải vào Connection -> **Create new Keyspace** (hoặc mở **CQL Editor** để thực thi câu lệnh CQL trực tiếp).

---

## 3. So Sánh Các Công Cụ GUI Theo Rubric Đồ Án & Giáo Trình HUIT

| Tiêu Chí | DBeaver Lite / Community | NoSQL Manager for Cassandra | TablePlus |
| :--- | :--- | :--- | :--- |
| **Nguồn gốc trong học phần** | Đề xuất trong đồ án nhóm | **Hướng dẫn chi tiết trong Slide BM HTTT** | **Hướng dẫn trong Giáo trình TH 2025** |
| **Hỗ trợ CQL & Scylla/Cassandra** | Đầy đủ visual keyspaces, column family, schema | Chuyên biệt 100% cho Cassandra/ScyllaDB | Hỗ trợ cơ bản, duyệt bảng trực quan |
| **Tự động tải driver** | Tải driver JAR qua Maven | Tích hợp sẵn engine driver | Tích hợp sẵn engine driver |
| **Quản lý Schema & Index** | Rất chi tiết (Partition Key, Clustering Key) | Trực quan chuyên sâu cho Column Family | Xem cấu trúc bảng dạng lưới đơn giản |
| **Tiêu tốn tài nguyên (RAM)** | Java (~300-600MB RAM) | Native Win32 (~80-150MB RAM, rất nhẹ) | Native (~100-200MB RAM) |
| **Đánh giá đồ án** | **Lựa chọn chính thức (Primary)** | **Lựa chọn thực hành theo Slide trường** | **Lựa chọn so sánh / dự phòng** |

---

## 4. Xử Lý Sự Cố Thường Gặp (Troubleshooting)

1. **Lỗi "Connection refused: connect"**:
   - Nguyên nhân: Docker container `scylla-node` chưa chạy hoặc port 9042 chưa được map ra host.
   - Khắc phục:
     ```powershell
     docker compose ps
     # Nếu container Exit hoặc chưa chạy:
     docker compose up -d
     ```

2. **Lỗi "Timed out waiting for server to respond"**:
   - Nguyên nhân: ScyllaDB cần khoảng 30 - 45 giây sau khi container khởi động để bật socket CQL 9042.
   - Khắc phục: Đợi lệnh `docker exec -it scylla-node nodetool status` hiển thị trạng thái `UN` (Up/Normal) trước khi nhấn Test Connection.

3. **Xung đột cổng 9042**:
   - Kiểm tra bằng PowerShell:
     ```powershell
     Get-NetTCPConnection -LocalPort 9042 -ErrorAction SilentlyContinue
     ```
   - Đảm bảo không có service Cassandra/Scylla nào khác đang chiếm port.
