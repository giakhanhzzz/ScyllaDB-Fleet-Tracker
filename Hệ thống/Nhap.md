# Temp Notes — NoSQL Project

> Nhật ký nháp bền vững. Không xóa mục cũ; khi đã chốt, giữ lại quyết định và liên kết/tóm tắt nó trong `TAKENOTE_NOSQL.md`.

## Quy ước trạng thái

- `[MỞ]`: đang bàn, chưa chốt.
- `[CẦN KIỂM CHỨNG]`: thiếu dữ liệu hoặc cần đối chiếu tài liệu/phiên bản.
- `[ĐÃ CHỐT]`: quyết định có thể dùng; phải tóm tắt sang Takenote.
- `[BỎ]`: phương án không chọn; giữ lý do để không lặp lại tranh luận.

## Nhật ký

### 2026-09-09 — Khởi tạo

- `[ĐÃ CHỐT]` Thư mục quản lý chuẩn: `C:\Users\artis\Downloads\Project_NoSql`.
- `[ĐÃ CHỐT]` Ghi nhớ dùng bốn lớp: Takenote (kiến thức chốt), Temp Notes (nháp/vấn đề), Rules (cách làm việc), Project Guidelines (khung đồ án/báo cáo).
- `[MỞ]` Chưa có đề tài đồ án, use case, stack ứng dụng hoặc rubric chính thức.

### 2026-09-09 — Hoàn tất đọc Chương 3 Cassandra

- `[ĐÃ CHỐT]` Đã đọc `Chương 3. Cassandara.md` và cập nhật `TAKENOTE_Baihoc_NOSQL.md` về kiến trúc commit log/memtable/SSTable, compaction, query-first, partition/clustering key, collection/UDT/materialized view và C# prepared statement.
- `[CẦN KIỂM CHỨNG]` File nguồn bị lỗi OCR/chuyển đổi ở nhiều đoạn CQL; không dùng nguyên văn lệnh bị vỡ tên bảng, dấu nháy hoặc JSON. Khi triển khai Cassandra sẽ viết lại cú pháp chuẩn, chạy kiểm chứng trên phiên bản cụ thể.
- `[CẦN KIỂM CHỨNG]` Môi trường Cassandra 3.11.4 + JDK 8 + Python 2.7 trong tài liệu là cũ; chỉ chốt phiên bản cài đặt sau khi có yêu cầu stack/đồ án.

### 2026-09-14 — Chốt đề tài 14 và kế hoạch ScyllaDB

- `[ĐÃ CHỐT]` Đề tài: quản lý vị trí phương tiện và lịch sử hành trình đội xe bằng ScyllaDB/Column Family.
- `[ĐÃ CHỐT]` Nhóm: Phạm Gia Khánh, Trà Ngọc Nguyên Vũ, Lê Hữu Luân.
- `[ĐÃ CHỐT]` Stack: ScyllaDB Docker, Python `cassandra-driver`, FastAPI, web + Leaflet, Docker Compose, seed và GPS simulator.
- `[ĐÃ CHỐT]` Đã cập nhật rubric vào `PROJECT_QUYDINH.md` và lưu kế hoạch tại `C:\Users\artis\Downloads\Project_NoSql\KE_HOACH_DO_AN_SCYLLADB.md`.
- `[ĐÃ CHỐT]` Phạm vi tối thiểu: một Scylla node, FastAPI phục vụ API + frontend tĩnh; không thêm React/Kafka/Redis/microservice.
- `[ĐÃ CHỐT]` Schema query-first: GPS bucket xe+ngày, activity theo giờ, clustering theo thời gian; latest và bảng nghiệp vụ denormalized; không `ALLOW FILTERING`.
- `[CẦN KIỂM CHỨNG]` Cassandra connector theo tài liệu DBeaver hiện thuộc Lite/Enterprise/Ultimate; cần thử edition/license trên máy demo. TablePlus là fallback/GUI so sánh.
- `[CẦN KIỂM CHỨNG]` Yêu cầu khóa `cassandra-driver`, trong khi ScyllaDB có Python driver riêng; P1 phải smoke-test đúng Python/Scylla và chưa được tự đổi driver.
- `[MỞ]` Khánh cần chốt retention GPS (đề xuất 90 ngày), cấu hình máy demo, deadline/tuần báo cáo và DBeaver edition thực tế.

### 2026-09-14 — P0 đang chờ xác nhận trước khi lập trình

- `[MỞ]` Đã đọc lại kế hoạch và bắt đầu đúng Phase P0; chưa tạo/sửa mã nguồn vì kế hoạch yêu cầu nhóm xác nhận các quyết định mở.
- `[MỞ]` Cần Khánh xác nhận có dùng các mặc định của kế hoạch: DBeaver Lite/trial (TablePlus làm GUI so sánh/fallback), TTL GPS 90 ngày, seed 10 xe, simulator gửi mỗi 3–5 giây.
- `[MỞ]` Cần xác nhận role matrix, luồng demo và phân công ba thành viên trong kế hoạch đã được nhóm chốt; sau xác nhận mới chuyển sang P1.

