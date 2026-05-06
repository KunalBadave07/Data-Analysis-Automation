from __future__ import annotations

import pandas as pd

from app.services.pipeline.preprocessing import clean_dataset, feature_engineering, handle_outliers


def test_clean_dataset_normalizes_columns_and_dates():
    raw = pd.DataFrame(
        {
            "Order Date": ["01-01-2025", "15-01-2025"],
            "Units Sold": ["10", "20"],
            "Region/Zone": ["North", "South"],
        }
    )

    cleaned, metadata = clean_dataset(raw)

    assert cleaned.columns.tolist() == ["order_date", "units_sold", "region_zone"]
    assert "order_date" in metadata["date_columns"]
    assert cleaned["units_sold"].sum() == 30


def test_feature_engineering_creates_date_parts():
    frame = pd.DataFrame({"date": pd.to_datetime(["2025-01-01", "2025-01-02"])})

    engineered, notes = feature_engineering(frame)

    assert {"date_year", "date_month", "date_day"}.issubset(engineered.columns)
    assert "year" in engineered.columns
    assert notes["derived_features"]


def test_handle_outliers_reports_counts_without_dropping_rows():
    frame = pd.DataFrame({"units_sold": [10, 11, 12, 13, 999]})

    result, notes = handle_outliers(frame)

    assert len(result) == 5
    assert notes["outlier_counts"]["units_sold"] >= 1
