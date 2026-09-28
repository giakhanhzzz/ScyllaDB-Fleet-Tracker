# ScyllaDB Fleet Tracker

> **Đồ án**: Hệ thống quản lý dữ liệu theo dõi vị trí phương tiện vận tải và lịch sử hành trình của đội xe  
> **Repository**: [https://github.com/giakhanhzzz/ScyllaDB-Fleet-Tracker](https://github.com/giakhanhzzz/ScyllaDB-Fleet-Tracker)  
> **Giai đoạn hiện tại**: **Phase 1 (P1) - Môi trường & Hạ tầng ScyllaDB**

---

## 1. Phân Công Thành Viên Nhóm

- **Phạm Gia Khánh**: Phụ trách dữ liệu (Data Modeling, Keyspace/Tables), môi trường hạ tầng (Docker/ScyllaDB), tích hợp hệ thống.
- **Trà Ngọc Nguyên Vũ**: Phụ trách Backend (FastAPI), xác thực & phân quyền (RBAC), quy tắc nghiệp vụ (Trip, Alert).
- **Lê Hữu Luân**: Phụ trách Frontend (HTML/CSS/JS + Leaflet), GPS Simulator, kịch bản demo.

---

## 2. Mục Tiêu & Phạm Vi Phase 1 (P1)

Phase 1 tập trung thiết lập và chuẩn hóa toàn bộ hạ tầng cơ sở dữ liệu ScyllaDB cục bộ:
1. **Docker Compose**: Cấu hình ScyllaDB Single Node (phiên bản `5.4`), ánh xạ cổng `9042` (CQL) và `10000` (Management API), cấu hình Volume `scylla_fleet_data` lưu trữ dữ liệu bền vững, và Healthcheck tự động.
2. **Tối ưu tài nguyên cho máy 8GB RAM**: Áp dụng các cờ ScyllaDB `--smp 1 --memory 1500M --overprovisioned 1` để đảm bảo hệ thống không bị tràn RAM hoặc quá tải CPU trên môi trường Windows Docker Desktop.
3. **Script xác minh**: Cung cấp `scripts/wait_for_scylla.py` sử dụng `cassandra-driver` chính thức để kiểm tra tính sẵn sàng của port TCP 9042, CQL Native Protocol và truy vấn bảng metadata `system.local`.
4. **Tài liệu hướng dẫn GUI**: Hướng dẫn kết nối công cụ quản trị trực quan **DBeaver Lite** và **TablePlus** qua giao thức Cassandra tại `docs/GUI_DBEAVER.md`.
5. **Nhật ký kiểm thử**: Ghi nhận bằng chứng thực nghiệm tại `docs/TEST_EVIDENCE.md`.

---

## 3. Cấu Trúc Thư Mục Hiện Tại (Phase 1)

```
scylladb-fleet-tracker/
├── .env.example              # Cấu hình biến môi trường mẫu cho ScyllaDB và ứng dụng
├── docker-compose.yml        # Docker Compose cấu hình ScyllaDB node, volume, healthcheck
├── README.md                 # Tài liệu tổng quan và hướng dẫn chạy P1
├── docs/
│   ├── GUI_DBEAVER.md        # Hướng dẫn kết nối DBeaver Lite & TablePlus tới ScyllaDB
│   └── TEST_EVIDENCE.md      # Nhật ký kiểm thử, kết quả chạy và trạng thái môi trường
└── scripts/
    └── wait_for_scylla.py    # Script Python kiểm tra kết nối ScyllaDB qua cassandra-driver
```

---

## 4. Hướng Dẫn Thực Thi Phase 1 Bằng PowerShell (Trên Máy Windows)

### Bước 1: Khởi động Docker Desktop
Đảm bảo phần mềm **Docker Desktop** đã được mở và biểu tượng trạng thái hiển thị **Docker Engine: Running**.

### Bước 2: Khởi động ScyllaDB Node
Mở PowerShell tại thư mục dự án và chạy:
```powershell
# Khởi chạy ScyllaDB dưới dạng background daemon
docker compose up -d

# Xem log khởi động của ScyllaDB container
docker compose logs -f scylla
```
*(Nhấn Ctrl+C để thoát khỏi màn hình logs sau khi thấy ScyllaDB đã hoàn tất khởi tạo).*

### Bước 3: Kiểm tra trạng thái Cluster bằng `nodetool`
```powershell
docker exec -it scylla-node nodetool status
```
*Kết quả mong đợi*: Dòng trạng thái hiển thị `UN` (**U**p / **N**ormal), Owns `100.0%`, Address `172.x.x.x`.

### Bước 4: Kiểm tra kết nối CQL nội bộ bằng `cqlsh`
```powershell
docker exec -it scylla-node cqlsh -e "SHOW VERSION;"
```
*Kết quả mong đợi*: Hiển thị phiên bản `[cqlsh ... | Cassandra 3.0.8 | CQL spec 3.4.0 | Scylla release 5.4...]`.

### Bước 5: Kiểm tra kết nối từ Python Host (`cassandra-driver`)
Chạy bằng môi trường Python đã có cài `cassandra-driver` (ví dụ Laragon Python 3.13):
```powershell
# Chạy script xác minh kết nối tự động
python scripts/wait_for_scylla.py
```
*Kết quả mong đợi*: Script in thông tin `Cluster Name`, `Release Version`, `Datacenter` và báo `[SUCCESS] Phase 1 da san sang 100%!`.

### Bước 6: Kiểm tra kết nối GUI (DBeaver)
- Thực hiện theo các bước chi tiết trong file `docs/GUI_DBEAVER.md`.
- Kết nối tới `localhost:9042` bằng driver **Apache Cassandra**.

---

## 5. Trạng Thái Kiểm Chứng Hiện Tại & Lưu Ý An Toàn

- **Trạng thái thực nghiệm**: Cấu hình P1 đã được soạn thảo đầy đủ và đúng cú pháp. Tuy nhiên, do Docker Desktop Engine trên máy host Windows của nhóm đang ở trạng thái dừng (Stopped) tại lần kiểm tra trước và môi trường sandbox hiện tại không có Docker Engine, toàn bộ các bài kiểm thử thực tế được đánh dấu là **CHƯA KIỂM CHỨNG** theo đúng quy định.
- **Không tự ý chuyển Phase**: Nhóm chỉ chuyển sang Phase 2 (P2: Basic/Advanced Queries & Data Model) sau khi Khánh xác nhận chạy thành công các lệnh trên và đánh dấu `PASS` trong `docs/TEST_EVIDENCE.md`.

---

## 6. Đề Xuất Phê Duyệt Cho Khánh (.gitignore)

Để bảo vệ repository công khai GitHub khỏi việc vô tình commit các file nhạy cảm hoặc file rác runtime, đề xuất bổ sung file `.gitignore` với các quy tắc sau:
```gitignore
# Python artifacts
__pycache__/
*.py[cod]
.venv/
venv/
env/

# Environment secrets
.env
!.env.example

# Scylla / Docker runtime data
scylla_data/
*.log

# IDE & Editor configs
.vscode/
.idea/
*.sublime-project
```
*(Chờ bạn Phạm Gia Khánh phê duyệt trước khi ghi chính thức vào kế hoạch dự án).*
