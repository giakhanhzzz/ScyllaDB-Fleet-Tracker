# Bằng chứng kiểm thử và gate nghiệm thu

## Nguồn và môi trường — 28/09/2026

Source GitHub đã tải được; commit gốc:
`0c0c04d6db970c44039f576481a2e2f228208fda`.
Nhánh chuẩn bị bản sửa: `codex/fix-demo-foundation`.
Khánh đã đồng ý commit và nhập bản sửa vào `main`; trạng thái phát hành xác minh
bằng commit/ref GitHub, không đồng nghĩa các gate ScyllaDB đã đạt.

- Python test: 3.13, venv tạm riêng; đã cài đúng các bản pin trong requirements.
- `cassandra.cluster` import được; điều này không chứng minh kết nối CSDL.
- Phiên kiểm tra hiện tại không tìm được lệnh Docker qua PATH/các đường dẫn
  thông thường đã kiểm tra. Chưa chạy container; không kết luận Docker đã bị
  gỡ hoặc Engine luôn dừng chỉ từ kiểm tra này.
- Truy vấn RAM qua Win32_OperatingSystem bị Access denied. Không có số đo RAM
  mới; không ghi 0 MB, không dùng số đo cũ làm hiện trạng.
- Docker/GUI/RAM trong báo cáo 14/09 là bằng chứng lịch sử, không phải hiện tại.
  Ngưỡng 4 GB RAM trống ở báo cáo cũ chưa có căn cứ nghiệm thu.
- Không cài GUI, không push, không chạy TRUNCATE/DROP/restore/reset khi rà soát.

## Đã chạy thực tế

| Kiểm tra | Kết quả | Giới hạn |
| --- | --- | --- |
| `python -m unittest discover -s backend/tests -q` | PASS — 24 tests, OK | DB giả lập; không có Scylla server |
| Python `ast.parse` cho source backend/database/scripts/simulator | PASS — 15 file | Cú pháp, không phải hành vi CQL |
| `yaml.safe_load` + kiểm tra service/profile | PASS | Không thay cho `docker compose config` |
| PowerShell Parser cho 4 script .ps1 | PASS — 0 lỗi parse | Chưa thực thi Docker/backup |
| `git diff --check` cho source đã sửa (không gồm note/kế hoạch gốc) | PASS | Note gốc giữ nguyên định dạng; không thay thế test ứng dụng |

Phạm vi test: mật khẩu đúng/sai và hash có salt; token sai/hết quyền, user
inactive; Viewer 403; không đăng nhập 401; đọc theo company của DB; DB không
sẵn sàng 503; GPS tọa độ/speed/heading/UUID/timezone; không cho client giả company;
geofence không nuốt lỗi; GPS trễ không ghi đè latest; LWT không applied không
báo cập nhật thành công; lịch sử đọc cả hai bucket ngày; UTC/date trả rõ nghĩa;
Haversine và lọc điểm nhảy/đồng thời; seed chạy hai lần giữ 3.200 GPS primary keys,
month bucket theo ngày chuyến kể cả qua ranh giới tháng.

TestClient trong test không chạy startup thật; mọi fake DB được ghi rõ trong
source test. Không dùng các kết quả này để tick CQL, integration hay đồ án 10/10.

## Gate cần chạy với CSDL thật

| Gate | Tiêu chí PASS / bằng chứng phải lưu | Hiện tại |
| --- | --- | --- |
| P1 Compose | `docker compose config --quiet`, container healthy, CQL và nodetool UN | CHƯA KIỂM CHỨNG |
| P1 Driver | `wait_for_scylla.py` đọc metadata thực bằng cassandra-driver | CHƯA KIỂM CHỨNG |
| P1 GUI | Edition/license/connector, localhost:9042, đọc system.local | CHƯA KIỂM CHỨNG |
| P2 Model/query | 15 bảng, đúng PK/clustering/TTL, Q1–Q14 chạy được không ALLOW FILTERING | CHƯA KIỂM CHỨNG |
| P3 Seed | 3 user, 10 xe, 8 tài xế, 20 chuyến, 3.200 GPS; chạy lại đối chiếu count | CHƯA KIỂM CHỨNG |
| API integration | Đăng nhập, Viewer 403, ingest đọc lại CQL/latest, restart vẫn có dữ liệu | CHƯA KIỂM CHỨNG |
| Nghiệp vụ | CRUD, start/end/cancel, km từ GPS, ba loại alert đúng workflow | CHƯA HOÀN THIỆN |
| Frontend | Leaflet và các thao tác gọi API, role thật, không in-memory giả | CHƯA HOÀN THIỆN |
| COPY + restore | Dừng writer, export đủ 15 bảng, import kiểu đúng, count và mẫu dòng khớp | CHƯA KIỂM CHỨNG |
| Demo/báo cáo | Theo rubric, ảnh/log thật; Word/PPT/source đủ, đúng định dạng | CHƯA HOÀN THIỆN |

