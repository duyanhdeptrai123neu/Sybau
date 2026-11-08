# Phương pháp MVP và giới hạn diễn giải

## Phạm vi

MVP nhận CSV hoặc Excel có sheet Du_lieu, phát hiện lớp nghi vấn, tạo điểm đề xuất để
rà soát và tính TCI theo tín chỉ. Điểm gốc luôn được giữ nguyên. Tệp thời khóa biểu chỉ
xem trước: mã lớp/môn trong tệp này không nối trực tiếp được với bảng điểm.

## Phát hiện bất thường

Mỗi lớp thường được so sánh trước với các lớp khác cùng Mã môn. Khi chưa có ít nhất
hai lớp đối chiếu phù hợp, hệ thống dùng Nhóm môn và ghi rõ đây là tham chiếu yếu hơn.
Điểm trung bình, tỷ lệ điểm từ 8,5 và độ lệch chuẩn được tính trên điểm học phần không
trống; đồ án/thực tập/khóa luận được tách khỏi lớp thường.

Độ lệch trung bình dùng z-score robust dựa trên trung vị và MAD của lớp đối chiếu. Score
0–1 lấy tín hiệu mạnh nhất trong độ lệch trung bình, tỷ lệ điểm từ 8,5 trên 60% và độ
phân tán thấp. Nhãn
gồm HIGH_INFLATION, UNUSUALLY_STEEP, SUSPICIOUS_DISTRIBUTION hoặc NO_FLAG.
Lớp ít sinh viên hay ít lớp đối chiếu được hạ mức tin cậy. Score chưa được hiệu chuẩn
thành xác suất.

## Điểm đề xuất

Với lớp có Anomaly Score s, điểm trung bình lớp m và trung bình đối chiếu b:

    delta = clip(0.5 × s × clip(m − b, −1.5, 1.5), −0.75, 0.75)
    Adjusted_Score = clip(Điểm gốc − delta, 0, 10)

Cả lớp có điểm cao bất thường và thấp bất thường đều được đề xuất dịch về nhóm đối
chiếu; thứ hạng nội bộ lớp được giữ nguyên trước khi chạm giới hạn 0–10. Lớp chỉ bất
thường về độ phân tán có thể được gắn cờ nhưng không tự ý dời điểm trung bình.

## TCI

Do bộ dữ liệu không kèm quy tắc đổi thang 10 sang GPA 4 chính thức, MVP dùng phép đổi
tuyến tính: điểm 4 = Adjusted_Score × 0.4, sau đó tính trung bình theo tín chỉ. Ngưỡng
Advanced (3,60), Proficient (3,20), Intermediate (2,50) và At-Risk / Beginner (<2,50)
lấy theo đề bài. Cần thay phép quy đổi tuyến tính bằng bảng quy đổi được xác nhận trước
khi dùng kết quả như xếp loại chính thức.

## Giới hạn dữ liệu

- Tệp chỉ đại diện cho một khoa, không có ngành, giảng viên, hình thức thi, điểm đầu vào
  hoặc điểm các môn nền tảng được định danh.
- Tương quan với điểm trung bình các môn khác chỉ là chỉ báo khám phá, không được coi là
  tương quan với năng lực nền tảng.
- Điểm 0 có thể gồm vắng thi/bỏ học; ô trống có nghĩa là thiếu dữ liệu.
- 2019–2020 thiếu nhiều điểm quá trình; một số lớp 2025–2026 chưa có điểm cuối kỳ.
- Gắn cờ không chứng minh sai phạm. Mọi hiệu chỉnh chỉ là đề xuất cần con người rà soát.
- Chỉ phân tích tổng hợp; không tìm cách định danh sinh viên/giảng viên, không tải dữ
  liệu cuộc thi lên dịch vụ ngoài, và không đưa dữ liệu thật vào repository.
