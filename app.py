from __future__ import annotations

import hashlib
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.data_loader import load_grade_file, timetable_preview, validate_grade_data
from src.pipeline import run_analysis

st.set_page_config(page_title="NEU Academic Integrity", page_icon="🎓", layout="wide")

PAGES = [
    "Overview Dashboard",
    "Grade Anomaly Detection",
    "Grade Adjustment",
    "Student Profiling",
    "Data Management",
]


def signature(uploaded: Any) -> str | None:
    return hashlib.sha256(uploaded.getvalue()).hexdigest() if uploaded else None


def fmt(value: Any, digits: int = 2) -> str:
    return "—" if value is None or pd.isna(value) else f"{value:,.{digits}f}"


def require_result():
    result = st.session_state.get("analysis_result")
    if result is None:
        st.info("Tải dữ liệu ở **Data Management**, kiểm tra tệp rồi nhấn **Chạy phân tích**.")
    return result


def page_data_management() -> None:
    st.title("Data Management")
    st.write("Chọn tệp điểm CSV hoặc Excel. Tệp được đọc trong phiên và không lưu vào thư mục dự án.")
    grade_file = st.file_uploader(
        "Tệp điểm (CSV / XLSX)", type=["csv", "xlsx", "xlsm"], key="grade_upload",
        help="Excel cần có sheet Du_lieu hoặc một sheet chứa các cột điểm bắt buộc.",
    )
    timetable_file = st.file_uploader("Thời khóa biểu (CSV, tùy chọn)", type=["csv"], key="timetable_upload")

    current_signature = signature(grade_file)
    previous_signature = st.session_state.get("source_signature")
    if grade_file is None:
        st.caption("Chưa chọn tệp điểm.")
    else:
        try:
            raw, source = load_grade_file(grade_file)
            errors = validate_grade_data(raw)
            if errors:
                for error in errors:
                    st.error(error)
            else:
                col_a, col_b, col_c, col_d = st.columns(4)
                col_a.metric("Số dòng", f"{len(raw):,}")
                col_b.metric("Số sinh viên", f"{raw['Mã SV'].nunique(dropna=True):,}")
                col_c.metric("Số lớp", f"{raw['Mã lớp học phần'].nunique(dropna=True):,}")
                col_d.metric("Điểm HP còn trống", f"{raw['Điểm HP (thang 10)'].isna().mean():.1%}")
                st.caption(f"Nguồn: {source}. Xem trước tối đa 10 dòng:")
                st.dataframe(raw.head(10), use_container_width=True, hide_index=True)
                if previous_signature and current_signature != previous_signature:
                    st.warning("Tệp đã thay đổi so với lần phân tích trước. Hãy chạy lại để cập nhật các trang.")
        except Exception as exc:
            st.error(f"Không đọc được tệp: {exc}")

    if timetable_file is not None:
        try:
            timetable, errors = timetable_preview(timetable_file)
            if errors:
                for error in errors:
                    st.warning(error)
            else:
                st.caption(
                    f"Thời khóa biểu: {len(timetable):,} dòng. Mã lớp/môn không nối trực tiếp với "
                    "bảng điểm; MVP chỉ xem trước tệp này."
                )
                with st.expander("Xem trước thời khóa biểu"):
                    st.dataframe(timetable.head(10), use_container_width=True, hide_index=True)
        except Exception as exc:
            st.warning(f"Không đọc được thời khóa biểu: {exc}")

    st.divider()
    run = st.button("Chạy phân tích", type="primary", disabled=grade_file is None)
    if run and grade_file is not None:
        try:
            with st.spinner("Đang phân tích trong phiên hiện tại..."):
                raw, _ = load_grade_file(grade_file)
                result = run_analysis(raw)
            st.session_state["analysis_result"] = result
            st.session_state["source_signature"] = current_signature
            st.success(
                f"Hoàn tất: {len(result['anomalies']):,} lớp, "
                f"{len(result['students']):,} sinh viên đã được xử lý."
            )
        except Exception as exc:
            st.error(f"Phân tích chưa hoàn tất: {exc}")

    st.caption(
        "Dữ liệu cuộc thi không được đưa lên dịch vụ bên ngoài. Hãy chạy dashboard cục bộ "
        "và không commit CSV/XLSX thật lên GitHub."
    )


