from __future__ import annotations

import hashlib
import html
from io import BytesIO
from math import ceil
from typing import Any

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import streamlit as st
from openpyxl.styles import Font, PatternFill
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

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


def build_analysis_report(result: dict[str, pd.DataFrame]) -> bytes:
    """Package the current analysis outputs into a portable Excel report."""
    data, anomalies, adjusted, students = (
        result["data"], result["anomalies"], result["adjusted"], result["students"]
    )
    summary = pd.DataFrame(
        [
            ("Lượt điểm đầu vào", len(data)),
            ("Sinh viên", data["Mã SV"].nunique()),
            ("Lớp học phần", anomalies["Mã lớp học phần"].nunique()),
            ("Lớp có nhãn cần xem xét", int(anomalies["Nhãn"].isin(
                ["HIGH_INFLATION", "UNUSUALLY_STEEP", "SUSPICIOUS_DISTRIBUTION"]
            ).sum())),
            ("Điểm gốc trung bình", adjusted["_score"].mean()),
            ("Điểm đề xuất trung bình", adjusted["Adjusted_Score"].mean()),
            ("Sinh viên cần rà soát", int(adjusted["Review Required"].sum())),
            ("TCI trung bình", students["TCI"].mean() if not students.empty else float("nan")),
        ],
        columns=["Chỉ số", "Giá trị"],
    )
    method = pd.DataFrame(
        {
            "Nội dung": [
                "Điểm gốc được giữ nguyên; Adjusted_Score là đề xuất phân tích.",
                "Chỉ đề xuất giảm điểm trên 8,0 tại lớp HIGH_INFLATION; mức giảm tối đa 1,5 điểm.",
                "Điểm dưới hoặc bằng 8,0 và các lớp nhãn khác được giữ nguyên; điểm đề xuất không tăng điểm.",
                "Anomaly Score và cờ rà soát là tín hiệu tham khảo, không phải kết luận vi phạm hay quyết định học vụ.",
                "TCI được tính từ điểm đề xuất và tín chỉ theo cấu hình prototype.",
            ]
        }
    )
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Tổng quan", index=False)
        anomalies.to_excel(writer, sheet_name="Phát hiện bất thường", index=False)
        adjusted.rename(columns={"_score": "Điểm gốc"}).to_excel(
            writer, sheet_name="Điểm đề xuất", index=False
        )
        students.to_excel(writer, sheet_name="Hồ sơ sinh viên", index=False)
        method.to_excel(writer, sheet_name="Diễn giải", index=False)
        for worksheet in writer.book.worksheets:
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions
            for cell in worksheet[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(fill_type="solid", fgColor="24476B")
            for column_cells in worksheet.columns:
                width = min(max(max(len(str(cell.value or "")) for cell in column_cells) + 2, 12), 48)
                worksheet.column_dimensions[column_cells[0].column_letter].width = width
    return output.getvalue()


def report_download(result: dict[str, pd.DataFrame], key: str) -> None:
    st.download_button(
        "Tải báo cáo phân tích (.xlsx)",
        data=build_analysis_report(result),
        file_name="NEU_Academic_Integrity_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key=key,
    )


def build_pdf_report(result: dict[str, pd.DataFrame]) -> bytes:
    """Build a compact PDF with a section for each dashboard page."""
    data, anomalies, adjusted, students = (
        result["data"], result["anomalies"], result["adjusted"], result["students"]
    )
    regular_font = "Helvetica"
    bold_font = "Helvetica-Bold"
    windows_fonts = ("C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/arialbd.ttf")
    if all(__import__("os").path.exists(font_path) for font_path in windows_fonts):
        if "NEUArial" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("NEUArial", windows_fonts[0]))
            pdfmetrics.registerFont(TTFont("NEUArial-Bold", windows_fonts[1]))
        regular_font, bold_font = "NEUArial", "NEUArial-Bold"

    buffer = BytesIO()
    page_size = landscape(A4)
    doc = SimpleDocTemplate(
        buffer, pagesize=page_size, rightMargin=15 * mm, leftMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=17 * mm, title="NEU Academic Integrity - Analysis Report",
        author="NEU Academic Integrity Dashboard",
    )
    base_styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "NEUTitle", parent=base_styles["Title"], fontName=bold_font,
        fontSize=20, leading=25, textColor=colors.HexColor("#173B5E"), alignment=TA_CENTER,
        spaceAfter=8 * mm,
    )
    heading_style = ParagraphStyle(
        "NEUHeading", parent=base_styles["Heading2"], fontName=bold_font,
        fontSize=14, leading=18, textColor=colors.HexColor("#173B5E"), spaceBefore=2 * mm,
        spaceAfter=3 * mm,
    )
    body_style = ParagraphStyle(
        "NEUBody", parent=base_styles["BodyText"], fontName=regular_font,
        fontSize=8.5, leading=12, spaceAfter=2 * mm,
    )
    cell_style = ParagraphStyle(
        "NEUCell", parent=body_style, fontSize=7, leading=9, spaceAfter=0,
    )
    header_style = ParagraphStyle(
        "NEUHeader", parent=cell_style, fontName=bold_font, textColor=colors.white,
    )

    def on_page(canvas, current_doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D5E0EA"))
        canvas.line(15 * mm, 12 * mm, page_size[0] - 15 * mm, 12 * mm)
        canvas.setFont(regular_font, 8)
        canvas.setFillColor(colors.HexColor("#64748B"))
        canvas.drawString(15 * mm, 7 * mm, "NEU Academic Integrity | Báo cáo phân tích tham khảo")
        canvas.drawRightString(page_size[0] - 15 * mm, 7 * mm, f"Trang {current_doc.page}")
        canvas.restoreState()

    def table_for(rows, widths=None, header=True):
        cooked = []
        for row_index, row in enumerate(rows):
            cooked.append([
                Paragraph(html.escape(str(value if value is not None else "")),
                          header_style if header and row_index == 0 else cell_style)
                for value in row
            ])
        table = Table(cooked, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#24476B")) if header else ("BACKGROUND", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D5E0EA")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1 if header else 0), (-1, -1), [colors.white, colors.HexColor("#F3F7FA")]),
        ]))
        return table

    def records_table(frame, columns, headers, max_rows=35, widths=None):
        available = [column for column in columns if column in frame.columns]
        shown = frame[available].head(max_rows)
        rows = [headers[:len(available)]]
        for record in shown.itertuples(index=False, name=None):
            values = []
            for value in record:
                if pd.isna(value):
                    values.append("-")
                elif isinstance(value, (float, np.floating)):
                    values.append(f"{value:.2f}")
                else:
                    text_value = str(value)
                    values.append(text_value if len(text_value) <= 45 else text_value[:42] + "...")
            rows.append(values)
        if not len(shown):
            return Paragraph("Không có dòng dữ liệu để hiển thị.", body_style)
        return table_for(rows, widths=widths)

    def histogram_chart(before, after):
        bins = np.arange(0, 11, 1)
        before_hist = np.histogram(before.dropna(), bins=bins)[0].tolist()
        after_hist = np.histogram(after.dropna(), bins=bins)[0].tolist()
        chart = VerticalBarChart()
        chart.x, chart.y, chart.width, chart.height = 48, 28, 670, 100
        chart.data = [before_hist, after_hist]
        chart.categoryAxis.categoryNames = [f"{n}-{n + 1}" for n in range(10)]
        chart.categoryAxis.labels.fontName = regular_font
        chart.categoryAxis.labels.fontSize = 7
        chart.valueAxis.labels.fontName = regular_font
        chart.valueAxis.labels.fontSize = 7
        chart.valueAxis.valueMin = 0
        maximum = max(before_hist + after_hist + [1])
        chart.valueAxis.valueMax = max(1, ceil(maximum * 1.1))
        chart.valueAxis.valueStep = max(1, ceil(maximum / 5))
        chart.bars[0].fillColor = colors.HexColor("#2E8B57")
        chart.bars[1].fillColor = colors.HexColor("#D64545")
        chart.barWidth = 18
        chart.groupSpacing = 7
        chart.barSpacing = 1
        drawing = Drawing(740, 145)
        drawing.add(chart)
        return drawing

    score_mean = adjusted["_score"].mean() if not adjusted.empty else np.nan
    adjusted_mean = adjusted["Adjusted_Score"].mean() if not adjusted.empty else np.nan
    flagged = anomalies[anomalies["Nhãn"].isin(
        ["HIGH_INFLATION", "UNUSUALLY_STEEP", "SUSPICIOUS_DISTRIBUTION"]
    )] if "Nhãn" in anomalies else anomalies
    level_order = ["Advanced", "Proficient", "Intermediate", "At-Risk / Beginner"]
    level_counts = students["Phân loại"].value_counts().reindex(level_order, fill_value=0) if not students.empty else pd.Series(dtype=int)

    story = [
        Paragraph("NEU ACADEMIC INTEGRITY", title_style),
        Paragraph("Báo cáo tổng hợp kết quả từ năm trang dashboard", heading_style),
        Paragraph(
            "Báo cáo được tạo từ dữ liệu đã tải lên trong phiên hiện tại. Điểm đề xuất và TCI là kết quả phân tích thử nghiệm, không thay thế điểm chính thức.",
            body_style,
        ),
        Paragraph("1. Overview Dashboard", heading_style),
        table_for([
            ["Chỉ số", "Kết quả", "Chỉ số", "Kết quả"],
            ["Lượt điểm", f"{len(data):,}", "Sinh viên", f"{data['Mã SV'].nunique():,}"],
            ["Lớp học phần", f"{anomalies['Mã lớp học phần'].nunique():,}", "Lớp nghi vấn", f"{len(flagged):,}"],
            ["Điểm gốc TB", fmt(score_mean), "Điểm đề xuất TB", fmt(adjusted_mean)],
            ["GPA danh nghĩa TB", fmt(students["GPA danh nghĩa (quy đổi NEU, thử nghiệm)"].mean() if not students.empty else np.nan), "TCI TB", fmt(students["TCI"].mean() if not students.empty else np.nan)],
            ["Sinh viên cần rà soát", f"{int(adjusted['Review Required'].sum()):,}", "Thang TCI", "NEU thang 4 (thử nghiệm)"],
        ], widths=[130, 170, 150, 180]),
        Spacer(1, 3 * mm),
        Paragraph("Phân phối điểm gốc và điểm sau đề xuất siết", body_style),
        Paragraph('<font color="#2E8B57"><b>■</b></font> Điểm gốc &nbsp;&nbsp; <font color="#D64545"><b>■</b></font> Điểm sau đề xuất siết', body_style),
        histogram_chart(adjusted["_score"], adjusted["Adjusted_Score"]),
        table_for([["Cấp độ năng lực", "Số sinh viên"]] + [[str(level), f"{int(level_counts.get(level, 0)):,}"] for level in level_order], widths=[260, 160]),
        PageBreak(),
        Paragraph("2. Grade Anomaly Detection", heading_style),
        Paragraph(f"Có {len(flagged):,} lớp được gắn nhãn cần xem xét trong tổng số {len(anomalies):,} lớp đã phân tích. Sắp xếp theo Anomaly Score giảm dần.", body_style),
        records_table(
            flagged.sort_values("Anomaly Score", ascending=False, na_position="last"),
            ["Mã lớp học phần", "Mã môn", "Năm học", "Học kỳ", "Điểm TB lớp", "Điểm TB tham chiếu", "Tỷ lệ điểm A", "Anomaly Score", "Nhãn"],
            ["Lớp HP", "Môn", "Năm", "Kỳ", "TB lớp", "TB tham chiếu", "Tỷ lệ A", "Score", "Nhãn"],
        ),
        Spacer(1, 3 * mm),
        Paragraph("Cờ bất thường là yêu cầu rà soát, không phải kết luận sai phạm. Nhóm đối chiếu được chọn theo môn, kỳ và năm khi dữ liệu cho phép.", body_style),
        PageBreak(),
        Paragraph("3. Grade Adjustment", heading_style),
        Paragraph(
            f"Điểm gốc trung bình: {fmt(score_mean)}; điểm đề xuất trung bình: {fmt(adjusted_mean)}. Cơ chế hiện tại chỉ giảm điểm trên 8,0 trong lớp HIGH_INFLATION; các điểm khác không tăng.",
            body_style,
        ),
        records_table(
            adjusted.sort_values("Mức đề xuất điều chỉnh", ascending=False),
            ["Mã SV", "Mã môn", "Mã lớp học phần", "_score", "Mức đề xuất điều chỉnh", "Adjusted_Score", "Nhãn"],
            ["Mã SV", "Môn", "Lớp HP", "Điểm gốc", "Mức giảm", "Điểm đề xuất", "Nhãn"],
            widths=[75, 65, 100, 65, 75, 75, 100],
        ),
        Spacer(1, 3 * mm),
        Paragraph("Công thức: excess = clip(điểm TB lớp − điểm TB tham chiếu, 0, 2); áp lực lớp = clip(0,75 × Anomaly Score × excess, 0, 1,5); mức giảm cá nhân = áp lực lớp × clip((điểm gốc − 8) / 2, 0, 1). Đây là đề xuất thử nghiệm, không tự động cập nhật điểm chính thức.", body_style),
        PageBreak(),
        Paragraph("4. Student Profiling", heading_style),
        table_for([["Cấp độ", "Số sinh viên"]] + [[str(level), f"{int(level_counts.get(level, 0)):,}"] for level in level_order], widths=[260, 160]),
        Spacer(1, 4 * mm),
        Paragraph("Danh sách sinh viên xếp theo TCI giảm dần; báo cáo PDF hiển thị tối đa 35 hồ sơ. Tệp Excel kèm theo dashboard giữ bảng dữ liệu đầy đủ.", body_style),
        records_table(
            students.sort_values("TCI", ascending=False),
            ["Mã SV", "TCI", "Phân loại", "GPA danh nghĩa (quy đổi NEU, thử nghiệm)", "Số học phần", "Số lớp cần rà soát"],
            ["Mã SV", "TCI", "Phân loại", "GPA danh nghĩa", "Học phần", "Lớp rà soát"],
            widths=[100, 60, 120, 145, 85, 100],
        ),
        PageBreak(),
        Paragraph("5. Data Management", heading_style),
        Paragraph("Tổng quan dữ liệu được phân tích trong phiên", body_style),
        table_for([
            ["Trường dữ liệu", "Giá trị"],
            ["Lượt điểm sau chuẩn hóa", f"{len(data):,}"],
            ["Sinh viên", f"{data['Mã SV'].nunique():,}"],
            ["Mã môn", f"{data['Mã môn'].nunique():,}"],
            ["Lớp học phần", f"{data['Mã lớp học phần'].nunique():,}"],
            ["Điểm học phần bị trống", f"{int(data['_score'].isna().sum()):,}"],
        ], widths=[260, 180]),
        Spacer(1, 4 * mm),
        Paragraph("Bảng thời khóa biểu hiện chỉ được xem trước và chưa nối với bảng điểm. Để tải toàn bộ dòng kết quả và các cột chi tiết, dùng nút tải Excel trên dashboard.", body_style),
        Spacer(1, 4 * mm),
        Paragraph("Lưu ý sử dụng", heading_style),
        Paragraph("Phân tích dựa trên cấu trúc và chất lượng của tệp đầu vào. Các lớp thiếu đối chiếu có thể được gắn NOT_ASSESSED. Anomaly Score chưa được hiệu chuẩn thành xác suất; TCI và điểm đề xuất cần được hội đồng chuyên môn rà soát trước khi sử dụng cho quyết định học vụ.", body_style),
    ]
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    return buffer.getvalue()


