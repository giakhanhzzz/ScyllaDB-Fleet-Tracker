# GUI quản trị: DBeaver Lite/trial và TablePlus

## Điều đã xác minh bằng tài liệu chính thức

Driver Cassandra của DBeaver nằm trong Lite, Enterprise và Ultimate, không
mặc định coi Community là lựa chọn đáp ứng đề tài. DBeaver mô tả khả năng duyệt
schema/dữ liệu và chạy CQL. Đọc [tài liệu Cassandra của DBeaver](https://dbeaver.com/docs/dbeaver/Cassandra/).

Chưa cài/thử GUI trong lần rà soát này. Cassandra connector làm việc với ScyllaDB
trong cấu hình dự án là điều cần kiểm chứng, không ghi “tương thích 100%”.
Không dùng RAM ước lượng hoặc ảnh/result mẫu làm bằng chứng.

## Quy trình kiểm tra trên máy demo

1. Khánh xác nhận bản DBeaver Lite/trial, version, hệ điều hành, license/trial
   hợp lệ tới ngày báo cáo. Không tự mua license hay cài công cụ.
2. Chạy gate P1: Scylla healthy, CQL đọc được system.local, cổng 9042 không
   bị Cassandra cũ chiếm. Không chạy hai server cùng cổng.
3. Tạo connection bằng Cassandra connector: localhost, port 9042.
   Cấu hình local hiện chưa bật auth CSDL; đây không phải mẫu triển khai public.
4. Test Connection, đọc `SELECT release_version FROM system.local;`.
   Ghi nguyên kết quả/ảnh thật, không điền trước release/datacenter.
5. Sau khởi tạo schema/seed, duyệt fleet_tracker và xem PK/clustering/TTL.
6. Chạy từng Q1–Q14 trong hai file query; thay ngày theo seed và tham số theo
   bản ghi thật. Không chạy cả file mutation vô tình trong lúc demo.
7. Thử các thao tác GUI cần đưa vào báo cáo: query editor, schema/data browser,
   export/import một bảng fixture. Khả năng edit phụ thuộc đủ primary key;
   một lần sửa bảng không tự đồng bộ projection khác của ứng dụng.

## So sánh GUI theo bằng chứng, không theo quảng cáo

TablePlus vẫn là ứng viên đã chốt để so sánh/dự phòng. Chưa xác nhận connector
Cassandra có trên đúng phiên bản Windows của máy nhóm. Trang chủ liệt kê sản
phẩm theo nhiều hệ điều hành, không đủ chứng minh connector cần dùng:
[TablePlus](https://tableplus.com/).

| Mục đo trên cùng máy/dataset | DBeaver Lite/trial | TablePlus đúng bản OS |
| --- | --- | --- |
| Version, license, hạn trial | CẦN GHI NHẬN | CẦN GHI NHẬN |
| Cassandra/Scylla connect thực | CHƯA KIỂM CHỨNG | CHƯA KIỂM CHỨNG |
| Schema, PK/clustering, TTL | CHƯA THỬ | CHƯA THỬ |
| Q1–Q14 và kết quả tương đương | CHƯA THỬ | CHƯA THỬ |
| Import/export dữ liệu có kiểm đếm | CHƯA THỬ | CHƯA THỬ |
| Thời gian thao tác, RAM đo thực | CHƯA ĐO | CHƯA ĐO |
| Điểm mạnh/yếu nhóm trực tiếp gặp | CHƯA KẾT LUẬN | CHƯA KẾT LUẬN |

Nếu TablePlus không có connector trên OS đang dùng, ghi thiếu hỗ trợ đúng
phiên bản là một hạn chế và hỏi Khánh trước khi thay GUI so sánh/fallback.
Không tự bổ sung NoSQL Manager hoặc gán nó cho nội dung slide chưa có bằng chứng.

## Xử lý lỗi

Connection refused: kiểm tra `docker compose ps`, health/log và port mapping.
Timeout: đọc log, chờ CQL ready bằng retry script; không cam kết mốc 30–45 giây.
Driver/license thiếu: ghi version/edition và thông báo lỗi; không lách license.
Query bị từ chối: đối chiếu PK/clustering, kiểu timestamp/timeuuid và CQL;
không thêm ALLOW FILTERING để làm demo trông như chạy được.
