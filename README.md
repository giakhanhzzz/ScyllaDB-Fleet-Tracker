# ScyllaDB Fleet Tracker

Đồ án 14: Quản lý dữ liệu theo dõi vị trí phương tiện vận tải và lịch sử hành trình của đội xe.
Nhóm: Phạm Gia Khánh, Trà Ngọc Nguyên Vũ, Lê Hữu Luân.

## Trạng thái thực tế — 28/09/2026

Đã nhận source trên GitHub tại commit `0c0c04d6db970c44039f576481a2e2f228208fda`.
Bản rà soát sửa lỗi nền tảng được chuẩn bị từ nhánh `codex/fix-demo-foundation`;
Khánh đã yêu cầu nhập bản sửa vào `main`.
Không có bằng chứng chạy trọn hệ thống với ScyllaDB; chưa được gọi là đồ án hoàn chỉnh.

| Thành phần | Hiện có | Còn thiếu/chưa xác minh |
| --- | --- | --- |
| Hạ tầng | Compose một Scylla node; profile demo cho API/simulator | Docker/CQL/volume thực tế |
| CSDL | 15 bảng query-first, Q1–Q14; TTL GPS 90 ngày, activity 48 giờ | Thực thi schema/truy vấn trên Scylla và GUI |
| Seed | 3 user, 10 xe, 8 tài xế, 20 chuyến, 3.200 GPS, 1 cảnh báo mẫu | Nạp vào CSDL thật; km chuyến hoàn tất là số liệu fixture |
| API | Đăng nhập, đọc user/xe/tài xế/chuyến; tạo chuyến; ingest/lịch sử/latest, xe di chuyển, xử lý cảnh báo, thống kê | CRUD đầy đủ; start/end/cancel chuyến; nối tính km khi kết thúc; GPS_LOST |
| Backup/restore | Script COPY CSV 15 bảng, kiểm đếm, xác nhận và backup an toàn | Chạy thử/đối chiếu thực tế; không phải snapshot SSTable |
| Giao diện | React prototype trong `src/`, đã gắn nhãn mô phỏng | Frontend tĩnh theo kế hoạch và kết nối API thật |
| Kiểm thử | 24 test logic/API đạt; Python AST, YAML cơ bản và PowerShell parser đạt | Không thay thế integration test ScyllaDB |

## Cấu trúc và nguyên tắc

Kế hoạch gốc: `KE_HOACH_DO_AN_SCYLLADB.md`.
`Hệ thống/` giữ quy định giảng viên, luật làm việc, kiến thức môn học và nhật ký.
Không thay thế các file gốc bằng bản AI dựng lại.

- `database/`: schema, truy vấn, seed, import/export.
- `backend/app/`: FastAPI, driver Cassandra, bảo mật và nghiệp vụ.
- `backend/tests/`: kiểm thử có DB giả lập rõ ràng.
- `simulator/`: tiến trình gửi GPS qua API đã đăng nhập.
- `scripts/`: khởi tạo, kiểm tra CQL, COPY backup/restore và reset có xác nhận.
- `docs/`: GUI, kịch bản demo và bằng chứng kiểm thử.

Runtime Docker không dùng React/Vite hay dịch vụ ngoài kế hoạch. Các file
`src/`, `package.json`, `vite.config.ts`, `index.html` ở root là prototype
Gemini cũ, chưa phải frontend cuối cùng. Giữ lại để tham khảo giao diện; không
đánh dấu chức năng prototype là đã làm trên ScyllaDB.

## Kiểm chứng P1 trước

Chạy ở thư mục repo bằng PowerShell 7, trên máy có Docker Compose và Linux Engine:

```powershell
docker info
docker compose config --quiet
docker compose up -d --wait scylla
docker compose exec -T scylla nodetool status
docker compose exec -T scylla cqlsh -e "SELECT release_version FROM system.local;"
```

Kết quả mong đợi: node UN, CQL đọc được metadata. Đây là hướng dẫn, không phải
log PASS. Cần đo tài nguyên máy thực tế; không áp đặt ngưỡng 4 GB RAM trống chưa
có căn cứ. Cổng CQL chỉ bind `127.0.0.1:9042`, không public API quản trị 10000.

