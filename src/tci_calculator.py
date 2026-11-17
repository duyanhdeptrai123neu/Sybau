from __future__ import annotations

import numpy as np
import pandas as pd


TCI_THRESHOLDS = [
    (3.60, "Advanced"),
    (3.20, "Proficient"),
    (2.50, "Intermediate"),
    (-np.inf, "At-Risk / Beginner"),
]


def _neu_grade_points(scores: pd.Series) -> pd.Series:
    """Convert rounded 10-point grades using the NEU QD 712/2025 reference table."""
    numeric = pd.to_numeric(scores, errors="coerce")
    values = numeric.to_numpy(dtype=float, na_value=np.nan)
    rounded = np.floor(values * 10 + 0.5 + 1e-9) / 10
    points = np.select(
        [
            rounded >= 8.5,
            rounded >= 8.0,
            rounded >= 7.0,
            rounded >= 6.5,
            rounded >= 5.5,
            rounded >= 5.0,
            rounded >= 4.5,
        ],
        [4.0, 3.5, 3.0, 2.5, 2.0, 1.5, 1.0],
        default=0.0,
    )
    points[np.isnan(rounded)] = np.nan
    return pd.Series(points, index=scores.index, dtype="float64")


def calculate_tci(adjusted: pd.DataFrame) -> pd.DataFrame:
    """Credit-weighted prototype index using the NEU 10-to-4 grade table."""
    if adjusted.empty:
        return pd.DataFrame()

    frame = adjusted.copy()
    # Use one-decimal grades and the published NEU QD 712/2025 scale as a
    # transparent reference. Confirm the applicable rule for each cohort before
    # using this analytical index for any official academic decision.
    frame["_grade_point"] = _neu_grade_points(frame["Adjusted_Score"])
    frame["_raw_grade_point"] = _neu_grade_points(frame["_score"])
    frame["_weighted_point"] = frame["_grade_point"] * frame["_credits"]
    frame["_weighted_raw"] = frame["_raw_grade_point"] * frame["_credits"]
    frame["_weighted_delta"] = (
        frame["_grade_point"] - frame["_raw_grade_point"]
    ) * frame["_credits"]

    students = frame.groupby("Mã SV", dropna=True).agg(
        TCI=("_weighted_point", "sum"),
        _credits=("_credits", "sum"),
        GPA_danh_nghia=("_weighted_raw", "sum"),
        So_hoc_phan=("_score", "count"),
        So_hoc_phan_chua_danh_gia=(
            "Nhãn", lambda labels: int(labels.eq("NOT_ASSESSED").sum())
        ),
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
            "So_hoc_phan_chua_danh_gia": "Số học phần chưa đánh giá",
            "So_lop_can_ra_soat": "Số lớp cần rà soát",
            "Tong_muc_dieu_chinh": "Tổng điều chỉnh quy đổi",
            "GPA_danh_nghia": "GPA danh nghĩa (quy đổi NEU, thử nghiệm)",
        }
    )
    return students.sort_values("TCI", ascending=False).reset_index(drop=True)
