# NEU Academic Integrity & True Competency Analytics

Prototype dashboard phân tích bất thường điểm học phần và năng lực sinh viên. Ứng dụng chạy cục bộ, giữ nguyên điểm gốc và tạo điểm đề xuất để con người rà soát.

## Chức năng

Dashboard gồm 5 trang:

1. **Overview Dashboard** — chỉ số tổng quan, phân phối điểm gốc và điểm đề xuất, GPA danh nghĩa và TCI.
2. **Grade Anomaly Detection** — so sánh lớp theo môn, ưu tiên cùng năm học và học kỳ; hiển thị nhãn, Anomaly Score và lý do.
3. **Grade Adjustment** — bảng điểm gốc, mức giảm đề xuất và điểm sau siết.
4. **Student Profiling** — TCI, phân loại năng lực và thông tin giải thích theo sinh viên.
5. **Data Management** — tải CSV/XLSX, kiểm tra dữ liệu và chạy phân tích.

Sau khi phân tích, thanh bên có nút tải **PDF tổng hợp cả 5 trang**. PDF gồm các chỉ số và bảng tóm tắt; mỗi bảng chi tiết hiển thị tối đa 35 dòng. Nút tải Excel ở Overview và Data Management xuất các bảng dữ liệu chi tiết đầy đủ.

## Hướng dẫn tải và chạy trên Windows bằng VS Code

Hướng dẫn này giả định máy đã cài **Git for Windows**, **Python 3.10 trở lên** và **Visual Studio Code**. Các lệnh chính bên dưới dành cho **PowerShell**. Hãy chạy từng lệnh một: sao chép một dòng, dán vào terminal, nhấn **Enter**, rồi chờ lệnh hoàn tất trước khi chạy dòng tiếp theo.

### Bước 1: Kiểm tra môi trường

Mở PowerShell từ Start Menu hoặc mở VS Code rồi chọn **Terminal → New Terminal**. Kiểm tra Git và Python đã sẵn sàng:

```powershell
git --version
python --version
```

Mỗi lệnh cần in ra số phiên bản. Nếu terminal báo không nhận diện lệnh, hãy kiểm tra môi trường cài đặt/PATH trước khi tiếp tục.

### Bước 2: Mở PowerShell trong VS Code và tạo thư mục

1. Mở VS Code.
2. Trên thanh menu, chọn **Terminal → New Terminal**. Một khung terminal sẽ xuất hiện ở phía dưới cửa sổ.
3. Nhìn đầu dòng trong terminal:
   - Nếu có dạng `PS C:\Users\...>`, đây là PowerShell và bạn có thể chạy các lệnh bên dưới.
   - Nếu chỉ có dạng `C:\Users\...>` mà không có `PS`, đây là Command Prompt (CMD). Bấm mũi tên nhỏ cạnh nút **+** ở góc phải khung Terminal, rồi chọn **PowerShell**. Mở terminal mới nếu cần.
4. Sao chép dòng lệnh thứ nhất bên dưới, dán vào terminal và nhấn **Enter**. Lệnh tạo thư mục `Projects` bên trong thư mục tài khoản Windows. `$HOME` là đường dẫn thư mục tài khoản của bạn; `-Force` giúp lệnh chạy được cả khi `Projects` đã tồn tại.
5. Khi terminal trả lại dấu nhắc lệnh, chạy dòng thứ hai. Dòng này chuyển terminal vào `Projects`.

```powershell
New-Item -ItemType Directory -Force -Path "$HOME\Projects" | Out-Null
Set-Location "$HOME\Projects"
```

Bạn có thể thay `$HOME\Projects` bằng nơi muốn lưu project, chẳng hạn thư mục Documents.

Sau dòng thứ hai, đường dẫn ở đầu dòng lệnh sẽ kết thúc bằng `\Projects`. Hãy giữ terminal này mở để tiếp tục Bước 3. Nếu muốn dùng CMD thay cho PowerShell, hai lệnh tương đương là:

```cmd
if not exist "%USERPROFILE%\Projects" mkdir "%USERPROFILE%\Projects"
cd /d "%USERPROFILE%\Projects"
```

