from __future__ import annotations
from typing import Any
import pandas as pd


REQUIRED_GRADE_COLUMNS = [
    "Năm học",
    "Học kỳ",
    "Mã môn",
    "Nhóm môn",
    "Số TC",
    "Là đồ án/thực tập/khóa luận",
    "Mã lớp học phần",
    "Mã SV",
    "Điểm HP (thang 10)",
]

NUMERIC_COLUMNS = [
    "Số TC",
    "CC",
    "KTTX1",
    "KTTX2",
    "KTTX (TB)",
    "Thi",
    "Điểm HP (thang 10)",
]


def load_grade_file(uploaded_file: Any) -> tuple[pd.DataFrame, str]:
    """Read a user-selected CSV or Excel workbook without saving it to disk."""
    name = getattr(uploaded_file, "name", "uploaded file").lower()
    uploaded_file.seek(0)
    if name.endswith(".csv"):
        try:
            frame = pd.read_csv(uploaded_file, encoding="utf-8-sig")
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            frame = pd.read_csv(uploaded_file, encoding="cp1252")
        return frame, "CSV"

    if name.endswith((".xlsx", ".xlsm")):
        workbook = pd.ExcelFile(uploaded_file)
        preferred = next(
            (sheet for sheet in ["Du_lieu", "Du lieu", "Data"] if sheet in workbook.sheet_names),
            None,
        )
        if preferred is None:
            candidates = []
            for sheet in workbook.sheet_names:
                sample = pd.read_excel(workbook, sheet_name=sheet, nrows=2)
                if set(REQUIRED_GRADE_COLUMNS).issubset(sample.columns):
                    preferred = sheet
                    break
                candidates.append(sheet)
        if preferred is None:
            raise ValueError(
                "Không tìm thấy sheet dữ liệu điểm. Hãy dùng sheet Du_lieu "
                "hoặc sheet có đủ các cột bắt buộc."
            )
        return pd.read_excel(workbook, sheet_name=preferred), f"Excel · sheet {preferred}"

    raise ValueError("Chỉ hỗ trợ tệp .csv, .xlsx hoặc .xlsm.")


def validate_grade_data(frame: pd.DataFrame) -> list[str]:
    missing = [column for column in REQUIRED_GRADE_COLUMNS if column not in frame.columns]
    if missing:
        return ["Thiếu cột bắt buộc: " + ", ".join(missing)]
    if frame.empty:
        return ["Tệp không có dòng dữ liệu."]
    if frame["Mã SV"].isna().all():
        return ["Không tìm thấy mã sinh viên hợp lệ."]
    if frame["Điểm HP (thang 10)"].notna().sum() == 0:
        return ["Không có điểm học phần để phân tích."]
    return []


def prepare_grade_data(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    data.columns = [str(column).strip() for column in data.columns]
    for column in NUMERIC_COLUMNS:
        if column in data.columns:
            data[column] = pd.to_numeric(data[column], errors="coerce")

    for column in ["Mã SV", "Mã môn", "Mã lớp học phần", "Nhóm môn"]:
        if column in data.columns:
            data[column] = data[column].astype("string").str.strip()

    if "Là đồ án/thực tập/khóa luận" in data.columns:
        data["_is_project"] = (
            data["Là đồ án/thực tập/khóa luận"]
            .astype("string")
            .str.strip()
            .str.casefold()
            .isin(["có", "co", "yes", "true", "1"])
        )
    else:
        data["_is_project"] = False

    data["_score"] = data["Điểm HP (thang 10)"]
    data.loc[~data["_score"].between(0, 10), "_score"] = pd.NA
    data["_credits"] = data["Số TC"].where(data["Số TC"].between(1, 10), 1).fillna(1)
    return data


def timetable_preview(uploaded_file: Any) -> tuple[pd.DataFrame, list[str]]:
    uploaded_file.seek(0)
    name = getattr(uploaded_file, "name", "").lower()
    if not name.endswith(".csv"):
        return pd.DataFrame(), ["Thời khóa biểu hiện chỉ hỗ trợ CSV."]
    try:
        frame = pd.read_csv(uploaded_file, encoding="utf-8-sig")
    except UnicodeDecodeError:
        uploaded_file.seek(0)
        frame = pd.read_csv(uploaded_file, encoding="cp1252")

    required = {"Năm học", "Học kỳ", "Mã HP", "Mã LHP"}
    if not required.issubset(frame.columns):
        return frame, ["Thiếu một hoặc nhiều cột nhận diện thời khóa biểu."]
    return frame, []
