# Checklist bằng chứng đồ án

Tài liệu này là checklist theo thang điểm giảng viên. Mỗi mục được đánh dấu sau khi
đã chạy được trên máy demo và lưu ảnh/log/query tương ứng trong thư mục
`docs/screenshots/`.

## 10 nhóm tiêu chí

- [ ] 1. Lý thuyết và cài đặt ScyllaDB cùng GUI quản trị theo yêu cầu.
- [ ] 2. Trình bày đầy đủ các chức năng của GUI Tool được chọn.
- [ ] 3. So sánh GUI Tool chính với một GUI Tool khác, nêu điểm mạnh/yếu.
- [ ] 4. Giải thích nhóm ứng dụng ScyllaDB phù hợp nhất.
- [ ] 5. Xây dựng Database: tạo schema, seed dữ liệu, truy vấn cơ bản và nâng cao.
- [ ] 6. Import/export dữ liệu và backup/restore CSDL.
- [ ] 7. Chạy truy vấn cơ bản và nâng cao trực tiếp trên GUI Tool.
- [ ] 8. Kết nối Database với phần mềm ứng dụng.
- [ ] 9. Demo đủ quản trị người dùng, thao tác CSDL, nghiệp vụ đội xe và chức năng hỗ trợ.
- [ ] 10. Báo cáo, thuyết trình, nộp đủ Word/PowerPoint/source và bằng chứng phân công.

## Quyết định P0 đã chốt

- GUI chính: DBeaver Lite/trial; TablePlus là công cụ so sánh/dự phòng.
- GPS retention: 90 ngày.
- Seed: 10 xe.
- GPS simulator: gửi mỗi 3–5 giây.
- Nhóm: Phạm Gia Khánh, Trà Ngọc Nguyên Vũ, Lê Hữu Luân.

## Quy ước ảnh bằng chứng

- Đặt ảnh theo dạng `p<phase>_<so-muc>_<mo-ta>.png`.
- Không đánh dấu hoàn thành nếu chưa có thao tác chạy lại được hoặc log/query đối chiếu.
- Ảnh GUI phải thể hiện rõ connection, CQL/query, kết quả hoặc trạng thái thao tác.

## Trạng thái P0

- [x] Phạm vi, access patterns, role matrix, luồng demo và phân công đã được nhóm xác nhận.
- [x] Tạo thư mục ảnh bằng chứng `docs/screenshots/`.
- [ ] Kiểm tra DBeaver Lite/trial và license trên máy demo (hiện chưa phát hiện DBeaver/TablePlus đã cài).
