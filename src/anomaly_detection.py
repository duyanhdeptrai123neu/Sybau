from __future__ import annotations

import numpy as np
import pandas as pd


SECTION = "Mã lớp học phần"
ANOMALY_COLUMNS = [
    SECTION, "Mã môn", "Năm học", "Học kỳ", "Số sinh viên", "Điểm TB lớp",
    "Độ lệch chuẩn", "Tỷ lệ điểm A", "Điểm TB tham chiếu", "Z robust",
    "Nhóm đối chiếu", "Độ tin cậy", "Anomaly Score", "Nhãn", "Giải thích",
]


def _robust_z(value: float, center: float, mad: float, fallback_scale: float) -> float:
    scale = 1.4826 * mad
    if not np.isfinite(scale) or scale < 1e-8:
        scale = max(fallback_scale, 0.25)
    return float((value - center) / scale)


def detect_anomalies(data: pd.DataFrame, min_class_size: int = 8) -> pd.DataFrame:
    """Rank sections against other sections of the same course where possible."""
    scored = data.loc[data["_score"].notna() & data[SECTION].notna()].copy()
    if scored.empty:
        return pd.DataFrame(columns=ANOMALY_COLUMNS)

    rows = []
    for section_id, group in scored.groupby(SECTION, dropna=True):
        regular = group.loc[~group["_is_project"]]
        if regular.empty:
            regular = group
        score = regular["_score"].astype(float)
        n = int(score.count())
        first = regular.iloc[0]
        rows.append(
            {
                SECTION: str(section_id),
                "Mã môn": str(first.get("Mã môn", "")),
                "Nhóm môn": str(first.get("Nhóm môn", "")),
                "Năm học": str(first.get("Năm học", "")),
                "Học kỳ": str(first.get("Học kỳ", "")),
                "Số sinh viên": n,
                "Điểm TB lớp": float(score.mean()),
                "Độ lệch chuẩn": float(score.std(ddof=1)) if n > 1 else 0.0,
                "Tỷ lệ điểm A": float((score >= 8.5).mean()),
                "Đồ án/thực tập": bool(group["_is_project"].all()),
            }
        )

    sections = pd.DataFrame(rows)
    if sections.empty:
        return sections

    diagnostics = []
    for _, current in sections.iterrows():
        if current["Đồ án/thực tập"]:
            diagnostics.append(
                {
                    SECTION: current[SECTION],
                    "Mã môn": current["Mã môn"],
                    "Năm học": current["Năm học"],
                    "Học kỳ": current["Học kỳ"],
                    "Số sinh viên": current["Số sinh viên"],
                    "Điểm TB lớp": current["Điểm TB lớp"],
                    "Độ lệch chuẩn": current["Độ lệch chuẩn"],
                    "Tỷ lệ điểm A": current["Tỷ lệ điểm A"],
                    "Điểm TB tham chiếu": np.nan,
                    "Z robust": np.nan,
                    "Nhóm đối chiếu": "Loại khỏi so sánh lớp thường",
                    "Độ tin cậy": "Không đánh giá",
                    "Anomaly Score": 0.0,
                    "Nhãn": "NO_FLAG",
                    "Giải thích": "Đồ án/thực tập/khóa luận được tách khỏi phân tích lớp thường",
                }
            )
            continue

        same_course = sections[
            (sections["Mã môn"] == current["Mã môn"])
            & (sections[SECTION] != current[SECTION])
            & (~sections["Đồ án/thực tập"])
            & (sections["Số sinh viên"] >= max(5, min_class_size // 2))
        ]
        source = "Cùng môn"
        peers = same_course
        if len(peers) < 2:
            peers = sections[
                (sections["Nhóm môn"] == current["Nhóm môn"])
                & (sections[SECTION] != current[SECTION])
                & (~sections["Đồ án/thực tập"])
                & (sections["Số sinh viên"] >= max(5, min_class_size // 2))
            ]
            source = "Cùng nhóm môn (tham chiếu yếu hơn)"

        if peers.empty:
            fallback = sections[
                (sections[SECTION] != current[SECTION]) & (~sections["Đồ án/thực tập"])
            ]
            peer_mean = float(fallback["Điểm TB lớp"].median())
            if not np.isfinite(peer_mean):
                peer_mean = float(current["Điểm TB lớp"])
            peer_sd = float(fallback["Độ lệch chuẩn"].median())
            if not np.isfinite(peer_sd):
                peer_sd = float(current["Độ lệch chuẩn"])
            peer_a = float(fallback["Tỷ lệ điểm A"].median())
            if not np.isfinite(peer_a):
                peer_a = float(current["Tỷ lệ điểm A"])
            mean_mad = 0.0
            a_mad = 0.0
            confidence = "Rất thấp · không đủ lớp đối chiếu"
            source = "Toàn bộ lớp thường (tham chiếu yếu)"
        else:
            peer_mean = float(peers["Điểm TB lớp"].median())
            peer_sd = float(peers["Độ lệch chuẩn"].median())
            peer_a = float(peers["Tỷ lệ điểm A"].median())
            mean_mad = float((peers["Điểm TB lớp"] - peer_mean).abs().median())
            a_mad = float((peers["Tỷ lệ điểm A"] - peer_a).abs().median())
            confidence = (
                "Cao" if len(peers) >= 5 and current["Số sinh viên"] >= min_class_size
                else "Vừa · số lớp đối chiếu còn ít"
            )

        mean_z = _robust_z(
            float(current["Điểm TB lớp"]), peer_mean, mean_mad,
            float(peers["Điểm TB lớp"].std(ddof=1)) if len(peers) > 1 else 0.5,
        )
        a_z = _robust_z(
            float(current["Tỷ lệ điểm A"]), peer_a, a_mad,
            float(peers["Tỷ lệ điểm A"].std(ddof=1)) if len(peers) > 1 else 0.1,
        )
        high_signal = max(
            np.clip(mean_z / 4, 0, 1),
            np.clip((a_z - 1) / 3, 0, 1),
            np.clip((current["Tỷ lệ điểm A"] - 0.60) / 0.40, 0, 1),
        )
        low_signal = float(np.clip((-mean_z - 1.5) / 3, 0, 1))
        narrow_signal = (
            float(np.clip((peer_sd - current["Độ lệch chuẩn"]) / max(peer_sd, 0.5), 0, 1))
            if peer_sd >= 0.5
            else 0.0
        )

        label = "NO_FLAG"
        reasons = []
        anomaly_score = 0.0
        if current["Tỷ lệ điểm A"] > 0.60:
            reasons.append("Tỷ lệ điểm từ 8,5 vượt 60%")
        if mean_z >= 2:
            reasons.append("Điểm trung bình cao hơn nhóm đối chiếu")
        if mean_z <= -2:
            reasons.append("Điểm trung bình thấp hơn nhóm đối chiếu")
        if narrow_signal >= 0.5:
            reasons.append("Độ phân tán điểm thấp bất thường so với nhóm đối chiếu")

        if (high_signal >= 0.4 and mean_z >= 1.5) or current["Tỷ lệ điểm A"] > 0.60:
            label = "HIGH_INFLATION"
            anomaly_score = float(max(high_signal, 0.25))
        elif low_signal >= 0.4:
            label = "UNUSUALLY_STEEP"
            anomaly_score = low_signal
        elif narrow_signal >= 0.5:
            label = "SUSPICIOUS_DISTRIBUTION"
            anomaly_score = narrow_signal

        if current["Số sinh viên"] < min_class_size:
            reasons.append(f"Lớp nhỏ (n={int(current['Số sinh viên'])}), cần thận trọng")
            confidence = "Thấp · lớp nhỏ"
        if not reasons:
            reasons.append("Chưa có chỉ báo vượt ngưỡng sàng lọc")

        diagnostics.append(
            {
                SECTION: current[SECTION],
                "Mã môn": current["Mã môn"],
                "Năm học": current["Năm học"],
                "Học kỳ": current["Học kỳ"],
                "Số sinh viên": current["Số sinh viên"],
                "Điểm TB lớp": current["Điểm TB lớp"],
                "Độ lệch chuẩn": current["Độ lệch chuẩn"],
                "Tỷ lệ điểm A": current["Tỷ lệ điểm A"],
                "Điểm TB tham chiếu": peer_mean,
                "Z robust": mean_z,
                "Nhóm đối chiếu": source,
                "Độ tin cậy": confidence,
                "Anomaly Score": anomaly_score,
                "Nhãn": label,
                "Giải thích": "; ".join(reasons),
            }
        )

    result = pd.DataFrame(diagnostics)
    result = result.sort_values(
        ["Anomaly Score", "Số sinh viên"], ascending=[False, False]
    ).reset_index(drop=True)
    return result


def other_course_correlation(data: pd.DataFrame) -> pd.DataFrame:
    """Exploratory proxy only; the source does not identify foundational courses."""
    valid = data.loc[data["_score"].notna() & data["Mã SV"].notna()].copy()
    if valid.empty:
        return pd.DataFrame(
            columns=[SECTION, "Tương quan với điểm môn khác (proxy)", "Số cặp quan sát"]
        )

    non_project = valid.loc[~valid["_is_project"]]
    course_means = (
        non_project.groupby(["Mã SV", "Mã môn"], dropna=True)["_score"]
        .mean()
        .rename("_course_mean")
        .reset_index()
    )
    student_stats = course_means.groupby("Mã SV")["_course_mean"].agg(["sum", "count"])
    valid = valid.merge(course_means, on=["Mã SV", "Mã môn"], how="left")
    valid = valid.merge(student_stats, left_on="Mã SV", right_index=True, how="left")
    valid["_other_course_mean"] = valid["sum"] / valid["count"]
    ordinary = ~valid["_is_project"] & valid["_course_mean"].notna() & (valid["count"] > 1)
    valid.loc[ordinary, "_other_course_mean"] = (
        (valid.loc[ordinary, "sum"] - valid.loc[ordinary, "_course_mean"])
        / (valid.loc[ordinary, "count"] - 1)
    )
    valid.loc[~valid["_is_project"] & (valid["count"] <= 1), "_other_course_mean"] = np.nan

    result = []
    for section, group in valid.dropna(subset=[SECTION]).groupby(SECTION):
        paired = group[["_score", "_other_course_mean"]].dropna()
        corr = paired["_score"].corr(paired["_other_course_mean"]) if len(paired) >= 8 else np.nan
        result.append(
            {
                SECTION: str(section),
                "Tương quan với điểm môn khác (proxy)": corr,
                "Số cặp quan sát": int(len(paired)),
            }
        )
    return pd.DataFrame(result)