## Khởi tạo backend và dữ liệu mẫu

Sau khi gate P1 đạt:

```powershell
./scripts/init_demo.ps1
```

Script tạo `.env` với khóa JWT ngẫu nhiên nếu chưa có, build image Python 3.11,
dừng writer trước seed, kiểm tra CQL, nạp schema/seed rồi bật backend.
Nếu `.env` đã tồn tại, tự kiểm tra `SECRET_KEY` có ít nhất 32 ký tự.
Không commit `.env`, CSV backup hoặc dữ liệu người dùng thật.

- API docs: `http://localhost:8000/docs`; health: `http://localhost:8000/health`.
- Tài khoản demo local: `khanh_admin`, `vu_dispatcher`, `luan_viewer`.
- Mật khẩu demo chung: `Password123@`; không dùng ngoài môi trường local.
- Seed mặc định ngày UTC `2026-09-28`, gồm ngày trước đó. Dùng đúng ngày này
  khi chạy các CQL mẫu; simulator tạo dữ liệu tại thời điểm hiện tại.
- Chạy seed lại cùng ngày giữ nguyên primary key GPS. Đây không phải reset toàn
  dữ liệu hay giữ nguyên trạng thái đã chỉnh sửa. Nếu đổi SEED_DATE, cần reset
  có backup/xác nhận và điều chỉnh ngày trong truy vấn mẫu.

Bật GPS giả lập sau khi API đã chạy:

```powershell
docker compose --profile demo up -d simulator
docker compose --profile demo logs --tail 30 simulator
```

Simulator gửi mỗi 3–5 giây, mặc định 4; dùng dispatcher JWT.
GPS cần timestamp có timezone, UUID v1 cùng millisecond; company/trip không do
client tùy ý gán. Backend lấy company từ user đang hoạt động trong CSDL.

## Import/export và backup/restore

`python` trên host chỉ cần thư viện chuẩn để gọi COPY trong container:

```powershell
python database/import_export.py export vehicles_by_id ./vehicles.csv
python database/import_export.py import vehicles_by_id ./vehicles.csv
docker compose --profile demo stop simulator backend
./scripts/backup.ps1
./scripts/restore.ps1 -BackupDir "./docs/backups/<ten-ban-backup>"
```

Backup từ chối chạy khi backend/simulator đang hoạt động; đồng thời phải dừng
các writer ngoài ứng dụng, kể cả GUI. Restore yêu cầu schema 15 bảng tương ứng
đã tồn tại, hỏi gõ RESTORE, lưu dữ liệu hiện tại trước TRUNCATE và kiểm đếm đủ
15 bảng trước bật backend lại. `schema.cql` trong backup là tài liệu khôi phục
DDL, không tự apply lên keyspace đang có.

COPY là backup logic: TTL được tính lại khi import; row count bằng nhau chưa
chứng minh dữ liệu từng ô hoặc expiry giống hệt. Reset yêu cầu gõ RESET và
backup an toàn; chưa thực thi reset/restore khi rà soát.

## Chạy test logic độc lập

Tạo venv riêng, cài `backend/requirements.txt` và `httpx` để chạy TestClient,
không cài vào Python toàn cục nếu chưa thống nhất môi trường.

```powershell
python -m unittest discover -s backend/tests -v
```

Các test chủ động giả lập DB và không chạy lifespan kết nối Scylla. Xem
`docs/TEST_EVIDENCE.md` để biết đúng phạm vi bằng chứng.

## Thứ tự tiếp tục và phân công

Theo phase trong kế hoạch gốc: xác minh P1 → chạy schema/query/seed thật →
hoàn thiện API và vòng đời chuyến/cảnh báo → frontend tĩnh kết nối thật →
import/backup/restore đối chiếu → demo/báo cáo. Không coi skeleton do Gemini
viết qua nhiều phase là các gate đã đạt.

- Khánh: hạ tầng, model/query/seed, GUI và tích hợp/bằng chứng.
- Vũ: auth/RBAC, CRUD API, vòng đời chuyến, GPS/cảnh báo và kiểm thử.
- Luân: frontend tĩnh + Leaflet, simulator và workflow demo.

Không thêm bảng/framework/tính năng ngoài kế hoạch để chữa thiếu sót.