def page_overview() -> None:
    st.title("Overview Dashboard")
    result = require_result()
    if result is None:
        return
    data, anomalies, adjusted, students = (
        result["data"], result["anomalies"], result["adjusted"], result["students"]
    )
    flagged = anomalies[anomalies["Nhãn"] != "NO_FLAG"]
    high = int((anomalies["Nhãn"] == "HIGH_INFLATION").sum())
    at_risk = int((students["Phân loại"] == "At-Risk / Beginner").sum())

    metrics = st.columns(5)
    metrics[0].metric("Lượt điểm", f"{len(data):,}")
    metrics[1].metric("Sinh viên", f"{data['Mã SV'].nunique():,}")
    metrics[2].metric("Lớp học phần", f"{anomalies['Mã lớp học phần'].nunique():,}")
    metrics[3].metric("Lớp có cờ", f"{len(flagged):,}", f"{high:,} HIGH_INFLATION")
    metrics[4].metric("At-Risk / Beginner", f"{at_risk:,}")

    left, right = st.columns(2)
    with left:
        st.subheader("Phân phối điểm trước và sau đề xuất")
        fig = go.Figure()
        fig.add_trace(go.Histogram(x=adjusted["_score"], name="Điểm gốc", marker_color="#2E8B57", opacity=0.65,
                                   xbins={"start": 0, "end": 10, "size": 0.5}))
        fig.add_trace(go.Histogram(x=adjusted["Adjusted_Score"], name="Điểm đề xuất", marker_color="#D64545", opacity=0.65,
                                   xbins={"start": 0, "end": 10, "size": 0.5}))
        fig.update_layout(barmode="overlay", xaxis_title="Điểm (thang 10)", yaxis_title="Số lượt")
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.subheader("GPA danh nghĩa và TCI")
        if not students.empty:
            fig = go.Figure()
            fig.add_trace(
                go.Histogram(
                    x=students["GPA danh nghĩa (quy đổi tuyến tính)"],
                    name="GPA danh nghĩa (quy đổi tuyến tính)",
                    opacity=0.65,
                    xbins={"start": 0, "end": 4, "size": 0.1},
                )
            )
            fig.add_trace(
                go.Histogram(
                    x=students["TCI"],
                    name="TCI sau đề xuất",
                    opacity=0.65,
                    xbins={"start": 0, "end": 4, "size": 0.1},
                )
            )
            fig.update_layout(
                barmode="overlay",
                xaxis_title="Thang 4 (quy đổi tuyến tính)",
                yaxis_title="Số sinh viên",
            )
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Phân loại năng lực")
    order = ["Advanced", "Proficient", "Intermediate", "At-Risk / Beginner"]
    counts = students["Phân loại"].value_counts().reindex(order, fill_value=0)
    st.dataframe(pd.DataFrame({"Cấp độ": counts.index, "Số sinh viên": counts.values}),
                 hide_index=True, use_container_width=True)
    st.caption(
        "TCI là chỉ số thử nghiệm: điểm thang 10 được quy đổi tuyến tính sang thang 4 "
        "và tính theo tín chỉ. Cần xác nhận bảng quy đổi chính thức trước khi kết luận."
    )


def page_anomalies() -> None:
    st.title("Grade Anomaly Detection")
    result = require_result()
    if result is None:
        return
    anomalies = result["anomalies"]
    if anomalies.empty:
        st.info("Không có lớp đủ dữ liệu để phân tích.")
        return
    labels = ["Tất cả"] + sorted(anomalies["Nhãn"].dropna().unique().tolist())
    selected = st.selectbox("Lọc theo nhãn", labels)
    shown = anomalies if selected == "Tất cả" else anomalies[anomalies["Nhãn"] == selected]
    st.write(
        "Ưu tiên so sánh lớp với lớp khác cùng môn. Nếu thiếu lớp đối chiếu, hệ thống dùng "
        "nhóm môn và hạ mức tin cậy."
    )
    display = [
        "Mã lớp học phần", "Mã môn", "Năm học", "Học kỳ", "Số sinh viên",
        "Điểm TB lớp", "Điểm TB tham chiếu", "Độ lệch chuẩn", "Tỷ lệ điểm A",
        "Anomaly Score", "Nhãn", "Độ tin cậy", "Giải thích",
    ]
    if "Tương quan với điểm môn khác (proxy)" in shown.columns:
        display.insert(-1, "Tương quan với điểm môn khác (proxy)")
    formats = {
        "Điểm TB lớp": "{:.2f}", "Điểm TB tham chiếu": "{:.2f}",
        "Độ lệch chuẩn": "{:.2f}", "Tỷ lệ điểm A": "{:.1%}",
        "Anomaly Score": "{:.2f}",
    }
    if "Tương quan với điểm môn khác (proxy)" in display:
        formats["Tương quan với điểm môn khác (proxy)"] = "{:.2f}"
    st.dataframe(shown[display].style.format(formats, na_rep="—"),
                 use_container_width=True, hide_index=True)
    st.caption(
        "Tương quan với điểm các môn khác chỉ là chỉ báo khám phá, không phải điểm nền tảng "
        "được xác nhận. Cờ bất thường yêu cầu rà soát, không phải kết luận sai phạm."
    )