### 2026-09-14 — Xác nhận P0 của Khánh

- `[ĐÃ CHỐT]` Khánh đồng ý các mặc định P0: DBeaver Lite/trial (TablePlus fallback), TTL GPS 90 ngày, 10 xe seed và simulator 3–5 giây.
- `[ĐÃ CHỐT]` Role matrix, luồng demo và phân công ba thành viên được xem là đã xác nhận theo kế hoạch.
- `[CẦN KIỂM CHỨNG]` Kiểm tra thực tế không tìm thấy DBeaver hoặc TablePlus trong PATH/Start Menu; chưa thể đánh dấu kiểm GUI hoàn tất và chưa được tự ý cài/đổi công cụ.

### 2026-09-14 — Báo cáo preflight từ AI local

- `[ĐÃ CHỐT]` Báo cáo độc lập xác nhận các quyết định P0 nhất quán: retention 90 ngày, 10 xe seed, simulator 3–5 giây, GUI dự kiến DBeaver Lite/trial + TablePlus fallback và đúng ba thành viên.
- `[CẦN XỬ LÝ]` DBeaver và TablePlus chưa cài; chưa xác minh edition/license/connector. Không tự cài hoặc đổi GUI khi chưa có chỉ đạo.
- `[CẦN XỬ LÝ]` Docker Desktop đã cài nhưng Docker Engine đang dừng; chưa chạy được Scylla container.
- `[CẦN XỬ LÝ]` RAM trống lúc kiểm tra chỉ khoảng 300–600 MB, chưa phù hợp để chạy Docker + Scylla; cần giải phóng RAM hoặc chọn máy demo khác.
- `[MỞ]` Kế hoạch chưa chốt interpreter Python chuẩn: Laragon Python 3.13 đã có `cassandra-driver` 3.30.1 hay Python 3.12 riêng. Chưa tự quyết.
- `[TẠM DỪNG]` Chưa bắt đầu code P1 vì các quyết định/điều kiện trên chưa được Khánh xác nhận; giữ đúng thứ tự phase và quy tắc không suy đoán.

### 2026-09-14 — Preflight lần hai: BLOCKED

- `[ĐÃ XÁC MINH]` Docker Engine vẫn dừng; Docker Compose chỉ có client. Không thể chạy ScyllaDB, `nodetool`, `cqlsh` hay smoke-test P1.
- `[ĐÃ XÁC MINH]` RAM trống khoảng 614 MB trên máy hiện tại, thấp hơn ngưỡng 4 GB cần cho Docker + ScyllaDB demo.
- `[ĐÃ XÁC MINH]` DBeaver và TablePlus chưa cài; edition/trial/license/Cassandra connector đều chưa kiểm chứng được.
- `[ĐÃ XÁC MINH]` Laragon Python 3.13 có `cassandra-driver` 3.30.1 và import được; Python 3.12 chưa có driver.
- `[MỞ]` Khánh cần chốt interpreter chuẩn (Laragon 3.13 hoặc Python 3.12), người/thời điểm cài GUI, và phương án giải phóng RAM hoặc đổi máy demo.
- `[TẠM DỪNG]` Không tạo `docker-compose.yml` trước khi môi trường P1 chạy được, để giữ đúng phase và tránh mã nguồn chưa thể kiểm chứng.

### 2026-09-28 — Nhận source GitHub và sửa nền tảng Gemini

- `[ĐÃ XÁC MINH]` Repo giakhanhzzz/ScyllaDB-Fleet-Tracker đã push main,
  commit nguồn 0c0c04d6db970c44039f576481a2e2f228208fda. Không còn coi source
  chỉ nằm ở /app/applet hoặc phụ thuộc link ZIP yêu cầu đăng nhập.
- `[ĐÃ CHỐT]` Folder chuẩn vẫn là C:\Users\artis\Downloads\Project_NoSql.
  Giữ kế hoạch và bốn file Hệ thống gốc của Khánh, không thay bằng bản Gemini
  tự dựng lại. Nhật ký này chỉ bổ sung; TAKENOTE môn học không trộn với log code.
- `[SAI SÓT ĐÃ LÀM RÕ]` Source Gemini đi qua nhiều phase nhưng React chỉ dùng
  state mô phỏng; API/CQL/backup chưa chạy với Scylla. Không được gọi hoàn chỉnh,
  không dùng UI đổi role hay toast thành bằng chứng RBAC/backup thật.
