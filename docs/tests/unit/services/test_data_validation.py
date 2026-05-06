from __future__ import annotations

import pandas as pd

from app.services.pipeline.data_validation import run_data_validation


def test_data_validation_fails_for_empty_dataset():
    result = run_data_validation(pd.DataFrame())

    assert result["passed"] is False
    assert any("empty" in issue.lower() for issue in result["issues"])


def test_data_validation_warns_without_numeric_columns():
    result = run_data_validation(pd.DataFrame({"category": ["A", "B"], "region": ["N", "S"]}))

    assert any("numeric columns" in issue.lower() for issue in result["issues"])


def test_data_validation_passes_for_valid_shape():
    result = run_data_validation(pd.DataFrame({"category": ["A", "B"], "sales": [10, 20]}))

    assert result["passed"] is True