def page_adjustment() -> None:
    st.title("Grade Adjustment")
    result = require_result()
    if result is None:
        return
    adjusted = result["adjusted"]
    sections = ["Tất cả"] + sorted(adjusted["Mã lớp học phần"].dropna().astype(str).unique())
    section = st.selectbox("Lớp học phần", sections)
    view = adjusted if section == "Tất cả" else adjusted[adjusted["Mã lớp học phần"].astype(str) == section]
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Điểm gốc TB", fmt(view["_score"].mean()))
    col_b.metric("Điểm đề xuất TB", fmt(view["Adjusted_Score"].mean()))
    col_c.metric("Sinh viên cần rà soát", f"{int(view['Review Required'].sum()):,}")
    display = [
        "Mã SV", "Mã môn", "Mã lớp học phần", "_score", "Mức đề xuất điều chỉnh",
        "Adjusted_Score", "Anomaly Score", "Review Required", "Ghi chú điều chỉnh",
    ]
    preview = view[display].rename(columns={"_score": "Điểm gốc"}).head(500)
    st.dataframe(
        preview.style.format(
            {"Điểm gốc": "{:.1f}", "Mức đề xuất điều chỉnh": "{:+.2f}",
             "Adjusted_Score": "{:.2f}", "Anomaly Score": "{:.2f}"}
        ),
        use_container_width=True, hide_index=True,
    )
    if len(view) > len(preview):
        st.caption(f"Đang hiển thị 500 trên {len(view):,} dòng. Chọn một lớp để xem toàn bộ lớp đó.")
    st.warning(
        "Điểm đề xuất dùng quy tắc co rút minh bạch: dịch tối đa 50% độ lệch trung bình "
        "của lớp so với nhóm đối chiếu, giới hạn ±0,75 điểm. Đây là mô phỏng để rà soát, "
        "không phải điểm chính thức hay quyết định tự động."
    )


def page_student_profiling() -> None:
    st.title("Student Profiling")
    result = require_result()
    if result is None:
        return
    students = result["students"]
    if students.empty:
        st.info("Chưa có hồ sơ sinh viên.")
        return
    levels = ["Tất cả", "Advanced", "Proficient", "Intermediate", "At-Risk / Beginner"]
    level = st.selectbox("Lọc cấp độ", levels)
    view = students if level == "Tất cả" else students[students["Phân loại"] == level]
    columns = [
        "Mã SV", "TCI", "Phân loại", "GPA danh nghĩa (quy đổi tuyến tính)",
        "Chênh lệch TCI", "Tổng tín chỉ", "Số học phần", "Số lớp cần rà soát",
    ]
    st.dataframe(
        view[columns].style.format({
            "TCI": "{:.2f}", "GPA danh nghĩa (quy đổi tuyến tính)": "{:.2f}",
            "Chênh lệch TCI": "{:+.2f}", "Tổng tín chỉ": "{:.0f}",
        }),
        use_container_width=True, hide_index=True,
    )
    ids = view["Mã SV"].astype(str).tolist()
    if not ids:
        return
    chosen = st.selectbox("Xem giải thích hồ sơ", ids)
    detail = result["adjusted"][result["adjusted"]["Mã SV"].astype(str) == chosen]
    summary = students[students["Mã SV"].astype(str) == chosen].iloc[0]
    st.subheader(f"Chẩn đoán cho {chosen}")
    kpis = st.columns(4)
    kpis[0].metric("TCI", fmt(summary["TCI"]))
    kpis[1].metric("Phân loại", summary["Phân loại"])
    kpis[2].metric("Học phần", f"{int(summary['Số học phần'])}")
    kpis[3].metric("Lớp cần rà soát", f"{int(summary['Số lớp cần rà soát'])}")
    st.write(
        "TCI là trung bình điểm đề xuất quy đổi tuyến tính và tính theo tín chỉ. "
        "Mã sinh viên chỉ được dùng trong phiên ứng dụng để tra cứu."
    )
    st.dataframe(
        detail[
            ["Mã môn", "Mã lớp học phần", "_score", "Adjusted_Score",
             "Mức đề xuất điều chỉnh", "Nhãn", "Review Required", "Giải thích"]
        ].rename(columns={"_score": "Điểm gốc"}),
        use_container_width=True, hide_index=True,
    )


with st.sidebar:
    st.title("🎓 NEU Integrity")
    st.caption("Academic Integrity & True Competency Analytics")
    page = st.radio("Điều hướng", PAGES, label_visibility="collapsed")
    st.divider()
    if st.session_state.get("analysis_result") is None:
        st.info("Chưa có kết quả phân tích.")
    else:
        st.success("Đã có kết quả trong phiên này.")

if page == "Overview Dashboard":
    page_overview()
elif page == "Grade Anomaly Detection":
    page_anomalies()
elif page == "Grade Adjustment":
    page_adjustment()
elif page == "Student Profiling":
    page_student_profiling()
else:
    page_data_management()
