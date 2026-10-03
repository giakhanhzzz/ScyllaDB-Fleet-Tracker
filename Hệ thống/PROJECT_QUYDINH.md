# Quy định đồ án NoSQL — Đề tài 14

> Nguồn chính thức do Phạm Gia Khánh cung cấp ngày 14/09/2026. Khi kế hoạch hoặc ghi chú khác file này, ưu tiên file này và yêu cầu mới nhất của giảng viên.

## 1. Thông tin đề tài

- Đề tài 14: Tìm hiểu công cụ quản trị CSDL **ScyllaDB** cho hệ thống **“Quản lý dữ liệu theo dõi vị trí phương tiện vận tải và lịch sử hành trình của đội xe”**; xây dựng ứng dụng minh họa.
- Loại CSDL: Column Family Database, tương thích CQL/Cassandra.
- Thành viên: Phạm Gia Khánh, Trà Ngọc Nguyên Vũ, Lê Hữu Luân.
- Điểm đánh giá theo từng thành viên. Mọi đề tài phải có lý thuyết về Tool, thiết kế CSDL và ứng dụng demo.

## 2. Thang điểm chính thức — 10 điểm

| Mục | Nội dung | Điểm |
|---|---|---:|
| 1 | Tìm hiểu lý thuyết và cài đặt Tool theo đề tài | 0,5 |
| 2 | Trình bày chi tiết các chức năng của Tool | 0,5 |
| 3 | So sánh điểm mạnh/yếu của Tool với một GUI Tool khác | 0,5 |
| 4 | Nêu ScyllaDB phù hợp với loại ứng dụng Database nào | 0,5 |
| 5a | Tạo Database | 0,5 |
| 5b | Insert dữ liệu đầy đủ cho ứng dụng | 0,5 |
| 5c | Dữ liệu đáp ứng truy vấn cơ bản | 0,5 |
| 5d | Dữ liệu đáp ứng truy vấn nâng cao theo ứng dụng | 0,5 |
| 6 | Import/export; backup và restore dữ liệu | 0,5 |
| 7a | Chạy truy vấn cơ bản trên GUI Tool | 0,5 |
| 7b | Chạy truy vấn nâng cao trên GUI Tool | 0,5 |
| 8 | Phần mềm ứng dụng kết nối CSDL | 0,5 |
| 9a | Demo quản trị người dùng | 0,5 |
| 9b | Demo thao tác CSDL: thêm/xóa/sửa/backup… | 0,5 |
| 9c | Demo chức năng nghiệp vụ theo đề tài | 0,5 |
| 9d | Demo chức năng hỗ trợ | 0,5 |
| 10a | Báo cáo đầy đủ, đúng chính tả/định dạng, không sao chép | 0,5 |
| 10b | Báo cáo tự tin, lưu loát, trả lời được giảng viên | 0,5 |
| 10c | Nộp đúng hạn đủ Word, PowerPoint và source code | 0,5 |
| 10d | Phân công rõ, hoàn thành cá nhân, tích hợp tốt, có trách nhiệm | 0,5 |

> Nếu đề tài không tìm hiểu GUI Tool mới ngoài MongoDB, Cassandra, Neo4j, Redis thì thiết kế Database và ứng dụng phải tăng chức năng để thay 2 điểm mục 1–4. Đề tài ScyllaDB vẫn chuẩn bị đầy đủ mục 1–4 và GUI quản trị phù hợp.

## 3. Yêu cầu trình bày và nộp

- Báo cáo 50–60 trang, gồm lý thuyết, thiết kế CSDL, ứng dụng demo, tài liệu tham khảo…
- Times New Roman, cỡ 13, giãn dòng 1,5.
- Báo cáo xen kẽ các buổi học hoặc đầy đủ vào buổi cuối; sau đó nộp quyển báo cáo.
- Nộp đủ Word, PowerPoint và source code; tài liệu chỉ tham khảo, không sao chép.
- Làm việc nghiêm túc, kỷ luật; phân công rõ và tích hợp hệ thống hoàn chỉnh.
- Văn bản giảng viên: TP.HCM, 08/08/2026 — Nguyễn Thị Định.

## 4. Ràng buộc kỹ thuật nhóm đã chốt

- ScyllaDB chạy Docker; Python `cassandra-driver`; FastAPI; web đơn giản + Leaflet.
- Chạy local bằng Docker Compose; có schema, seed và GPS simulator gửi mỗi vài giây.
- Dữ liệu: users, drivers, vehicles, trips, location events, alerts và geofence.
- Role: Admin, Dispatcher, Viewer; quyền cưỡng chế tại backend.
- GPS event: latitude, longitude, speed, heading, timestamp; lưu time-series theo bucket và có thể dùng TTL.
- Alert: vượt tốc độ, ra khỏi bounding-box geofence, mất GPS quá N phút.
- Dữ liệu GPS mẫu tối thiểu vài trăm; kế hoạch đặt tiêu chí ít nhất 3.000 event.

## 5. Chức năng và truy vấn bắt buộc

- CRUD xe, tài xế, chuyến đi; quản trị user và phân quyền.
- Theo dõi latest location trên bản đồ; lịch sử hành trình; xem/xử lý alert.
- Cơ bản: xe theo trạng thái, latest location của xe, trip trong ngày.
- Nâng cao: lịch sử xe trong `[t1,t2]`; xe di chuyển N phút gần nhất; tổng km/số chuyến theo tài xế/tháng.
- Import/export CSV hoặc JSON; backup/restore bằng snapshot hoặc `COPY`.
- Chạy query trên GUI Tool và ứng dụng; có simulator, thống kê và tìm kiếm/lọc.

