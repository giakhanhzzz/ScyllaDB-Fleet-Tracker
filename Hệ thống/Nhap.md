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
