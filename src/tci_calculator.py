from __future__ import annotations

import numpy as np
import pandas as pd


TCI_THRESHOLDS = [
    (3.60, "Advanced"),
    (3.20, "Proficient"),
    (2.50, "Intermediate"),
    (-np.inf, "At-Risk / Beginner"),
]


def calculate_tci(adjusted: pd.DataFrame) -> pd.DataFrame:
    """Credit-weighted prototype index using a stated linear 10-to-4 conversion."""
    if adjusted.empty:
        return pd.DataFrame()

    frame = adjusted.copy()
    # The competition brief does not specify an official conversion table.
    frame["_grade_point"] = frame["Adjusted_Score"] * 0.4
    frame["_weighted_point"] = frame["_grade_point"] * frame["_credits"]
    frame["_weighted_raw"] = frame["_score"] * 0.4 * frame["_credits"]
    frame["_weighted_delta"] = frame["Mức đề xuất điều chỉnh"] * 0.4 * frame["_credits"]

    students = frame.groupby("Mã SV", dropna=True).agg(
        TCI=("_weighted_point", "sum"),
        _credits=("_credits", "sum"),
        GPA_danh_nghia=("_weighted_raw", "sum"),
        So_hoc_phan=("_score", "count"),
        So_lop_can_ra_soat=("Review Required", "sum"),
        Tong_muc_dieu_chinh=("_weighted_delta", "sum"),
    )
    students["TCI"] = students["TCI"] / students["_credits"].replace(0, np.nan)
    students["GPA_danh_nghia"] = (
        students["GPA_danh_nghia"] / students["_credits"].replace(0, np.nan)
    )
    students["Chênh lệch TCI"] = students["TCI"] - students["GPA_danh_nghia"]
    students["Phân loại"] = pd.cut(
        students["TCI"],
        bins=[-np.inf, 2.5, 3.2, 3.6, np.inf],
        labels=["At-Risk / Beginner", "Intermediate", "Proficient", "Advanced"],
        right=False,
    ).astype("string")
    students = students.reset_index().rename(
        columns={
            "_credits": "Tổng tín chỉ",
            "So_hoc_phan": "Số học phần",
            "So_lop_can_ra_soat": "Số lớp cần rà soát",
            "Tong_muc_dieu_chinh": "Tổng điều chỉnh quy đổi",
            "GPA_danh_nghia": "GPA danh nghĩa (quy đổi tuyến tính)",
        }
    )
    return students.sort_values("TCI", ascending=False).reset_index(drop=True)