- `[ĐÃ SỬA MÃ NGUỒN]` Auth kiểm tra hash scrypt có salt, JWT secret bắt buộc;
  quyền/company lấy từ user active trong DB. API không nuốt lỗi bằng mock,
  unavailable trả 503. Chuẩn hóa UTC/date trong response.
- `[ĐÃ SỬA MÃ NGUỒN]` GPS kiểm tra UUID v1 cùng timestamp, bounds/timezone,
  ownership; event trễ không đè latest, kiểm tra kết quả LWT. History đa ngày
  giới hạn range; activity đọc đúng bucket, báo cáo đúng month/COMPLETED.
- `[ĐÃ SỬA MÃ NGUỒN]` Seed có primary key GPS ổn định, month bucket theo
  trip date; thời gian GPS hôm nay khớp chuyến đang chạy. Compose một node
  mặc định, API/simulator profile demo; không expose management API ra host.
- `[ĐÃ SỬA MÃ NGUỒN]` COPY dùng cqlsh thật trong container; backup kiểm tra
  writer dừng, restore/reset xác nhận và tạo backup an toàn. Logical restore
  yêu cầu schema tương ứng đã tồn tại; không tự apply CREATE lên bảng hiện có.
  TTL bắt đầu lại khi COPY import, không gọi đây là snapshot vật lý.
- `[ĐÃ XÁC MINH]` 24 test logic/API đạt với venv test riêng, Python AST 15 file
  đạt, parser 4 PowerShell script đạt, YAML cơ bản và diff whitespace source
  đã sửa đạt (note/kế hoạch gốc giữ nguyên định dạng).
  DB trong test là fake: không đủ để nghiệm thu phase phụ thuộc CSDL thật.
- `[CẦN KIỂM CHỨNG]` Phiên hiện tại chưa tìm thấy Docker CLI ở PATH/đường dẫn
  đã thử; chưa chạy Scylla. RAM query bị Access denied, không có số đo mới.
  Số RAM ngày 14/09 là lịch sử; ngưỡng 4 GB trống khi ấy chưa có căn cứ chuẩn.
  Có thể soạn/sửa mã nhưng không được đánh dấu gate runtime PASS.
- `[CÒN THIẾU]` CRUD đầy đủ, vòng đời trip/start/end/cancel và gắn trip mới vào
  GPS, tính km lúc end trip; GPS_LOST và state alert bền qua retry/restart;
  frontend tĩnh nối API; integration CQL/GUI/backup; Word/PPT/demo đầy đủ.
  React được giữ dưới nhãn prototype và không có trong Docker runtime.
- `[ĐÃ CHUẨN HÓA]` README/GUI/DEMO_SCRIPT/TEST_EVIDENCE phân biệt mã đã viết,
  test logic và phần chưa chạy. Gộp checklist trùng vào TEST_EVIDENCE;
  bản CHECKLIST_BANG_CHUNG.md cũ còn khôi phục được từ commit nguồn.
- `[CHƯA THỰC HIỆN]` Không git push, không cài GUI/mua license, không chạy
  reset/restore/DROP/TRUNCATE trong lần rà soát. Nhánh local sửa lỗi:
  codex/fix-demo-foundation. Tiếp tục theo gate/phase trong kế hoạch gốc,
  không thêm bảng hoặc framework để che phần thiếu.

### 2026-09-28 — Khánh yêu cầu nhập bản sửa vào main

- `[ĐÃ CHỐT]` Khánh đồng ý commit và nhập bản sửa đã rà soát vào main của
  giakhanhzzz/ScyllaDB-Fleet-Tracker, không chỉ giữ ở nhánh local.
- `[ĐÃ XÁC MINH]` Fetch trước khi bàn giao: origin/main vẫn ở
  0c0c04d6db970c44039f576481a2e2f228208fda, chưa có commit mới/xung đột.
  Các file local trước cập nhật log khớp bản source đã chạy 24 test.
- `[PHẠM VI]` Chỉ commit source/test/tài liệu dự án đã rà soát. Không đưa
  tài liệu môn học chưa track, backup CSV, .env hoặc secret vào commit.
  Dùng fast-forward và push thường; không force-push hay đổi lịch sử cũ.
- `[CẦN NHỚ]` Bản trên main vẫn là nền tảng đã sửa lỗi, chưa phải demo hoàn
  chỉnh. Các gate Docker/Scylla/GUI/backup thực tế và chức năng còn thiếu giữ
  nguyên trong TEST_EVIDENCE; không tự tick PASS khi phát hành mã nguồn.

### 2026-10-03 — Main local và lát cắt frontend thật

- `[ĐÃ XÁC MINH]` origin/main vẫn ở 0c0c04d trước lần bàn giao; commit sửa lỗi
  1c7d9e4 đã vào main local bằng fast-forward, không force. Push bị bộ kiểm
  duyệt an toàn chặn vì repo public và commit chứa file ghi nhớ/quy định nội bộ.
  Không được tuyên bố mã mới đã lên GitHub; đã hỏi Khánh chọn giữ private hay
  cho công khai, không lách chặn.