Chạy các lệnh CMD trong terminal CMD; không dán cú pháp PowerShell vào CMD.
Sau khi tạo thư mục bằng CMD, chuyển terminal sang PowerShell để làm các bước tiếp theo theo hướng dẫn: bấm mũi tên cạnh nút **+** và chọn **PowerShell**, rồi chạy `Set-Location "$HOME\Projects"`.

### Bước 3: Clone repository từ GitHub

Xác nhận đầu dòng terminal đang ở đường dẫn kết thúc bằng `\Projects`, sau đó chạy lệnh này và nhấn **Enter**:

```powershell
git clone https://github.com/duyanhdeptrai123neu/Sybau.git
```

Git sẽ tự tạo thư mục `Sybau` và tải mã nguồn vào đó. Repository public nên không cần đăng nhập GitHub để clone.
Chờ Git tải xong và dấu nhắc lệnh xuất hiện lại rồi mới sang bước tiếp theo. Nếu báo `git is not recognized`, kiểm tra Git đã được cài và mở terminal mới.
Nếu báo thư mục `Sybau` đã tồn tại, không clone chồng lên thư mục đó; chuyển vào thư mục hiện có ở Bước 4.

### Bước 4: Mở đúng thư mục project trong VS Code

Trong PowerShell, chuyển vào thư mục vừa tải:

```powershell
Set-Location "$HOME\Projects\Sybau"
```

Thử mở project bằng lệnh:

```powershell
code .
```

Nếu lệnh `code` không khả dụng, mở VS Code → **File → Open Folder...** → chọn `$HOME\Projects\Sybau` → **Select Folder**. Trong Explorer của VS Code, thư mục gốc đúng cần thấy `app.py`, `requirements.txt`, `src` và `docs`.

Mở terminal ngay trong VS Code bằng **Terminal → New Terminal**. Terminal cần đang ở thư mục `Sybau`. Kiểm tra:

```powershell
Get-Location
```

Đường dẫn in ra phải kết thúc bằng `Projects\Sybau` (hoặc đường dẫn khác mà bạn đã chọn ở Bước 2).

### Bước 5: Tạo môi trường ảo cho project

Trong terminal VS Code đang ở thư mục `Sybau`, chạy lệnh sau rồi nhấn **Enter**:

```powershell
python -m venv .venv
```

Lệnh này tạo folder `.venv` bên trong `Sybau`. Lần đầu có thể mất một lúc và thường không in thông báo khi thành công; chờ tới khi dấu nhắc lệnh xuất hiện lại. Sau đó chạy từng lệnh cài thư viện dưới đây, mỗi lệnh nhấn **Enter** và chờ hoàn tất:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Lần đầu có thể mất vài phút. Không bắt buộc phải activate `.venv`; dùng trực tiếp `\.venv\Scripts\python.exe` giúp tránh cài thư viện nhầm sang Python khác và không cần đổi Execution Policy của PowerShell.

### Bước 6: Chọn `.venv` làm Python interpreter trong VS Code

1. Nhấn **Ctrl+Shift+P**.
2. Gõ **Python: Select Interpreter** rồi chọn lệnh đó.
3. Chọn interpreter có đường dẫn kết thúc bằng `Sybau\.venv\Scripts\python.exe`.
4. Nếu chưa thấy, chọn **Enter interpreter path... → Find...** rồi tìm đến file `.venv\Scripts\python.exe` bên trong thư mục `Sybau`.

Việc này giúp VS Code, Pylance và terminal nhận cùng môi trường Python của project.

### Bước 7: Chạy dashboard

Đảm bảo terminal vẫn đang ở thư mục `Sybau` và `.venv` đã cài xong thư viện. Chạy lệnh sau rồi nhấn **Enter**:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Terminal sẽ in địa chỉ local, thường là `http://localhost:8501`, và trình duyệt có thể tự mở. Nếu không tự mở, giữ terminal đang chạy rồi sao chép địa chỉ được in ra vào trình duyệt. Muốn tắt dashboard, quay lại terminal và nhấn **Ctrl+C**.

