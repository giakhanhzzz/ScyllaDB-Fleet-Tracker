# Kế hoạch triển khai đồ án ScyllaDB

## 0. Mục tiêu và giới hạn

Xây dựng demo local cho hệ thống theo dõi vị trí và lịch sử hành trình đội xe. Sản phẩm phải chứng minh đặc trưng Column Family/time-series của ScyllaDB và đủ luồng: schema → seed/import → CQL trên GUI → backend → bản đồ → backup/restore.

Phạm vi tối thiểu nhưng hoàn chỉnh:

- Một ScyllaDB node mặc định để demo ổn định; không coi đây là cấu hình production.
- Một container FastAPI phục vụ API và frontend tĩnh; không cần React/build pipeline.
- Một GPS simulator độc lập chạy bằng Docker Compose.
- DBeaver Lite/trial là GUI chính; TablePlus là GUI so sánh và dự phòng.
- Không triển khai Kafka, Redis, microservice, Kubernetes, cloud, routing thực hoặc bản đồ offline đầy đủ.

## 1. Kiến trúc tổng thể

Luồng chính:

`GPS simulator → POST /api/locations → FastAPI validate + ghi ScyllaDB → cập nhật latest/activity → tạo alert → frontend đọc API và hiển thị Leaflet`

| Thành phần | Trách nhiệm |
|---|---|
| ScyllaDB | Dữ liệu nghiệp vụ/time-series; truy vấn theo partition key/CQL |
| FastAPI | Authentication/RBAC, CRUD, GPS ingestion, history, alert, report |
| Frontend tĩnh | Login, dashboard, CRUD, map, history, alert, admin data actions |
| GPS simulator | Sinh vị trí bình thường/lỗi có chủ đích cho nhiều xe |
| DBeaver | Duyệt schema/data, chạy CQL cơ bản/nâng cao, import/export |
| Scripts | Schema, seed, export/import, backup/restore, reset demo |

## 2. Access patterns cần khóa trước schema

| ID | Truy vấn | Mẫu khóa |
|---|---|---|
| Q1 | Login theo username | Một partition theo username |
| Q2 | Admin liệt kê user theo công ty | `(company_id), username` |
| Q3 | Chi tiết xe/tài xế/trip theo ID | Lookup table theo ID |
| Q4 | Xe theo trạng thái | `(company_id,status), vehicle_id` |
| Q5 | Tài xế của công ty | `(company_id), driver_id` |
| Q6 | Trip trong ngày | `(company_id,trip_date), start_time DESC, trip_id` |
| Q7 | Trip tài xế trong tháng | `(driver_id,year_month), start_time DESC, trip_id` |
| Q8 | Latest location một/tất cả xe | `(company_id), vehicle_id` |
| Q9 | GPS history `[t1,t2]` | `(vehicle_id,event_date), event_time, event_id` |
| Q10 | Xe hoạt động N phút gần nhất | `(company_id,date,hour), event_time, vehicle_id,event_id` |
| Q11 | Alert theo ngày | `(company_id,alert_date), created_at DESC, alert_id` |
| Q12 | Alert theo ID | Lookup alert_id |
| Q13 | Geofence của xe | Lookup vehicle_id |
| Q14 | Tổng km/số trip theo tài xế/tháng | Partition tháng của tài xế; cộng trong backend |

Không query quét toàn bảng, không `ALLOW FILTERING`, không giả định join/group-by tự do như SQL.

## 3. Data model dự kiến

### 3.1. Bảng nghiệp vụ

| Table | Khóa chính logic | Mục đích |
|---|---|---|
| `users_by_username` | `username` | password_hash, role, company_id, active; login |
| `users_by_company` | `(company_id), username` | danh sách/quản trị user |
| `vehicles_by_id` | `vehicle_id` | plate, model, driver_id, status, speed_limit |
| `vehicles_by_status` | `(company_id,status), vehicle_id` | liệt kê xe theo trạng thái |
| `drivers_by_id` | `driver_id` | name, license, phone, active |
| `drivers_by_company` | `(company_id), driver_id` | danh sách tài xế |
| `trips_by_id` | `trip_id` | xe, tài xế, điểm đi/đến, thời gian, status, distance |
| `trips_by_company_day` | `(company_id,trip_date), start_time, trip_id` | chuyến trong ngày |
| `trips_by_driver_month` | `(driver_id,year_month), start_time, trip_id` | lịch sử/thống kê tháng |
| `geofences_by_vehicle` | `vehicle_id` | bounding box và enabled |

### 3.2. Time-series và alert