- `[ĐÃ VIẾT - CHƯA TÍCH HỢP SCYLLA]` Frontend tĩnh HTML/CSS/JS theo kế hoạch,
  FastAPI phục vụ tại /; Leaflet 1.9.4 tải từ package npm chính thức và lưu
  cục bộ kèm LICENSE/icons. Login dùng /api/auth/login + /api/auth/me thật,
  danh sách xe/tài xế/chuyến/cảnh báo và GPS/latest/history qua API; Viewer
  không có nút cập nhật alert. React cũ vẫn được gắn nhãn prototype.
- `[ĐÃ XÁC MINH]` TestClient GET / và static assets chạy, API không bị static
  che; tổng 26 unit/API tests đạt với DB fake, gồm Viewer 403 khi xử lý alert.
  node --check app.js đạt.
  Không có Docker CLI/Scylla kết nối trong phiên này; chưa có browser E2E.
- `[CÒN THIẾU]` Frontend CRUD đầy đủ, vòng đời trip, cảnh báo GPS_LOST,
  kiểm chứng CQL/GUI/backup và demo tích hợp thật. Lát cắt hiện tại chỉ
  là xem dữ liệu + xử lý alert qua backend đã có, chưa là phase P7 PASS.
- `[ĐÃ VIẾT - CHƯA TÍCH HỢP SCYLLA]` P4 quản trị user: Admin tạo tài khoản
  trong công ty hiện tại, đổi role/active/password/full_name; ghi cả bảng
  users_by_username và users_by_company. Client không truyền company_id,
  không cho Admin tự khóa/bỏ quyền. UI có form tạo/đổi role/khóa cho Admin.
- `[ĐÃ XÁC MINH]` 32 test fake-DB/API đạt, gồm Viewer 403, công ty giả bị
  từ chối, user khác công ty 404, self-lock 409 và hai projection được ghi.
  Vẫn cần kiểm chứng batch CQL thật, đăng nhập user mới và vô hiệu token sau
  khóa trên Scylla trước khi nghiệm thu.
- `[ĐÃ VIẾT - CHƯA TÍCH HỢP SCYLLA]` P4 CRUD xe/tài xế: Admin và Dispatcher
  tạo, xem chi tiết, cập nhật, vô hiệu hóa mềm; cập nhật đủ bảng theo ID và
  projection theo công ty/trạng thái. Đổi trạng thái xe xóa khóa cũ rồi insert
  khóa mới trong logged batch; tạo xe đồng thời thêm geofence TP.HCM như seed.
  Tài xế còn gắn xe không thể bị khóa; Viewer bị backend 403.
- `[ĐÃ XÁC MINH]` Tổng 39 test fake-DB/API đạt, frontend có form user/xe/tài
  xế, node --check app.js đạt. Chưa có Docker CLI/Scylla thật nên không tick
  phase P4/P7. CQL batch, projection sau restart, geofence xe mới và UI cần
  kiểm chứng bằng demo thật.
- `[GIỚI HẠN]` Chống trùng ID vẫn là read-before-write, không CAS/isolation.
  Kiểm tra xe gắn tài xế đọc 4 partition status của công ty; hợp demo 10 xe,
  cần bảng tra theo tài xế nếu tăng quy mô. Bounding box geofence mặc định
  chưa có API/UI chỉnh sửa.

### 2026-10-03 — Tạo chuyến kế hoạch và quyết định công bố

- `[ĐÃ VIẾT - CHƯA TÍCH HỢP SCYLLA]` Frontend tĩnh có form tạo trip PLANNED;
  xe phải khả dụng, có tài xế đang active và được gán đúng xe. Backend kiểm
  lại các điều kiện này, ghi ba projection trip theo batch. Chưa có start/end/
  cancel hoặc liên kết GPS của trip mới.
- `[ĐÃ XÁC MINH]` 41 test fake-DB/API đạt; node --check frontend/app.js đạt.
  Không có bằng chứng CQL thực, UI browser E2E hay Scylla runtime.
- `[ĐÃ CHỐT BỞI KHÁNH]` Repo public được phép chứa cả bốn file Hệ thống/
  ghi nhớ/quy định trong commit local. Quyết định này chỉ giải quyết phạm vi
  công bố source hiện tại, không cho phép đưa .env, backup hay dữ liệu thật lên.
- `[ĐÃ XÁC MINH]` Sau quyết định trên, commit `1e7e5fb` chứa frontend/API/
  test/tài liệu đã push thành công lên `origin/main` cùng commit nền tảng
  `1c7d9e4`. Đây là phát hành mã nguồn, không phải nghiệm thu Scylla/GUI.