### Bước 8: Tải dữ liệu và chạy phân tích

1. Trên dashboard, mở **Data Management**.
2. Nhấn **Browse files** và chọn tệp điểm CSV/XLSX do Ban tổ chức cung cấp.
3. Xem trước dữ liệu và đọc thông báo kiểm tra. Excel cần có sheet `Du_lieu` hoặc một sheet chứa đủ cột bắt buộc.
4. Nhấn **Chạy phân tích**.
5. Xem kết quả trong năm trang dashboard. Dùng nút ở thanh bên để tải PDF tổng hợp; dùng nút Excel ở Overview Dashboard hoặc Data Management để tải dữ liệu chi tiết.

Thời khóa biểu CSV hiện chỉ được xem trước, chưa ghép trực tiếp vào bảng điểm. Tệp dữ liệu người dùng chọn không được commit vào repository. Vì repository này public, tuyệt đối không đưa dữ liệu Ban tổ chức, mã sinh viên, điểm cá nhân, token hoặc thông tin đăng nhập lên GitHub.

### Chạy dashboard trong những lần sau

Mở VS Code, chọn **File → Open Recent** để mở `Sybau`, mở terminal mới và chạy:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Nếu mở terminal ở một thư mục khác, chuyển về project trước. Ví dụ:

```powershell
Set-Location "$HOME\Projects\Sybau"
```

Không chạy `src\pipeline.py` để mở giao diện; file đó chỉ là một phần xử lý dữ liệu. Dùng lệnh Streamlit ở trên để khởi động dashboard.

### Lỗi thường gặp

- **`git` hoặc `python` không được nhận diện:** xác nhận đã cài công cụ đó, đóng/mở lại VS Code để nạp PATH mới, rồi kiểm tra phiên bản lần nữa.
- **`No module named streamlit`, `pandas` hoặc thư viện khác:** kiểm tra terminal đang ở thư mục project và chạy lại `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.
- **`.\.venv\Scripts\python.exe` không tìm thấy:** bạn đang ở sai thư mục hoặc chưa tạo `.venv`. Dùng `Get-Location`, chuyển về folder `Sybau`, rồi làm lại Bước 5.
- **PowerShell chặn activate:** hướng dẫn này không cần activate; chạy trực tiếp `.venv\Scripts\python.exe`.
- **Streamlit hỏi email:** có thể để trống rồi nhấn Enter.
- **Trình duyệt không mở hoặc không tải:** kiểm tra terminal Streamlit còn chạy không và dùng đúng URL mà terminal đã in ra.
- **Tệp dữ liệu không hợp lệ:** kiểm tra lại sheet Excel và các cột bắt buộc; xem hướng dẫn trong `data/README.md`.

## Phương pháp hiệu chỉnh hiện tại

- Lớp mang nhãn `HIGH_INFLATION` được xem xét siết điểm.
- Chỉ điểm trên 8,0 mới có thể bị giảm; mức giảm tăng theo điểm, độ lệch của lớp so với nhóm đối chiếu và Anomaly Score. Mức giảm tối đa hiện đặt là 1,5 điểm.
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

## Giới hạn MVP

Repository public để người chấm xem mã nguồn. Dữ liệu thử nghiệm hiện đại diện cho một khoa, chưa có điểm đầu vào hoặc danh mục môn nền tảng. Thời khóa biểu chưa được ghép với bảng điểm do mã lớp/môn khác nhau. Lớp không đủ nhóm đối chiếu mang nhãn `NOT_ASSESSED`; trạng thái này khác `NO_FLAG`.

Anomaly Score là điểm sàng lọc theo quy tắc, chưa được hiệu chuẩn thành xác suất. Điểm đề xuất và TCI cần được hội đồng chuyên môn rà soát trước khi cân nhắc dùng cho quyết định học vụ.

## Đóng góp nhóm

Giữ `main` ở trạng thái có thể chạy. Thành viên có thể tạo nhánh `feature/...`, commit thay đổi và mở Pull Request để nhóm rà soát trước khi nhập vào `main`.