| Table | Khóa chính logic | Chính sách |
|---|---|---|
| `location_events_by_vehicle_day` | `(vehicle_id,event_date), event_time,event_id` | DESC; TTL đề xuất 90 ngày; cân nhắc TWCS |
| `latest_locations_by_company` | `(company_id), vehicle_id` | một row/xe; không TTL ngắn |
| `vehicle_activity_by_hour` | `(company_id,date,hour), event_time,vehicle_id,event_id` | TTL 48 giờ; query N phút và dedupe backend |
| `alerts_by_company_day` | `(company_id,alert_date), created_at,alert_id` | alert list theo ngày |
| `alerts_by_id` | `alert_id` | lookup/acknowledge/resolve |

Quy tắc denormalization:

- Sửa xe cập nhật `vehicles_by_id` và `vehicles_by_status`; đổi status phải xóa row partition cũ rồi thêm mới.
- Start/end trip cập nhật đủ ba bảng trip.
- GPS ingestion ghi event, activity bucket, rồi cập nhật latest nếu timestamp mới hơn.
- Alert tạo/xử lý cập nhật bảng theo ngày và lookup.

## 4. Luật nghiệp vụ

### Trip

- Dispatcher tạo `PLANNED`, chọn xe/tài xế đang active.
- Start chuyển `IN_PROGRESS`; một xe chỉ có tối đa một trip đang chạy.
- GPS event trong khoảng start/end gắn trip hiện hành.
- End trip tính distance Haversine theo chuỗi điểm đã sắp thời gian và lưu vào các bảng trip.
- Loại bước nhảy GPS phi thực tế bằng ngưỡng khoảng cách/tốc độ; lưu số điểm bị loại để giải thích report.

### Alert

- `OVERSPEED`: speed vượt speed_limit; có cooldown để không tạo mỗi vài giây.
- `GEOFENCE_EXIT`: điểm chuyển từ trong ra ngoài bounding box hoặc hết cooldown.
- `GPS_LOST`: scheduler thấy last_seen quá N phút và chưa có alert mở.
- Alert status: `OPEN`, `ACKNOWLEDGED`, `RESOLVED`.

### RBAC

| Chức năng | Admin | Dispatcher | Viewer |
|---|:---:|:---:|:---:|
| Quản trị user/role | Có | Không | Không |
| CRUD xe/tài xế/trip | Có | Có | Chỉ đọc |
| Xem map/history/report | Có | Có | Có |
| Xử lý alert | Có | Có | Không |
| Import/export/backup/restore | Có | Không | Không |

Backend cưỡng chế quyền; ẩn nút frontend chỉ là UX.

## 5. Cấu trúc file/module

```text
C:\Users\artis\Downloads\Project_NoSql\
├─ Hệ thống\
│  ├─ PROJECT_QUYDINH.md
│  ├─ RULES_PROJECT.md
│  ├─ TAKENOTE_Baihoc_NOSQL.md
│  └─ Nhap.md
├─ KE_HOACH_DO_AN_SCYLLADB.md
├─ README.md
├─ docker-compose.yml
├─ .env.example
├─ database\
│  ├─ schema.cql
│  ├─ queries_basic.cql
│  ├─ queries_advanced.cql
│  ├─ seed.py
│  └─ import_export.py
├─ backend\
│  ├─ Dockerfile
│  ├─ requirements.txt
│  ├─ app\
│  │  ├─ main.py
│  │  ├─ config.py
│  │  ├─ database.py
│  │  ├─ security.py
│  │  ├─ schemas.py
│  │  ├─ routes_auth_users.py
│  │  ├─ routes_fleet.py
│  │  ├─ routes_tracking.py
│  │  └─ services.py
│  └─ tests\
│     ├─ test_permissions.py
│     └─ test_tracking_rules.py
├─ frontend\
│  ├─ index.html
│  ├─ app.js
│  ├─ styles.css
│  └─ vendor\leaflet\
├─ simulator\gps_simulator.py
├─ scripts\
│  ├─ wait_for_scylla.py
│  ├─ init_demo.ps1
│  ├─ backup.ps1
│  ├─ restore.ps1
│  └─ reset_demo.ps1
└─ docs\
   ├─ GUI_DBEAVER.md
   ├─ DEMO_SCRIPT.md
   ├─ TEST_EVIDENCE.md
   └─ screenshots\
```

FastAPI phục vụ frontend như static files. Lưu Leaflet assets cục bộ; tile online có fallback hiển thị tọa độ/polyline nền trống.

## 6. API/use case

| Nhóm | Use case |
|---|---|
| Auth | login, current user, client logout |
| Users | list/create/update role/activate-deactivate |
| Vehicles | list by status, detail, create/update/deactivate |
| Drivers | list/detail/create/update/deactivate |
| Trips | list by day, create/start/end/cancel, detail, monthly report |
| Tracking | ingest GPS, latest, history `[t1,t2]`, recent moving |
| Alerts | list by day, detail, acknowledge, resolve |
| Admin data | export/import status, backup trigger; restore bằng script xác nhận |

