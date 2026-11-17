# NEU Academic Integrity & True Competency Analytics

Prototype dashboard phân tích bất thường điểm học phần và năng lực sinh viên. Ứng dụng chạy cục bộ, giữ nguyên điểm gốc và tạo điểm đề xuất để con người rà soát.

## Chức năng

Dashboard có 5 trang:

1. **Overview Dashboard** — chỉ số tổng quan, phân phối điểm gốc và điểm đề xuất, GPA danh nghĩa và TCI.
2. **Grade Anomaly Detection** — so sánh lớp theo môn, ưu tiên cùng năm học và học kỳ; hiển thị nhãn, Anomaly Score và lý do.
3. **Grade Adjustment** — bảng điểm gốc, mức giảm đề xuất và điểm sau siết.
4. **Student Profiling** — TCI, phân loại năng lực và thông tin giải thích theo sinh viên.
5. **Data Management** — tải CSV/XLSX, kiểm tra dữ liệu và chạy phân tích.

Sau khi phân tích, thanh bên có nút tải **PDF tổng hợp cả 5 trang**. Báo cáo PDF trình bày các chỉ số và bảng tóm tắt; mỗi bảng chi tiết hiển thị tối đa 35 dòng. Nút tải Excel ở Overview và Data Management chứa các bảng dữ liệu chi tiết đầy đủ.

## Cách chạy trên Windows

Cài Python 3.10 trở lên, mở PowerShell tại thư mục dự án và chạy:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Mở địa chỉ local mà Streamlit in ra. Vào **Data Management**, chọn tệp CSV hoặc Excel, kiểm tra dữ liệu rồi nhấn **Chạy phân tích**. Excel cần có sheet `Du_lieu` hoặc một sheet chứa đủ các cột bắt buộc. Thời khóa biểu CSV hiện chỉ xem trước, chưa ghép vào bảng điểm.

## Phương pháp hiệu chỉnh hiện tại

- Lớp mang nhãn `HIGH_INFLATION` được xem xét siết điểm.
- Chỉ điểm trên 8,0 mới có thể bị giảm; điểm giảm tăng theo mức điểm, độ lệch của lớp so với nhóm đối chiếu và Anomaly Score. Mức giảm tối đa hiện đặt là 1,5 điểm.
- Điểm từ 8,0 trở xuống và các lớp có nhãn khác được giữ nguyên. Điểm gốc không bị ghi đè.
- TCI được tính lại từ điểm đề xuất theo tín chỉ và bảng quy đổi NEU đang dùng làm tham chiếu thử nghiệm.

Công thức, giả định và giới hạn được mô tả tại [docs/methodology.md](docs/methodology.md). Điểm đề xuất, Anomaly Score và TCI là kết quả phân tích thử nghiệm; cờ bất thường không phải kết luận sai phạm hay quyết định học vụ.

## Cấu trúc chính

- `app.py` — giao diện Streamlit, biểu đồ và xuất báo cáo PDF/Excel.
- `src/data_loader.py` — nạp, kiểm tra và chuẩn hóa CSV/XLSX.
- `src/anomaly_detection.py` — so sánh thống kê giữa các lớp và gắn nhãn bất thường.
- `src/grade_adjustment.py` — tính điểm đề xuất theo quy tắc siết hiện tại.
- `src/tci_calculator.py` — tính TCI và phân loại sinh viên.
- `src/pipeline.py` — kết nối các bước phân tích.
- `docs/methodology.md` — công thức, giả định và giới hạn.
- `docs/uml/overview.md` — sơ đồ luồng xử lý và thành phần.

## Dữ liệu và repository public

Repository này được public để người chấm có thể xem mã nguồn. Không commit dữ liệu của Ban tổ chức, tệp có mã sinh viên/điểm cá nhân, kết quả phân tích có thông tin định danh, thông tin đăng nhập hoặc token. Hãy kiểm tra nội dung staged trước mỗi lần commit. Dữ liệu trong `data/` và kết quả trong `outputs/` được `.gitignore` loại trừ.

Thời khóa biểu hiện chưa liên kết trực tiếp với bảng điểm vì mã môn/lớp chưa được ghép nối. Bộ dữ liệu thử nghiệm đại diện cho một khoa và chưa có điểm đầu vào hoặc danh mục môn nền tảng. Lớp không đủ dữ liệu đối chiếu được đánh dấu `NOT_ASSESSED`; trạng thái này khác `NO_FLAG`.

## Đóng góp nhóm

Giữ `main` ở trạng thái có thể chạy. Thành viên có thể tạo nhánh `feature/...`, commit thay đổi và mở Pull Request để nhóm rà soát trước khi nhập vào `main`.
