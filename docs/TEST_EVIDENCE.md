# Bằng Chứng Kiểm Thử & Trạng Thái Môi Trường (TEST_EVIDENCE.md)

Tài liệu này ghi nhận nhật ký kiểm thử thực tế và trạng thái môi trường cho từng giai đoạn của đồ án **scylladb-fleet-tracker**.

> **Quy tắc quan trọng**: Không tự động đánh dấu `PASS` khi chưa chạy kiểm chứng thực tế trên môi trường có ScyllaDB hoạt động. Các hạng mục chưa chạy thực nghiệm trên host được ghi rõ là `CHƯA KIỂM CHỨNG` hoặc `BLOCKED`.

---

## 1. Nhật Ký Trạng Thái Môi Trường (Cập Nhật Gần Nhất)

- **Hệ điều hành Host**: Windows (RAM khả dụng ~8 GB).
- **Docker Desktop**: Đã cài đặt trên Windows. *Trạng thái tại lần kiểm tra trước: Docker Engine đang dừng (Stopped)*.
- **Port 9042**: Trống tại lần kiểm tra trước (sẵn sàng map cho ScyllaDB Native Transport).
- **Môi trường Python**:
  - Python 3.13 (Laragon): Đã cài đặt `cassandra-driver` 3.30.1 (đã xác nhận `import cassandra` thành công).
  - Python 3.12 (Hệ thống): Có sẵn, chưa cài `cassandra-driver`.
- **Công cụ GUI (DBeaver / TablePlus)**: Chưa cài đặt tại lần kiểm tra trước.

---

## 2. Ma Trận Kiểm Thử Giai Đoạn 1 (Phase 1: Environment & Infrastructure)

| Mã Kiểm Thử | Mục Tiêu & Lệnh Thực Thi | Kết Quả Mong Đợi | Trạng Thái Thực Tế | Ghi Chú / Blocker |
| :--- | :--- | :--- | :--- | :--- |
| **TC-P1-01** | Khởi động Scylla container:<br>`docker compose up -d` | Container `scylla-node` khởi động thành công, port 9042 và 10000 được forward. | **CHƯA KIỂM CHỨNG** | **BLOCKER**: Cần mở Docker Desktop và bật Docker Engine trên Windows trước khi chạy. |
| **TC-P1-02** | Kiểm tra trạng thái node qua nodetool:<br>`docker exec -it scylla-node nodetool status` | Node hiển thị trạng thái `UN` (Up / Normal), Owns 100%, Datacenter `datacenter1`. | **CHƯA KIỂM CHỨNG** | Chờ TC-P1-01 hoàn thành. |
| **TC-P1-03** | Kiểm tra kết nối CQLSH nội bộ container:<br>`docker exec -it scylla-node cqlsh -e "SHOW VERSION;"` | Hiển thị phiên bản CQLSH, CQL spec 3.4.x, Release ScyllaDB 5.4.x. | **CHƯA KIỂM CHỨNG** | Chờ TC-P1-01 hoàn thành. |
| **TC-P1-04** | Kiểm tra kết nối Python driver:<br>`python scripts/wait_for_scylla.py` | Import driver thành công, kết nối port 9042, truy vấn thành công bảng `system.local`. | **CHƯA KIỂM CHỨNG** | Driver đã có trong Python 3.13 Laragon, chờ Scylla container chạy. |
| **TC-P1-05** | Kiểm tra kết nối DBeaver GUI:<br>Test Connection tới `localhost:9042` | DBeaver báo `Connected!` và duyệt được các system keyspaces. | **CHƯA KIỂM CHỨNG** | **BLOCKER**: DBeaver chưa được cài đặt trên máy người dùng. |

---

## 3. Nhật Ký Chi Tiết Thực Thi Lệnh (Execution Log)

### Lệnh 1: Kiểm tra cấu hình Compose (Cú pháp YAML)
- **Lệnh**: Kiểm tra định dạng `docker-compose.yml`.
- **Kết quả**: Cấu hình hợp lệ với Scylla 5.4, giới hạn tài nguyên `--smp 1 --memory 1500M --overprovisioned 1`, port 9042/10000, volume `scylla_data`, network `fleet-network`.

### Lệnh 2: Script xác minh kết nối `scripts/wait_for_scylla.py`
- **Lệnh**: Kiểm tra logic script.
- **Kết quả**: Đã tích hợp kiểm tra TCP socket readiness, retry loop 30 lần, kết nối Cluster và truy vấn `system.local` và `system_schema.keyspaces`.

---

## 4. Hành Động Tiếp Theo Để Hoàn Thành P1 (Cần Thực Hiện Trên Máy Windows Của Nhóm)

1. Bật Docker Desktop trên Windows và đợi Engine chuyển sang màu xanh (Running).
2. Mở PowerShell tại thư mục dự án và chạy:
   ```powershell
   docker compose up -d
   ```
3. Chạy script kiểm tra tự động:
   ```powershell
   python scripts/wait_for_scylla.py
   ```
4. Chụp ảnh màn hình kết quả lệnh `nodetool status` và lưu vào thư mục `docs/screenshots/` để làm bằng chứng cho báo cáo đồ án.
