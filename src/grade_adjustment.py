from __future__ import annotations

import numpy as np
import pandas as pd


def adjust_grades(data: pd.DataFrame, anomalies: pd.DataFrame) -> pd.DataFrame:
    """Create a transparent, capped review proposal; never overwrite source grades."""
    anomaly_cols = [
        "Mã lớp học phần", "Anomaly Score", "Nhãn", "Điểm TB tham chiếu",
        "Điểm TB lớp", "Giải thích",
    ]
    if anomalies.empty:
        lookup = pd.DataFrame(columns=anomaly_cols)
    else:
        lookup = anomalies[anomaly_cols].drop_duplicates("Mã lớp học phần")
    lookup["Mã lớp học phần"] = lookup["Mã lớp học phần"].astype("string")

    result = data.loc[data["_score"].notna() & data["Mã SV"].notna()].copy()
    result["Mã lớp học phần"] = result["Mã lớp học phần"].astype("string")
    result = result.merge(lookup, on="Mã lớp học phần", how="left")
    result["Anomaly Score"] = result["Anomaly Score"].fillna(0.0)
    result["Nhãn"] = result["Nhãn"].fillna("NO_FLAG")
    result["Điểm TB tham chiếu"] = result["Điểm TB tham chiếu"].fillna(result["_score"].mean())
    result["Điểm TB lớp"] = result["Điểm TB lớp"].fillna(result["_score"].mean())
    not_assessed = result["Nhãn"].eq("NOT_ASSESSED")
    result.loc[not_assessed, "Điểm TB tham chiếu"] = np.nan

    # Tighten only grades above 8.0 in high-inflation sections. Lower grades are
    # unchanged, and a flag remains a review signal rather than evidence of misconduct.
    excess = (
        result["Điểm TB lớp"] - result["Điểm TB tham chiếu"]
    ).clip(lower=0.0, upper=2.0).fillna(0.0)
    inflation_score = result["Anomaly Score"].where(result["Nhãn"].eq("HIGH_INFLATION"), 0.0)
    class_pressure = (0.75 * inflation_score * excess).clip(0.0, 1.5)
    high_grade_share = ((result["_score"] - 8.0) / 2.0).clip(0.0, 1.0)
    result["Mức đề xuất điều chỉnh"] = class_pressure * high_grade_share
    result["Adjusted_Score"] = (
        result["_score"] - result["Mức đề xuất điều chỉnh"]
    ).clip(0, 10)
    result["Review Required"] = (
        result["Nhãn"].isin(
            ["HIGH_INFLATION", "UNUSUALLY_STEEP", "SUSPICIOUS_DISTRIBUTION"]
        )
        | (result["Mức đề xuất điều chỉnh"].abs() >= 0.25)
    )
    result["Ghi chú điều chỉnh"] = np.select(
        [not_assessed, result["Review Required"]],
        [
            "Chưa đánh giá được; lớp bị loại khỏi so sánh hoặc thiếu nhóm đối chiếu, giữ nguyên điểm gốc",
            "Ước tính minh họa; cần hội đồng chuyên môn rà soát",
        ],
        default="Không có điều chỉnh theo ngưỡng MVP",
    )
    return result