Không yêu cầu nodetool báo Owns chính xác 100% hay release string giống ví dụ.
Ghi lại phiên bản/container/datacenter thực tế thay vì chép kết quả mong đợi.

## Nợ còn lại, không che bằng mock

1. React prototype chưa gọi FastAPI. Chưa có frontend tĩnh trong `frontend/`
   theo kế hoạch. React không được đưa vào Docker runtime.
2. Chưa đủ CRUD user/xe/tài xế/chuyến; chưa có start/end/cancel chuyến, chặn
   chuyến đồng thời và gắn trip mới vào GPS. Hàm tính km có test nhưng chưa
   nối với API kết thúc chuyến. Km của completed seed là fixture.
3. Chưa có bộ quét GPS_LOST. Chống lặp alert hiện chỉ tra ngày hiện tại/trước đó;
   trạng thái unresolved lâu hơn cần hoàn thiện trong phase cảnh báo.
4. GPS ghi nhiều projection không phải transaction SQL. Retry sau lỗi từng
   phần và alert bị lỗi sau khi latest đã ghi cần integration/recovery test.
   UUID ổn định và latest LWT không giải quyết mọi trường hợp lỗi một phần.
5. Batch nhỏ đồng bộ một nghiệp vụ không tạo isolation hay FK. Tạo trip bằng
   read-before-write chưa chống được mọi race.
6. History dùng offset giới hạn; dữ liệu mới chen vào giữa các trang có thể
   làm offset dịch chuyển. Chỉ hỗ trợ tối đa 7 ngày mỗi request.
7. Seed cùng ngày không nhân đôi GPS nhưng sẽ upsert các fixture nghiệp vụ.
   Đổi ngày khi chưa reset có thể để lại projection cũ.
8. COPY restore yêu cầu schema phù hợp đã có; khởi tạo lại schema khi mất
   keyspace là bước riêng có kiểm soát. TTL bắt đầu lại; chưa có backup SSTable.
9. Chưa benchmark tải, chưa chạy thử build React; chưa được suy ra năng lực
   high-throughput từ simulator vài xe hay một node demo.

## Checklist theo thang điểm giảng viên

Nội dung checklist trước đây ở CHECKLIST_BANG_CHUNG.md được gộp ở đây để tránh
hai nguồn trạng thái. Mỗi mục chỉ tick sau khi có thao tác tái lập và bằng chứng.

- [ ] 1. Lý thuyết/cài đặt ScyllaDB và GUI.
- [ ] 2. Trình bày các chức năng GUI đã trực tiếp thử.
- [ ] 3. So sánh GUI chính với một GUI khác, có edition/OS/version thực tế.
- [ ] 4. Nêu loại ứng dụng phù hợp và giới hạn của ScyllaDB.
- [ ] 5. Schema, dữ liệu đầy đủ, truy vấn cơ bản/nâng cao.
- [ ] 6. Import/export; backup/restore có đối chiếu.
- [ ] 7. Chạy query cơ bản/nâng cao trong GUI.
- [ ] 8. Backend kết nối và đọc/ghi CSDL thật.
- [ ] 9. Demo quản trị user, thao tác CSDL, nghiệp vụ và hỗ trợ.
- [ ] 10. Báo cáo/thuyết trình; Word/PPT/source; phân công và đóng góp từng người.

P0 đã chốt: DBeaver Lite/trial + TablePlus so sánh/dự phòng; TTL GPS 90 ngày;
10 xe; simulator 3–5 giây; nhóm Khánh/Vũ/Luân. Không tự đổi những quyết định này.

Ảnh lưu ở `docs/screenshots/`, tên `p<phase>_<muc>_<mo-ta>.png`.
Ảnh GUI cần thể hiện connection, CQL và kết quả. Không dựng ảnh PASS hoặc ghi
đã tạo thư mục ảnh nếu chưa thực sự có.
