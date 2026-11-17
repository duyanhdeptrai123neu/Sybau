# Buổi đối chiếu MVP với nhóm

Mục tiêu buổi review là thống nhất giả định và phân chia chỉnh sửa, không sửa trực tiếp
trên bản đang demo. Mỗi người ghi quyết định, lý do và người phụ trách tiếp theo.

## Năm phần để rà soát

1. **Dữ liệu và phạm vi:** xác nhận các cột bắt buộc; dữ liệu chỉ đại diện một khoa;
   lớp đồ án được tách; thời khóa biểu không nối trực tiếp; ô trống khác điểm 0.
2. **Phát hiện bất thường:** nhóm có đồng ý so sánh cùng môn qua các năm không; cần tối
   thiểu bao nhiêu lớp đối chiếu và sĩ số; ngưỡng điểm A trên 60% có phù hợp không;
   score hiện là mức sàng lọc hay nhóm muốn hiệu chuẩn lại.
3. **Hiệu chỉnh:** thảo luận công thức co rút và giới hạn ±0,75; xem việc kéo điểm lớp
   cao/thấp về mức đối chiếu có công bằng không; thống nhất luôn giữ nguyên điểm gốc.
4. **TCI:** xác nhận trọng số tín chỉ và bốn ngưỡng; đối chiếu bảng quy đổi NEU áp dụng
   cho từng khóa/năm dữ liệu; không gọi TCI thử nghiệm là GPA chính thức nếu chưa được
   xác nhận.
5. **Dashboard và bảo mật:** phân biệt NO_FLAG với NOT_ASSESSED; đảm bảo người dùng hiểu
   cờ không kết luận sai phạm và không tự động quyết định học bổng/cảnh báo; chỉ chạy cục
   bộ với dữ liệu thật; không commit hoặc tải bộ dữ liệu lên dịch vụ ngoài.

## Chia vai review nhanh

- Thành viên 1: kiểm tra tên cột, dữ liệu thiếu và giới hạn dữ liệu.
- Thành viên 2: phản biện baseline và ngưỡng anomaly.
- Thành viên 3: phản biện công thức điều chỉnh, tác động lên điểm cá nhân.
- Thành viên 4: phản biện TCI, cách đổi thang và giải thích.
- Thành viên 5: chạy demo cục bộ, rà luồng trang và README.

## Sau buổi review

Ghi mỗi góp ý thành một issue nhỏ; ưu tiên sửa lỗi làm sai kết quả hoặc gây hiểu nhầm,
sau đó mới chỉnh giao diện. Mỗi người làm trên nhánh riêng, tạo Pull Request về main và
ghi cách xác nhận thay đổi. Không đưa dữ liệu thật vào issue, ảnh chụp, log hoặc Pull Request.