def pdf_report_download(result: dict[str, pd.DataFrame]) -> None:
    st.download_button(
        "Tải báo cáo PDF tổng hợp 5 trang",
        data=build_pdf_report(result),
        file_name="NEU_Academic_Integrity_Report.pdf",
        mime="application/pdf",
        key="download_full_pdf_report",
        use_container_width=True,
    )


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
    existing_result = st.session_state.get("analysis_result")
    if existing_result is not None:
        report_download(existing_result, "download_report_data_management")


def page_overview() -> None:
    st.title("Overview Dashboard")
    result = require_result()
    if result is None:
        return
    data, anomalies, adjusted, students = (
        result["data"], result["anomalies"], result["adjusted"], result["students"]
    )
    review_labels = ["HIGH_INFLATION", "UNUSUALLY_STEEP", "SUSPICIOUS_DISTRIBUTION"]
    flagged = anomalies[anomalies["Nhãn"].isin(review_labels)]
    high = int((anomalies["Nhãn"] == "HIGH_INFLATION").sum())
    not_assessed = int((anomalies["Nhãn"] == "NOT_ASSESSED").sum())
    no_comparator = int(
        anomalies["Nhóm đối chiếu"].eq("Không đủ lớp đối chiếu theo môn/kỳ/năm").sum()
    )
    at_risk = int((students["Phân loại"] == "At-Risk / Beginner").sum())

    metrics = st.columns(5)
    metrics[0].metric("Lượt điểm", f"{len(data):,}")
    metrics[1].metric("Sinh viên", f"{data['Mã SV'].nunique():,}")
    metrics[2].metric("Lớp học phần", f"{anomalies['Mã lớp học phần'].nunique():,}")
    metrics[3].metric("Lớp nghi vấn", f"{len(flagged):,}", f"{high:,} HIGH_INFLATION")
    metrics[4].metric("At-Risk / Beginner", f"{at_risk:,}")
    if not_assessed:
        st.caption(
            f"Chưa đánh giá: {not_assessed:,} lớp "
            f"({no_comparator:,} lớp thiếu đối chiếu; các lớp đồ án/thực tập cũng được loại riêng)."
        )

    st.subheader("Phân phối điểm trước và sau đề xuất siết")
    chart_left, chart_right = st.columns(2)
    bin_edges = np.arange(0, 10.5, 0.5)
    max_bin_count = max(
        int(np.histogram(values.dropna(), bins=bin_edges)[0].max())
        for values in (adjusted["_score"], adjusted["Adjusted_Score"])
    )
    for container, title, series, color, chart_key in [
        (chart_left, "Trước điều chỉnh · Điểm gốc", adjusted["_score"], "#2E8B57", "before"),
        (chart_right, "Sau siết · Điểm đề xuất", adjusted["Adjusted_Score"], "#D64545", "after"),
    ]:
        with container:
            st.markdown(f"**{title}**")
            st.metric("Điểm trung bình", fmt(series.mean()))
            st.caption(f"{series.notna().sum():,} lượt điểm")
            fig = go.Figure(
                go.Histogram(
                    x=series,
                    marker_color=color,
                    xbins={"start": 0, "end": 10, "size": 0.5},
                    hovertemplate="Khoảng điểm: %{x}<br>Số lượt: %{y}<extra></extra>",
                )
            )
            fig.update_layout(
                xaxis={"title": "Điểm (thang 10)", "range": [0, 10], "dtick": 1},
                yaxis={"title": "Số lượt điểm", "range": [0, max(1, max_bin_count * 1.1)]},
                showlegend=False,
                margin={"t": 20, "b": 35, "l": 10, "r": 10},
            )
            st.plotly_chart(fig, use_container_width=True, key=f"grade_distribution_{chart_key}")
    st.caption(
        "Hai biểu đồ dùng cùng thang trục. Chỉ điểm trên 8,0 trong lớp HIGH_INFLATION được đề xuất giảm; "
        "các điểm còn lại giữ nguyên. Đây là đề xuất phân tích, chưa phải điểm chính thức."
    )
    report_download(result, "download_report_overview")

    with st.container():
        st.subheader("GPA danh nghĩa và TCI")
        if not students.empty:
            fig = go.Figure()
            fig.add_trace(
                go.Histogram(
                    x=students["GPA danh nghĩa (quy đổi NEU, thử nghiệm)"],
                    name="GPA danh nghĩa",
                    marker_color="#2E8B57",
                    opacity=0.65,
                    xbins={"start": 0, "end": 4, "size": 0.1},
                )
            )
            fig.add_trace(
                go.Histogram(
                    x=students["TCI"],
                    name="TCI sau đề xuất",
                    marker_color="#D64545",
                    opacity=0.65,
                    xbins={"start": 0, "end": 4, "size": 0.1},
                )
            )
            fig.update_layout(
                barmode="overlay",
                xaxis_title="Thang 4 (quy đổi NEU, thử nghiệm)",
                yaxis_title="Số sinh viên",
                legend={"orientation": "h", "yanchor": "top", "y": -0.25,
                        "xanchor": "center", "x": 0.5},
                margin={"b": 75},
            )
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Phân loại năng lực")
    order = ["Advanced", "Proficient", "Intermediate", "At-Risk / Beginner"]
    counts = students["Phân loại"].value_counts().reindex(order, fill_value=0)
    st.dataframe(pd.DataFrame({"Cấp độ": counts.index, "Số sinh viên": counts.values}),
                 hide_index=True, use_container_width=True)
    st.caption(
        "TCI thử nghiệm: điểm được làm tròn một chữ số, quy đổi theo bảng điểm NEU "
        "(QĐ 712/2025) rồi tính theo tín chỉ. Cần xác nhận quy định áp dụng cho từng khóa; "
        "TCI và cờ rà soát không phải kết luận học vụ hay sai phạm."
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
        "Ưu tiên cùng môn, cùng năm học và học kỳ. Nếu thiếu, hệ thống lần lượt mở rộng "
        "nhóm đối chiếu. NOT_ASSESSED nghĩa là không đủ đối chiếu hoặc lớp được loại khỏi "
        "phân tích; trạng thái này không đồng nghĩa với NO_FLAG."
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
        "được xác nhận. Cờ bất thường yêu cầu rà soát, không phải kết luận sai phạm hay căn cứ "
        "tự động cho học bổng/cảnh báo học vụ."
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
        "Quy tắc siết thử nghiệm: chỉ lớp HIGH_INFLATION bị xem xét; điểm trên 8,0 bị giảm "
        "tăng dần theo điểm và Anomaly Score, tối đa 1,5 điểm. Điểm từ 8,0 trở xuống và lớp "
        "thuộc nhãn khác giữ nguyên. Đây là đề xuất cần rà soát, không phải điểm chính thức."
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
        "Mã SV", "TCI", "Phân loại", "GPA danh nghĩa (quy đổi NEU, thử nghiệm)",
        "Chênh lệch TCI", "Tổng tín chỉ", "Số học phần", "Số học phần chưa đánh giá",
        "Số lớp cần rà soát",
    ]
    st.dataframe(
        view[columns].style.format({
            "TCI": "{:.2f}", "GPA danh nghĩa (quy đổi NEU, thử nghiệm)": "{:.2f}",
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
        "TCI là chỉ số thử nghiệm tính từ điểm đề xuất theo tín chỉ; học phần chưa đánh giá "
        "được giữ điểm gốc. Cờ rà soát chỉ là tín hiệu cần xem xét, không phải kết luận "
        "gian lận hay căn cứ tự động để xét học bổng/cảnh báo. Mã SV chỉ được dùng trong phiên."
    )
    st.caption(
        f"Học phần chưa đánh giá của sinh viên này: "
        f"{int(summary['Số học phần chưa đánh giá']):,}."
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
        pdf_report_download(st.session_state["analysis_result"])

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
