from __future__ import annotations

import pandas as pd


def validate_dataset_shape(df: pd.DataFrame) -> list[str]:
    issues: list[str] = []
    if df.empty:
        issues.append("The uploaded dataset is empty after loading.")
    if len(df.columns) < 2:
        issues.append("The dataset must contain at least two columns for analysis.")
    return issues


def validate_missing_headers(df: pd.DataFrame) -> list[str]:
    missing_headers = [str(column) for column in df.columns if str(column).startswith("unnamed")]
    if missing_headers:
        return [f"Unnamed columns detected: {', '.join(missing_headers)}"]
    return []


def validate_numeric_content(df: pd.DataFrame) -> list[str]:
    numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
    if numeric_columns:
        return []
    return ["No numeric columns were detected, so KPI and trend calculations may be limited."]


def run_data_validation(df: pd.DataFrame) -> dict:
    issues: list[str] = []
    issues.extend(validate_dataset_shape(df))
    issues.extend(validate_missing_headers(df))
    issues.extend(validate_numeric_content(df))
    warnings = [
        issue for issue in issues if "may be limited" in issue.lower() or "detected" in issue.lower()
    ]
    blockers = [
        issue for issue in issues if "must" in issue.lower() or "empty" in issue.lower()
    ]
    return {
        "issues": issues,
        "warnings": warnings,
        "blockers": blockers,
        "passed": not blockers,
        "summary": {
            "rows": len(df),
            "columns": len(df.columns),
            "numeric_columns": len(df.select_dtypes(include=["number"]).columns),
        },
    }
