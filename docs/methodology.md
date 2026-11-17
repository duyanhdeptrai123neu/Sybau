# Phương pháp MVP và giới hạn diễn giải

## Phạm vi

MVP nhận CSV hoặc Excel có sheet Du_lieu, phát hiện lớp nghi vấn, tạo điểm đề xuất để
rà soát và tính TCI theo tín chỉ. Điểm gốc luôn được giữ nguyên. Tệp thời khóa biểu chỉ
xem trước: mã lớp/môn trong tệp này không nối trực tiếp được với bảng điểm.

## Phát hiện bất thường

Các lớp đối chiếu được chọn theo thứ tự:

1. Cùng Mã môn, cùng Năm học và cùng Học kỳ.
2. Nếu chưa có ít nhất hai lớp đối chiếu đủ sĩ số, mở rộng sang cùng Mã môn ở các
   năm học/học kỳ khác.
3. Nếu vẫn thiếu, dùng cùng Nhóm môn trong cùng năm học/học kỳ.
4. Cuối cùng, nếu cần, mở rộng nhóm môn sang các kỳ/năm khác và đánh dấu đây là tham
   chiếu yếu hơn.

Lớp đang đánh giá luôn bị loại khỏi nhóm tham chiếu. Nếu không có ít nhất hai lớp đối
chiếu phù hợp sau các bước trên, hệ thống không gán score bất thường và ghi rõ không
đủ dữ liệu so sánh. Điểm trung bình, tỷ lệ điểm từ 8,5 và độ lệch chuẩn được tính trên
điểm học phần không trống; đồ án/thực tập/khóa luận được tách khỏi lớp thường.
Các lớp đồ án/thực tập/khóa luận hoặc lớp thiếu nhóm đối chiếu mang nhãn
`NOT_ASSESSED`, không phải `NO_FLAG`, và không được tự động hiệu chỉnh.

Độ lệch trung bình dùng z-score robust dựa trên trung vị và MAD của lớp đối chiếu. Score
0–1 hiện lấy tín hiệu mạnh nhất trong độ lệch trung bình, tỷ lệ điểm từ 8,5 trên 60% và
độ phân tán thấp. Nhãn gồm HIGH_INFLATION, UNUSUALLY_STEEP, SUSPICIOUS_DISTRIBUTION
hoặc NO_FLAG. Lớp ít sinh viên hay ít lớp đối chiếu được hạ mức tin cậy. Score chưa
được hiệu chuẩn thành xác suất. MVP giữ cách tổng hợp theo tín hiệu mạnh nhất; công thức
score trọng số đề xuất trong buổi họp chưa được áp dụng vì các thành phần và cách xử lý
chỉ số thiếu chưa được xác định/kiểm chứng đầy đủ.

## Điểm đề xuất

Với lớp có nhãn HIGH_INFLATION, Anomaly Score s, điểm trung bình lớp m và trung bình đối chiếu b:

    excess = clip(m − b, 0, 2)
    class_pressure = clip(0.75 × s × excess, 0, 1.5)
    high_grade_share = clip((Điểm gốc − 8) / 2, 0, 1)
    reduction = class_pressure × high_grade_share
    Adjusted_Score = clip(Điểm gốc − reduction, 0, 10)

Đề xuất hiện chỉ siết điểm ở lớp bị gắn nhãn HIGH_INFLATION. Điểm dưới hoặc bằng 8,0
không đổi; điểm cao hơn 8,0 bị giảm tăng dần theo mức điểm,
tối đa bằng class_pressure. Không có trường hợp nào được tăng điểm. Lớp UNUSUALLY_STEEP
hoặc SUSPICIOUS_DISTRIBUTION chỉ được gắn cờ rà soát, không tự động hiệu chỉnh. Mức giảm
tối đa 1,5 điểm là cấu hình thử nghiệm cần được nhóm chuyên môn rà soát trước khi cân
nhắc áp dụng thực tế.

## TCI

TCI dùng bảng quy đổi điểm thang 10 sang thang 4 được công bố trong Quyết định
712/QĐ-ĐHKTQD năm 2025 làm thang tham chiếu thử nghiệm. Theo [hướng dẫn của NEU], điểm
học phần được làm tròn đến một chữ số thập phân trước khi quy đổi:

| Điểm thang 10 sau làm tròn | Điểm thang 4 |
|---:|---:|
| 9,0–10,0 | 4,0 |
| 8,5–8,9 | 4,0 |
| 8,0–8,4 | 3,5 |
| 7,0–7,9 | 3,0 |
| 6,5–6,9 | 2,5 |
| 5,5–6,4 | 2,0 |
| 5,0–5,4 | 1,5 |
| 4,5–4,9 | 1,0 |
| Dưới 4,5 | 0,0 |

[hướng dẫn của NEU]: https://fit.neu.edu.vn/post/how-to-calculate-course-grades-and-cumulative-gpa-at-neu

GPA danh nghĩa và TCI đều là trung bình có trọng số tín chỉ; GPA danh nghĩa dùng điểm
gốc, TCI dùng điểm đề xuất. Không áp dụng thêm hệ số giảm trọng số theo Anomaly Score
trong TCI chính để tránh giảm ảnh hưởng một học phần hai lần. Ngưỡng Advanced (3,60),
Proficient (3,20), Intermediate (2,50) và At-Risk / Beginner (<2,50) lấy theo đề bài.

Bảng trên là quy tắc tham chiếu của prototype, không mặc định áp dụng cho mọi khóa và
mọi năm dữ liệu. Cần xác nhận quy định có hiệu lực cho từng nhóm sinh viên trước khi
diễn giải như GPA chính thức. Khoảng cách GPA danh nghĩa–TCI chỉ là tín hiệu phân tích,
không chứng minh sinh viên gian lận hay cố ý chọn lớp dễ.

## Giới hạn dữ liệu

- Tệp chỉ đại diện cho một khoa, không có ngành, giảng viên, hình thức thi, điểm đầu vào
  hoặc điểm các môn nền tảng được định danh.
- Tương quan với điểm trung bình các môn khác chỉ là chỉ báo khám phá, không được coi là
  tương quan với năng lực nền tảng; chỉ dùng khi có danh mục môn nền tảng được xác nhận.
- Điểm 0 có thể gồm vắng thi/bỏ học; ô trống có nghĩa là thiếu dữ liệu.
- 2019–2020 thiếu nhiều điểm quá trình; một số lớp 2025–2026 chưa có điểm cuối kỳ.
- Gắn cờ không chứng minh sai phạm. Mọi hiệu chỉnh chỉ là đề xuất cần con người rà soát.
- Chỉ phân tích tổng hợp; không tìm cách định danh sinh viên/giảng viên, không tải dữ
  liệu cuộc thi lên dịch vụ ngoài, và không đưa dữ liệu thật vào repository.
