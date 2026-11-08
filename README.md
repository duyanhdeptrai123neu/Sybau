# NEU Academic Integrity & True Competency Analytics

MVP dashboard cục bộ để phát hiện lớp điểm bất thường, đề xuất hiệu chỉnh và tính TCI
minh bạch. Ứng dụng không ghi đè điểm gốc và không lưu tệp tải lên xuống đĩa.

## Chạy trên Windows

Yêu cầu Python 3.10 trở lên.

~~~powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
~~~

Mở địa chỉ local mà Streamlit in ra, vào Data Management, chọn tệp điểm CSV hoặc Excel
rồi nhấn Chạy phân tích. Excel cần có sheet Du_lieu hoặc một sheet đủ cột. Thời khóa
biểu CSV có thể tải lên để xem trước; hiện chưa ghép vào điểm vì bộ mã lớp/môn khác nhau.

## Cấu trúc

- app.py: dashboard 5 trang, tải tệp và chạy phân tích.
- src/data_loader.py: nạp, kiểm tra và chuẩn hóa CSV/XLSX.
- src/anomaly_detection.py: thống kê lớp, điểm bất thường và chỉ báo khám phá.
- src/grade_adjustment.py: điểm đề xuất có giới hạn, giữ nguyên điểm gốc.
- src/tci_calculator.py: TCI theo tín chỉ và phân loại theo ngưỡng đề bài.
- src/pipeline.py: ghép các bước phân tích.
- docs/methodology.md: công thức, giả định và giới hạn.
- docs/uml/overview.md: sơ đồ luồng, component và dữ liệu logic.
- docs/team_review.md: checklist đối chiếu MVP với nhóm.

## GitHub và dữ liệu

Tạo repository riêng tư cho mã nguồn trong giai đoạn làm việc nhóm. Không commit dữ
liệu CSV/XLSX của ban tổ chức, kết quả có mã sinh viên hay thông tin định danh. .gitignore
đã loại trừ dữ liệu trong data/ và kết quả trong outputs/. Chỉ chia sẻ repository theo
phạm vi ban tổ chức cho phép; không đưa dữ liệu thật lên dashboard đám mây/dịch vụ ngoài.

Gợi ý nhánh: main giữ bản chạy được; mỗi thành viên dùng nhánh feature/..., rồi mở Pull
Request để thành viên khác xem thay đổi trước khi nhập.

## Giới hạn MVP

Tệp điểm chỉ bao phủ một khoa, không có điểm đầu vào hay danh sách môn nền tảng. TCI
hiện dùng phép đổi tuyến tính thang 10 sang thang 4 vì chưa có bảng quy đổi chính thức.
Anomaly Score là điểm sàng lọc theo quy tắc, không phải xác suất sai phạm. Xem
docs/methodology.md trước khi diễn giải kết quả.
