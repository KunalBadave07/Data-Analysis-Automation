from __future__ import annotations

import re
import warnings
from pathlib import Path

import pandas as pd


def normalize_column_name(name: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", str(name).strip().lower())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "column"


def _make_unique_columns(columns: list[str]) -> list[str]:
    counts: dict[str, int] = {}
    unique_columns: list[str] = []
    for column in columns:
        seen = counts.get(column, 0)
        if seen == 0:
            unique_columns.append(column)
        else:
            unique_columns.append(f"{column}_{seen + 1}")
        counts[column] = seen + 1
    return unique_columns


def _looks_like_date_column(column_name: str) -> bool:
    tokens = ("date", "time", "month", "year", "day", "timestamp")
    return any(token in column_name for token in tokens)


def _maybe_parse_datetime(series: pd.Series, column_name: str) -> pd.Series | None:
    if series.dtype.kind in {"M"}:
        return series

    if not _looks_like_date_column(column_name):
        return None

    non_null = series.dropna()
    if non_null.empty:
        return None

    sample = non_null.astype(str).head(25)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        parsed_sample = pd.to_datetime(sample, errors="coerce", dayfirst=True)
    valid_ratio = parsed_sample.notna().mean()
    if valid_ratio < 0.6:
        return None

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        return pd.to_datetime(series, errors="coerce", dayfirst=True)


def load_dataset(path: str) -> pd.DataFrame:
    suffix = Path(path).suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError(f"Unsupported dataset format: {suffix}")


def clean_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    cleaned = df.copy()
    original_rows = len(cleaned)
    original_columns = len(cleaned.columns)

    cleaned = cleaned.drop_duplicates()
    duplicates_removed = original_rows - len(cleaned)
    cleaned.columns = _make_unique_columns(
        [normalize_column_name(column) for column in cleaned.columns]
    )

    string_columns = cleaned.select_dtypes(include=["object", "string"]).columns
    for column in string_columns:
        cleaned[column] = cleaned[column].astype(str).str.strip()
        cleaned[column] = cleaned[column].replace(
            {"": pd.NA, "nan": pd.NA, "none": pd.NA, "null": pd.NA}
        )

    date_columns: list[str] = []
    for column in cleaned.columns:
        parsed = _maybe_parse_datetime(cleaned[column], column)
        if parsed is not None:
            cleaned[column] = parsed
            date_columns.append(column)
            continue

        if cleaned[column].dtype.kind not in {"O", "U", "S"}:
            continue

        raw = cleaned[column].astype(str).str.replace(",", "", regex=False)
        raw = raw.str.replace(r"[$€£₹%]", "", regex=True)
        numeric = pd.to_numeric(raw, errors="coerce")
        numeric_ratio = numeric.notna().mean() if len(numeric) else 0
        if numeric_ratio >= 0.7:
            cleaned[column] = numeric

    metadata = {
        "original_rows": original_rows,
        "cleaned_rows": len(cleaned),
        "original_columns": original_columns,
        "cleaned_columns": len(cleaned.columns),
        "duplicates_removed": duplicates_removed,
        "standardized_columns": cleaned.columns.tolist(),
        "date_columns": date_columns,
    }
    return cleaned, metadata


def feature_engineering(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    enriched = df.copy()
    derived_features: list[str] = []

    for column in enriched.columns:
        if _looks_like_date_column(column) and not pd.api.types.is_datetime64_any_dtype(enriched[column]):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                parsed = pd.to_datetime(enriched[column], errors="coerce", dayfirst=True)
            if parsed.notna().mean() >= 0.6:
                enriched[column] = parsed

    for column in enriched.columns:
        if not pd.api.types.is_datetime64_any_dtype(enriched[column]):
            continue

        enriched[f"{column}_year"] = enriched[column].dt.year
        enriched[f"{column}_month"] = enriched[column].dt.month
        enriched[f"{column}_quarter"] = enriched[column].dt.quarter
        enriched[f"{column}_day"] = enriched[column].dt.day
        derived_features.extend(
            [
                f"{column}_year",
                f"{column}_month",
                f"{column}_quarter",
                f"{column}_day",
            ]
        )

    if "date" in enriched.columns and pd.api.types.is_datetime64_any_dtype(enriched["date"]) and "year" not in enriched.columns:
        enriched["year"] = enriched["date"].dt.year
        derived_features.append("year")
    if "date" in enriched.columns and pd.api.types.is_datetime64_any_dtype(enriched["date"]) and "month" not in enriched.columns:
        enriched["month"] = enriched["date"].dt.month
        derived_features.append("month")

    return enriched, {"derived_features": derived_features}


def handle_outliers(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
    outlier_summary: dict[str, int] = {}
    for column in numeric_columns:
        series = df[column].dropna()
        if len(series) < 5:
            continue
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        if pd.isna(iqr) or iqr == 0:
            continue
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outlier_summary[column] = int(((df[column] < lower) | (df[column] > upper)).sum())

    return df, {"outlier_counts": outlier_summary}


def save_processed_dataset(df: pd.DataFrame, path: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(target, index=False)
