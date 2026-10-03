# Kịch bản demo — mục tiêu nghiệm thu, chưa phải kết quả đã đạt

## Trạng thái

API/script đang có mã nguồn và test logic; chưa chạy Scylla thật.
UI React là prototype mô phỏng, không dùng để chứng minh CRUD, role hay backup.
Frontend tĩnh `frontend/` đã gọi API nhưng vẫn cần chạy cùng Scylla thật trước
khi dùng làm bằng chứng trình diễn.
Không tuyên bố đạt 10/10 từ skeleton hoặc đổi role bằng nút trong UI.

## Gate theo thứ tự

1. **Khánh — P1**: docker info/config; Scylla healthy; nodetool UN; CQL metadata;
   driver và GUI đúng edition/license. Chụp ảnh/log thật.
2. **Khánh — CSDL/seed**: nạp schema 15 bảng/3.200 GPS, chạy lại seed cùng ngày
   đối chiếu count; đọc Q1–Q14 trong GUI; giải thích partition/clustering và TTL.
3. **Vũ — backend**: khởi tạo bằng init_demo.ps1, đăng nhập ba tài khoản; Viewer
   đọc được, POST ingest bị 403, request không token bị 401. Tắt CSDL thì API
   không trả mock/PASS; kiểm tra dữ liệu đọc lại sau ingest.
4. **Vũ — nghiệp vụ còn phải hoàn thiện**: CRUD user/xe/tài xế đã viết nhưng
   phải chạy với Scylla thật; tạo/start/end/cancel chuyến,
   liên kết GPS vào trip hiện hành; tính km từ GPS hợp lệ; overspeed/geofence/
   mất tín hiệu, ACK/RESOLVE và chống lặp sau retry/restart.
5. **Luân — frontend còn phải hoàn thiện**: frontend tĩnh phục vụ từ FastAPI,
   login thật, Leaflet latest/history, bộ lọc, thao tác theo quyền. Không dùng
   thay đổi React state để giả thao tác CSDL.
6. **Khánh/Luân — dữ liệu hỗ trợ**: simulator gửi 3–5 giây, lịch sử nhiều bucket,
   xe di chuyển trong N phút, báo cáo tài xế theo tháng. Km fixture và km được
   tính khi kết thúc chuyến phải được phân biệt rõ.
7. **Khánh — COPY backup/restore**: dừng writer/API, export 15 bảng, ghi count và
   mẫu dữ liệu; sửa fixture có kiểm soát rồi RESTORE bản đúng. Đối chiếu count,
   mẫu dòng và TTL; không gọi COPY là snapshot vật lý. Dữ liệu gốc luôn được
   backup an toàn trước thay thế.
8. **Cả nhóm — báo cáo**: GUI chính/so sánh có bằng chứng; ưu nhược Scylla và
   mô hình query-first; báo cáo 50–60 trang theo PROJECT_QUYDINH.md; Word,
   PowerPoint/source và phân công đủ. Mỗi thành viên giải thích phần mình.

Chỉ chuyển bước phụ thuộc khi gate trước đã có bằng chứng. Prototype không
thay thế phần ứng dụng nối CSDL thật. Khi gate thất bại, ghi log vào
TEST_EVIDENCE.md/Nhap.md và xử lý đúng phạm vi; không tick hoàn thành.

## Thao tác smoke hiện có sau gate P1

- Chạy `./scripts/init_demo.ps1`, mở `http://localhost:8000/docs`.
- Login khanh_admin/vu_dispatcher/luan_viewer với Password123@ (demo local).
- Với Admin: tạo một Viewer mới, đổi role/khóa; tài khoản bị khóa không thể
  dùng token cũ. Đây là bước cần chạy thực tế, chưa được tick bằng test fake.
- Với Dispatcher: thêm tài xế, thêm xe gán tài xế, sửa trạng thái xe và thử
  khóa tài xế còn được gán (mong đợi 409). Xe mới dùng geofence TP.HCM mặc
  định; chỉnh vùng theo nghiệp vụ chưa có trong UI.
- Tạo chuyến PLANNED bằng xe và tài xế đã gán; xem lại chuyến ở ngày UTC hiện
  tại. Start/end/cancel vẫn là phần phải xây tiếp, chưa có màn hình demo.
- Authorize Bearer token; GET xe/latest/history/chuyến theo ngày seed.
- Bật simulator bằng `docker compose --profile demo up -d simulator`.
- Trong GUI, đọc lại location/latest/alerts sau request thật.
- Thử POST ingest bằng Viewer: mong đợi 403, ghi response thực tế.
- Mọi ngày giờ dùng UTC rõ timezone; truy vấn mẫu mặc định 28/09/2026.
