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

    # Shrink only the section-level shift, and cap it so a flag is not treated as proof.
    shift = (result["Điểm TB lớp"] - result["Điểm TB tham chiếu"]).clip(-1.5, 1.5)
    location_score = result["Anomaly Score"].where(
        result["Nhãn"].isin(["HIGH_INFLATION", "UNUSUALLY_STEEP"]), 0.0
    )
    result["Mức đề xuất điều chỉnh"] = (
        0.5 * location_score * shift
    ).clip(-0.75, 0.75)
    result["Adjusted_Score"] = (
        result["_score"] - result["Mức đề xuất điều chỉnh"]
    ).clip(0, 10)
    result["Review Required"] = (
        (result["Nhãn"] != "NO_FLAG")
        | (result["Mức đề xuất điều chỉnh"].abs() >= 0.25)
    )
    result["Ghi chú điều chỉnh"] = np.where(
        result["Review Required"],
        "Ước tính minh họa; cần hội đồng chuyên môn rà soát",
        "Không có điều chỉnh theo ngưỡng MVP",
    )
    return result
