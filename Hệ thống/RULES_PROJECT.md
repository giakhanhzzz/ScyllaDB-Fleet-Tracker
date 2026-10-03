# Rules — Xử lý đồ án ScyllaDB

> Áp dụng cho dự án tại `C:\Users\artis\Downloads\Project_NoSql`.

## 1. Nguồn chuẩn

1. Yêu cầu mới nhất của Phạm Gia Khánh.
2. `PROJECT_QUYDINH.md`: đề tài, rubric, yêu cầu giảng viên.
3. Kế hoạch được Khánh chấp thuận.
4. `TAKENOTE_Baihoc_NOSQL.md`: kiến thức học phần đã chốt.
5. `Nhap.md`: lịch sử, giả định và vấn đề chưa chốt.

Không tạo file bộ nhớ trùng chức năng; không đổi tên/di chuyển bốn file trong `Hệ thống` nếu Khánh chưa yêu cầu.

## 2. Bộ nhớ

- Tự ghi `Nhap.md` khi có giả định, sai sót, mâu thuẫn, quyết định tạm, rủi ro hoặc câu hỏi chưa rõ.
- Chỉ cập nhật Takenote với kiến thức NoSQL đã logic hóa/kiểm chứng; không đưa yêu cầu riêng của đồ án vào Takenote.
- Chỉ cập nhật `PROJECT_QUYDINH.md` khi Khánh cung cấp quy định/rubric hoặc chốt ràng buộc.
- Sau việc quan trọng, báo file đã cập nhật; nếu có quyết định mới chưa được phép chốt thì hỏi Khánh.
- Không nghiên cứu lại kiến thức ổn định trong Takenote; chỉ kiểm tra phần phụ thuộc phiên bản, bảo mật hoặc mâu thuẫn.

## 3. Phạm vi đã chốt

- ScyllaDB, query-first, denormalization có chủ đích; không join/`ALLOW FILTERING` để vá schema.
- Docker Compose local; FastAPI + `cassandra-driver`; query prepared/parameterized.
- Frontend HTML/CSS/JavaScript + Leaflet; không thêm framework nặng khi chưa cần.
- Một Scylla node mặc định để demo ổn định; nhiều node là mở rộng nếu đủ tài nguyên.
- Không thêm Kafka, Redis, microservice, Kubernetes, cloud hoặc ML nếu rubric không yêu cầu.

## 4. Thiết kế và triển khai

- Chốt access patterns trước table; mỗi table ghi rõ query phục vụ.
- Time-series bucket theo xe + ngày/giờ, clustering theo thời gian; tránh partition vô hạn.
- TTL chỉ cho location/activity cũ; user, vehicle, driver, trip, alert không tự hết hạn.
- Một service/use case sở hữu write và cập nhật đủ bảng denormalized.
- RBAC bắt buộc ở backend; ẩn nút frontend không phải bảo mật.
- Restore/xóa dữ liệu: Admin, xác nhận và script riêng; không chạy mặc định.
- Seed idempotent hoặc có reset rõ; GPS event có ID chống trùng và UTC.
- Mỗi phase có bằng chứng chạy được trước phase phụ thuộc.

## 5. Giao tiếp và dừng

- Tiếng Việt, mở đầu bằng kết luận; giải thích kỹ phần kiến trúc/rubric.
- Nêu trade-off và khuyến nghị khi có lựa chọn; không tự đổi công nghệ đã chốt.
- Không viết code khi Khánh chỉ yêu cầu kế hoạch.
- Task hoàn tất khi đầu ra được kiểm tra, rubric có bằng chứng và bộ nhớ liên quan đã cập nhật/báo lại.