Không xóa vật lý user/xe/tài xế/trip đang được tham chiếu; dùng deactivate/cancel.

## 7. Thứ tự thực hiện

### P0 — Khóa phạm vi/rubric

1. Chốt DBeaver Lite/trial; kiểm tra license trên máy demo, TablePlus fallback.
2. Chốt retention GPS (đề xuất 90 ngày), 10 xe seed, interval 3–5 giây.
3. Tạo checklist 10 điểm và thư mục ảnh bằng chứng.

Qua phase khi nhóm duyệt access patterns, role matrix, demo flow và phân công.

### P1 — Environment spike

1. Docker Compose một Scylla node có volume/healthcheck.
2. Chứng minh `nodetool status`, `cqlsh`, Python `cassandra-driver` kết nối.
3. DBeaver kết nối `localhost:9042`, chạy smoke CQL.

Qua phase khi clean start chạy trên máy demo chính và ít nhất một máy dự phòng.

### P2 — Query-first schema

1. Viết file basic/advanced query trước schema.
2. Chốt key cho Q1–Q14; schema + TTL/TWCS + prepared-query catalog.
3. Review loại full scan/`ALLOW FILTERING`.

Qua phase khi mọi query ánh xạ được tới table và đủ partition key.

### P3 — Seed/import-export/GUI

1. Seed idempotent: 3 role user, 10 xe, 8–10 tài xế, 20+ trip, geofence, alert, ≥3.000 GPS event.
2. Chạy query bằng cqlsh và DBeaver; lưu screenshot.
3. `COPY TO/FROM` CSV; đối chiếu row count trước/sau.

Qua phase khi dữ liệu đáp ứng mọi query rubric và có bằng chứng GUI.

### P4 — Backend nền tảng

1. Config, Scylla session, readiness, prepared statements.
2. Login, password hash, token, role guard.
3. CRUD user/vehicle/driver/trip và denormalized writes.

Qua phase khi role tests/CRUD chạy và Viewer bị từ chối write.

### P5 — Tracking/simulator

1. Ingest validate GPS + chống trùng event ID.
2. Ghi history/latest/activity; simulator nhiều xe.
3. API latest, multi-day history, recent-moving dedupe.

Qua phase khi simulator chạy 10 phút không lỗi, history đúng thứ tự, latest đúng timestamp.

### P6 — Alert/report

1. Overspeed, geofence cooldown/transition, lost-signal scheduler/dedupe.
2. Trip distance và monthly driver report.
3. Test timestamp trễ, GPS trùng, mất tín hiệu, ngoài vùng.

Qua phase khi mỗi alert xuất hiện đúng một lần trong kịch bản và report khớp seed.

### P7 — Frontend/demo

1. Login/RBAC UI; dashboard xe, tài xế, trip, alert.
2. Leaflet latest markers; history polyline.
3. CRUD forms, filter, health, export/backup cho Admin.

Qua phase khi chạy được: login → start trip → GPS → map/history → alert → end trip/report.

### P8 — Backup/restore/bàn giao

1. `COPY TO/FROM` là bằng chứng import/export/restore tối thiểu.
2. Backup schema; `nodetool snapshot` là minh họa bổ sung; restore script có xác nhận/log.
3. Clean-room test theo README.
4. Hoàn thiện Word 50–60 trang, PowerPoint, source, screenshot và demo script.

Kết thúc khi checklist đủ 10 điểm, source chạy lại được và từng thành viên trình bày được phần tích hợp.

## 8. Phân công nhóm

### Phạm Gia Khánh — Data/Integration Lead

- Access patterns, schema/key, Docker Compose, DBeaver.
- Seed/import/export/backup/restore, CQL và bằng chứng GUI.
- Tích hợp cuối, checklist rubric, chương thiết kế/kiểm thử dữ liệu.

### Trà Ngọc Nguyên Vũ — Backend Lead

- FastAPI, Scylla session/prepared statements.
- Authentication/RBAC, CRUD user/vehicle/driver/trip.
- GPS ingestion, alert services, tests và API docs.

### Lê Hữu Luân — Frontend/Demo Lead

- HTML/CSS/JS, Leaflet, history, dashboard/filter.
- GPS simulator và kịch bản overspeed/geofence/GPS lost.
- Chức năng DBeaver, so sánh TablePlus, PowerPoint/demo script.

Việc chung: cả nhóm duyệt schema/API ở P0; cuối mỗi phase tích hợp trên máy Khánh rồi hai người còn lại chạy lại. Báo cáo ghi commit/file/ảnh minh chứng từng người.

