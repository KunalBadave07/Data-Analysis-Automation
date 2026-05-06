from __future__ import annotations

from app.services.analytics_service import build_metric_destinations, generate_analysis, infer_schema


def test_infer_schema_detects_dynamic_columns(sample_dataframe):
    schema = infer_schema(sample_dataframe)

    assert schema.date_column == "order_date"
    assert schema.quantity_column == "qty"
    assert schema.price_column == "unit_price"
    assert schema.category_column == "product_line"
    assert schema.region_column == "state"


def test_generate_analysis_builds_real_metrics_and_filters(sample_dataframe):
    analysis = generate_analysis(sample_dataframe, "business_analysis", region="South")

    assert analysis["metrics"]["records"]["value"] == 2
    assert analysis["metrics"]["total_metric"]["value"] == 45
    assert analysis["metrics"]["total_revenue"]["value"] == 5200
    assert analysis["filters"]["region"] == "South"
    assert analysis["dashboard"]["category_chart"]["labels"]
    assert analysis["recommendations"]
    assert analysis["insight_cards"]
    assert analysis["schema_health"]["confidence_score"] >= 45


def test_build_metric_destinations_uses_filters(sample_dataframe):
    analysis = generate_analysis(
        sample_dataframe,
        "business_analysis",
        category="A",
        region="North",
        year="2025",
        product="all",
    )
    destinations = build_metric_destinations("job-123", analysis)

    assert "job-123" in destinations["records"]["href"]
    assert "category=A" in destinations["records"]["href"]
    assert "region=North" in destinations["records"]["href"]
    assert "year=2025" in destinations["records"]["href"]
    assert "mode=business_analysis" in destinations["records"]["href"]
