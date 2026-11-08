from __future__ import annotations

import pandas as pd

from .anomaly_detection import detect_anomalies, other_course_correlation
from .data_loader import prepare_grade_data, validate_grade_data
from .grade_adjustment import adjust_grades
from .tci_calculator import calculate_tci


def run_analysis(raw: pd.DataFrame) -> dict[str, pd.DataFrame]:
    errors = validate_grade_data(raw)
    if errors:
        raise ValueError("\n".join(errors))

    data = prepare_grade_data(raw)
    anomalies = detect_anomalies(data)
    correlations = other_course_correlation(data)
    if not correlations.empty and not anomalies.empty:
        anomalies = anomalies.merge(correlations, on="Mã lớp học phần", how="left")
    adjusted = adjust_grades(data, anomalies)
    students = calculate_tci(adjusted)
    return {
        "data": data,
        "anomalies": anomalies,
        "adjusted": adjusted,
        "students": students,
    }