## 9. GUI Tool và lý thuyết

### DBeaver cần trình bày

- Tạo/test CQL connection; host/port/keyspace/driver.
- Database Navigator: keyspace/table/column.
- CQL editor, history, result grid, data viewer/filter.
- Import/export CSV và lưu bằng chứng query.
- Giới hạn: Cassandra connector hiện thuộc DBeaver Lite/Enterprise/Ultimate; cần trial/license.

### So sánh DBeaver và TablePlus

| Tiêu chí | DBeaver Lite/trial | TablePlus |
|---|---|---|
| CQL/schema/data view | Navigator/editor mạnh | Giao diện gọn, nhanh |
| Import/export | Nhiều tùy chọn | Đơn giản hơn |
| Tài nguyên/độ học | Nặng, nhiều chức năng | Nhẹ, dễ học |
| Edition | Cassandra không thuộc Community theo docs hiện hành | Kiểm tra giới hạn bản miễn phí/driver sớm |
| Vai trò | GUI chính | So sánh/fallback |

ScyllaDB hợp time-series, IoT/telemetry, ghi lớn, đọc theo device/key và thời gian; không hợp join ad-hoc hoặc transaction nhiều entity kiểu RDBMS.

## 10. Rủi ro/edge cases

| Rủi ro | Xử lý |
|---|---|
| DBeaver Community thiếu Cassandra | Lite/trial; smoke-test P1; TablePlus fallback |
| `cassandra-driver` lệch phiên bản | Pin sau P1; không tự đổi driver khi chưa hỏi Khánh |
| Scylla chậm/thiếu RAM Windows | Healthcheck/wait; một node; ghi mức RAM Docker cần thiết |
| Partition GPS vô hạn | Bucket xe+ngày; activity theo giờ; TTL |
| Query qua nhiều ngày | Tách ngày có giới hạn, merge/sort, pagination |
| Event trùng/out-of-order | event_id idempotency, UTC; latest chỉ nhận timestamp mới hơn |
| Denormalized write dở dang | Một service sở hữu; retry idempotent; reconciliation khi test chứng minh cần |
| Alert spam | Cooldown/state transition; một alert mở/xe/loại |
| GPS lost giả khi xe nghỉ | Chỉ kiểm tra xe/trip active |
| Bounding box qua kinh tuyến 180° | Ngoài scope; demo trong Việt Nam |
| GPS noise làm sai km | Haversine + lọc bước nhảy/tốc độ phi thực tế |
| Map mất Internet | Leaflet local; fallback coordinate/polyline không tile |
| Restore phá dữ liệu | Admin-only, xác nhận, backup trước, script riêng |
| Secret trong source | `.env`, hash password, example không có secret thật |
| Frontend giả quyền | Role guard backend + test 403 |
| App chạy nhưng thiếu điểm | Checklist + screenshot/query/row-count/log theo từng rubric |

## 11. Tiêu chí hoàn thành

- `docker compose up --build` chạy ScyllaDB, FastAPI/frontend, simulator theo README.
- Health đúng; DBeaver kết nối `localhost:9042`.
- Seed ≥3 user role, 10 xe, 8 tài xế, 20 trip, 3.000 GPS event; chạy lại không trùng ngoài chủ ý.
- Không query bắt buộc dùng `ALLOW FILTERING`; history qua ít nhất hai ngày bucket.
- RBAC backend đúng; password không plain text.
- Map latest/history và simulator hoạt động; ba loại alert tái hiện được.
- Monthly trip/km report khớp dữ liệu seed/kịch bản.
- `COPY TO/FROM` và backup/restore test có row-count/log.
- Có lý thuyết+cài đặt ScyllaDB/DBeaver, chức năng DBeaver, so sánh TablePlus và use case phù hợp.
- Demo đủ user/RBAC; CRUD/backup; tracking/history/alert; simulator/report/filter.
- Báo cáo 50–60 trang, TNR 13, line 1,5; đủ Word, PowerPoint, source; có phân công/bằng chứng từng thành viên.

## 12. Tài liệu kỹ thuật khi code

- Docker: https://docs.scylladb.com/manual/master/getting-started/install-scylla/run-in-docker.html
- Query bucketing: https://docs.scylladb.com/stable/get-started/data-modeling/query-design.html
- TTL: https://docs.scylladb.com/manual/stable/cql/time-to-live.html
- `COPY TO/FROM`: https://docs.scylladb.com/manual/stable/cql/cqlsh.html
- Backup: https://docs.scylladb.com/manual/stable/operating-scylla/procedures/backup-restore/backup.html
- DBeaver Cassandra: https://dbeaver.com/docs/dbeaver/Cassandra/

