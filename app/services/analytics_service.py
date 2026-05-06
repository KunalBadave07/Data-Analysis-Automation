from __future__ import annotations

from dataclasses import dataclass
from math import isnan
import re
from typing import Any

import numpy as np
import pandas as pd


SEMANTIC_ALIASES = {
    "date": ["date", "order_date", "invoice_date", "transaction_date", "timestamp", "time"],
    "quantity": [
        "units_sold",
        "units",
        "quantity",
        "qty",
        "volume",
        "demand",
        "sales_qty",
        "count",
    ],
    "revenue": ["revenue", "sales", "turnover", "amount", "gmv", "income"],
    "price": ["price", "unit_price", "selling_price", "avg_price", "cost"],
    "category": ["category", "segment", "product_category", "department", "line"],
    "region": ["region", "state", "zone", "territory", "city", "country", "market"],
    "customer": ["customer", "customer_name", "client", "account"],
    "product": ["product", "product_name", "sku", "item", "brand"],
    "inventory": ["inventory_level", "inventory", "stock", "stock_level", "on_hand"],
    "forecast": ["demand_forecast", "forecast", "projected_demand", "forecast_units"],
    "orders": ["units_ordered", "ordered_units", "orders", "order_qty"],
    "discount": ["discount", "discount_pct", "markdown"],
    "promotion": ["promotion_flag", "holiday_promotion", "promotion", "promo_flag", "campaign"],
}


@dataclass
class Schema:
    date_column: str | None
    quantity_column: str | None
    revenue_column: str | None
    price_column: str | None
    category_column: str | None
    region_column: str | None
    product_column: str | None
    customer_column: str | None
    primary_metric_column: str | None
    inventory_column: str | None
    forecast_column: str | None
    orders_column: str | None
    discount_column: str | None
    promotion_column: str | None
    categorical_columns: list[str]
    numeric_columns: list[str]
    datetime_columns: list[str]


def _normalize_identifier(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def _tokenize(value: str) -> set[str]:
    return {token for token in _normalize_identifier(value).split("_") if token}


def _match_alias(columns: list[str], aliases: list[str]) -> str | None:
    normalized_aliases = {_normalize_identifier(alias) for alias in aliases}
    for alias in aliases:
        if alias in columns:
            return alias
    normalized_columns = {_normalize_identifier(column): column for column in columns}
    for alias in normalized_aliases:
        if alias in normalized_columns:
            return normalized_columns[alias]

    alias_tokens = [_tokenize(alias) for alias in aliases]
    ranked_matches: list[tuple[int, int, str]] = []
    for column in columns:
        normalized_column = _normalize_identifier(column)
        tokens = _tokenize(column)
        score = 0
        exact_bonus = 0
        for alias, token_set in zip(aliases, alias_tokens):
            normalized_alias = _normalize_identifier(alias)
            if normalized_alias and normalized_alias in normalized_column:
                score += 5
            overlap = len(tokens & token_set)
            if overlap:
                score += overlap * 3
            if tokens == token_set and tokens:
                exact_bonus = 3
        if score:
            ranked_matches.append((score + exact_bonus, -len(normalized_column), column))

    if ranked_matches:
        ranked_matches.sort(reverse=True)
        return ranked_matches[0][2]
    return None


def _safe_number(value: Any) -> float | int:
    if value is None or (isinstance(value, float) and isnan(value)):
        return 0
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return round(float(value), 2)
    return value


def _format_number(value: Any, currency: bool = False, percent: bool = False) -> str:
    numeric = _safe_number(value)
    if not isinstance(numeric, (int, float)):
        return str(numeric)
    if percent:
        body = f"{float(numeric):,.1f}"
        return f"{body}%"
    if currency:
        body = f"{float(numeric):,.2f}"
        return f"Rs. {body}"
    body = f"{int(round(float(numeric))):,}"
    return body


def _safe_divide(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return float(numerator) / float(denominator)


def _labelize(value: str | None) -> str:
    if not value:
        return "Not Available"
    return value.replace("_", " ").title()


def _metric_suffix(metric_label: str, is_currency: bool = False, is_percent: bool = False) -> str:
    if is_percent:
        return "%"
    if is_currency:
        return "Revenue"
    return metric_label


def _time_bounds(df: pd.DataFrame, schema: Schema) -> tuple[str, str]:
    if not schema.date_column or schema.date_column not in df.columns:
        return ("the first observed period", "the latest observed period")
    valid_dates = pd.to_datetime(df[schema.date_column], errors="coerce").dropna()
    if valid_dates.empty:
        return ("the first observed period", "the latest observed period")
    return (str(valid_dates.min().date()), str(valid_dates.max().date()))


def _choose_categorical(columns: list[str], frame: pd.DataFrame, exclude: set[str]) -> list[str]:
    candidates: list[tuple[str, int]] = []
    max_distinct = max(2, min(40, int(len(frame) * 0.6) or 2))
    for column in columns:
        if column in exclude:
            continue
        series_or_frame = frame[column]
        if isinstance(series_or_frame, pd.DataFrame):
            continue
        distinct = series_or_frame.dropna().nunique()
        if 2 <= distinct <= max_distinct:
            candidates.append((column, distinct))
    candidates.sort(key=lambda item: item[1])
    return [column for column, _ in candidates]


def infer_schema(df: pd.DataFrame) -> Schema:
    columns = df.columns.tolist()
    numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
    datetime_columns = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
    categorical_source = (
        df.select_dtypes(include=["object", "string", "category", "bool"]).columns.tolist()
    )

    date_column = _match_alias(columns, SEMANTIC_ALIASES["date"])
    if not date_column and datetime_columns:
        date_column = datetime_columns[0]

    revenue_column = _match_alias(columns, SEMANTIC_ALIASES["revenue"])
    quantity_column = _match_alias(columns, SEMANTIC_ALIASES["quantity"])
    price_column = _match_alias(columns, SEMANTIC_ALIASES["price"])
    category_column = _match_alias(columns, SEMANTIC_ALIASES["category"])
    region_column = _match_alias(columns, SEMANTIC_ALIASES["region"])
    product_column = _match_alias(columns, SEMANTIC_ALIASES["product"])
    customer_column = _match_alias(columns, SEMANTIC_ALIASES["customer"])
    inventory_column = _match_alias(columns, SEMANTIC_ALIASES["inventory"])
    forecast_column = _match_alias(columns, SEMANTIC_ALIASES["forecast"])
    orders_column = _match_alias(columns, SEMANTIC_ALIASES["orders"])
    discount_column = _match_alias(columns, SEMANTIC_ALIASES["discount"])
    promotion_column = _match_alias(columns, SEMANTIC_ALIASES["promotion"])

    if not quantity_column:
        usable_numeric = [column for column in numeric_columns if column not in {"year", "month", "quarter"}]
        quantity_column = usable_numeric[0] if usable_numeric else None

    primary_metric_column = revenue_column or quantity_column or forecast_column or (numeric_columns[0] if numeric_columns else None)

    exclude = {value for value in [category_column, region_column, product_column, customer_column] if value}
    inferred_categoricals = _choose_categorical(categorical_source, df, exclude)
    if not category_column and inferred_categoricals:
        category_column = inferred_categoricals[0]
    if not region_column:
        region_candidates = [column for column in inferred_categoricals if column != category_column]
        region_column = region_candidates[0] if region_candidates else None
    if not product_column:
        product_candidates = [
            column for column in inferred_categoricals if column not in {category_column, region_column}
        ]
        product_column = product_candidates[0] if product_candidates else None
    if not customer_column:
        customer_candidates = [
            column
            for column in inferred_categoricals
            if column not in {category_column, region_column, product_column}
        ]
        customer_column = customer_candidates[0] if customer_candidates else None

    categorical_columns = []
    for column in [category_column, region_column, product_column, customer_column]:
        if column and column not in categorical_columns:
            categorical_columns.append(column)
    for column in inferred_categoricals:
        if column not in categorical_columns:
            categorical_columns.append(column)

    return Schema(
        date_column=date_column,
        quantity_column=quantity_column,
        revenue_column=revenue_column,
        price_column=price_column,
        category_column=category_column,
        region_column=region_column,
        product_column=product_column,
        customer_column=customer_column,
        primary_metric_column=primary_metric_column,
        inventory_column=inventory_column,
        forecast_column=forecast_column,
        orders_column=orders_column,
        discount_column=discount_column,
        promotion_column=promotion_column,
        categorical_columns=categorical_columns,
        numeric_columns=numeric_columns,
        datetime_columns=datetime_columns,
    )


def _ensure_revenue(df: pd.DataFrame, schema: Schema) -> tuple[pd.DataFrame, str | None]:
    if schema.revenue_column and schema.revenue_column in df.columns:
        return df, schema.revenue_column
    if schema.price_column and schema.quantity_column:
        enriched = df.copy()
        enriched["derived_revenue"] = enriched[schema.price_column].fillna(0) * enriched[
            schema.quantity_column
        ].fillna(0)
        return enriched, "derived_revenue"
    return df, None


def _apply_filters(
    df: pd.DataFrame,
    schema: Schema,
    category: str = "all",
    region: str = "all",
    year: str = "all",
    product: str = "all",
) -> tuple[pd.DataFrame, dict]:
    filtered = df.copy()
    applied = {"category": category, "region": region, "year": year, "product": product}

    if category != "all" and schema.category_column and schema.category_column in filtered.columns:
        filtered = filtered[filtered[schema.category_column].astype(str) == category]
    if region != "all" and schema.region_column and schema.region_column in filtered.columns:
        filtered = filtered[filtered[schema.region_column].astype(str) == region]
    if product != "all" and schema.product_column and schema.product_column in filtered.columns:
        filtered = filtered[filtered[schema.product_column].astype(str) == product]
    if year != "all" and schema.date_column and schema.date_column in filtered.columns:
        years = pd.to_datetime(filtered[schema.date_column], errors="coerce").dt.year
        filtered = filtered[years == int(year)]
    return filtered, applied


def _series_records(series: pd.Series, currency: bool = False, percent: bool = False, top_n: int = 10) -> list[dict]:
    if series.empty:
        return []
    return [
        {
            "label": str(index),
            "value": _safe_number(value),
            "display_value": _format_number(value, currency=currency, percent=percent),
        }
        for index, value in series.head(top_n).items()
    ]


def _build_kpis(df: pd.DataFrame, schema: Schema, revenue_column: str | None) -> dict:
    records = len(df)
    primary = schema.primary_metric_column
    quantity_total = df[schema.quantity_column].sum() if schema.quantity_column else 0
    quantity_average = df[schema.quantity_column].mean() if schema.quantity_column else 0
    revenue_total = df[revenue_column].sum() if revenue_column else 0
    revenue_average = df[revenue_column].mean() if revenue_column else 0

    metrics = {
        "records": {
            "label": "Records",
            "value": _safe_number(records),
            "display_value": _format_number(records),
            "detail_anchor": "dataset-overview",
            "insight": "Shows how many rows are included after processing and filters.",
        }
    }

    if primary and primary in df.columns:
        total_primary = df[primary].sum()
        avg_primary = df[primary].mean()
        metrics["total_metric"] = {
            "label": f"Total {_labelize(primary)}",
            "value": _safe_number(total_primary),
            "display_value": _format_number(total_primary, currency=primary == revenue_column),
            "detail_anchor": "metric-breakdown",
            "insight": f"Aggregates the filtered {_labelize(primary).lower()} across the selected scope.",
        }
        metrics["average_metric"] = {
            "label": f"Average {_labelize(primary)}",
            "value": _safe_number(avg_primary),
            "display_value": _format_number(avg_primary, currency=primary == revenue_column),
            "detail_anchor": "metric-breakdown",
            "insight": f"Shows the mean {_labelize(primary).lower()} per record.",
        }

    if schema.quantity_column and schema.quantity_column != primary:
        metrics["total_units"] = {
            "label": f"Total {_labelize(schema.quantity_column)}",
            "value": _safe_number(quantity_total),
            "display_value": _format_number(quantity_total),
            "detail_anchor": "metric-breakdown",
            "insight": "Tracks the total observed quantity in the filtered scope.",
        }
        metrics["avg_units"] = {
            "label": f"Average {_labelize(schema.quantity_column)}",
            "value": _safe_number(quantity_average),
            "display_value": _format_number(quantity_average),
            "detail_anchor": "metric-breakdown",
            "insight": "Shows the average quantity per record.",
        }

    if revenue_column:
        metrics["total_revenue"] = {
            "label": "Total Revenue",
            "value": _safe_number(revenue_total),
            "display_value": _format_number(revenue_total, currency=True),
            "detail_anchor": "revenue-breakdown",
            "insight": "Revenue is computed directly from dataset revenue or from quantity x price.",
        }
        metrics["avg_revenue"] = {
            "label": "Average Revenue",
            "value": _safe_number(revenue_average),
            "display_value": _format_number(revenue_average, currency=True),
            "detail_anchor": "revenue-breakdown",
            "insight": "Shows the mean revenue contribution per record.",
        }

    return metrics


def _time_series(
    df: pd.DataFrame, schema: Schema, metric_column: str | None, period: str = "M"
) -> tuple[pd.Series, str]:
    if not schema.date_column or not metric_column or schema.date_column not in df.columns or metric_column not in df.columns:
        return pd.Series(dtype=float), "No dated metric trend was available."

    trend_frame = df[[schema.date_column, metric_column]].dropna().copy()
    if trend_frame.empty:
        return pd.Series(dtype=float), "No dated metric trend was available."

    trend_frame[schema.date_column] = pd.to_datetime(trend_frame[schema.date_column], errors="coerce")
    trend_frame = trend_frame.dropna(subset=[schema.date_column])
    if trend_frame.empty:
        return pd.Series(dtype=float), "No dated metric trend was available."

    grouped = (
        trend_frame.groupby(trend_frame[schema.date_column].dt.to_period(period))[metric_column]
        .sum()
        .sort_index()
    )
    if len(grouped) < 2:
        return grouped, "The dataset contains limited time history, so trend confidence is low."

    x_axis = np.arange(len(grouped))
    slope = np.polyfit(x_axis, grouped.values.astype(float), 1)[0]
    direction = "upward" if slope > 0 else "downward" if slope < 0 else "flat"
    return grouped, f"The monthly trend is {direction} based on the observed time series."


def _forecast_series(trend_series: pd.Series, horizon: int = 3) -> dict:
    if trend_series.empty:
        return {
            "historical_labels": [],
            "historical_values": [],
            "future_labels": [],
            "forecast_values": [],
            "confidence_score": 0,
            "trend_delta_pct": 0,
            "projected_total": 0,
            "mape": 100,
            "first_label": "",
            "last_label": "",
            "first_value": 0,
            "last_value": 0,
        }

    actual_values = trend_series.astype(float).values
    if len(actual_values) == 1:
        forecast_values = np.repeat(actual_values[-1], horizon)
        fitted = actual_values
    else:
        x_axis = np.arange(len(actual_values))
        coeffs = np.polyfit(x_axis, actual_values, 1)
        fitted = coeffs[0] * x_axis + coeffs[1]
        future_x = np.arange(len(actual_values), len(actual_values) + horizon)
        forecast_values = coeffs[0] * future_x + coeffs[1]

    forecast_values = np.maximum(forecast_values, 0)
    future_labels = []
    if hasattr(trend_series.index, "to_timestamp") and len(trend_series.index):
        last_period = trend_series.index[-1]
        for step in range(1, horizon + 1):
            future_labels.append(str(last_period + step))
    else:
        future_labels = [f"Forecast {idx}" for idx in range(1, horizon + 1)]

    denominator = np.where(actual_values == 0, 1, actual_values)
    mape = float(np.mean(np.abs((actual_values - fitted) / denominator)) * 100) if len(actual_values) else 100
    confidence = max(35, min(95, round(100 - mape)))
    raw_trend_delta_pct = (
        _safe_divide(actual_values[-1] - actual_values[0], actual_values[0]) * 100 if len(actual_values) > 1 else 0
    )
    bounded_trend_delta_pct = max(0, min(100, raw_trend_delta_pct))

    return {
        "historical_labels": [str(index) for index in trend_series.index.tolist()],
        "historical_values": [_safe_number(value) for value in actual_values.tolist()],
        "future_labels": future_labels,
        "forecast_values": [_safe_number(value) for value in forecast_values.tolist()],
        "confidence_score": confidence,
        "trend_delta_pct": round(bounded_trend_delta_pct, 2),
        "raw_trend_delta_pct": round(raw_trend_delta_pct, 2),
        "projected_total": _safe_number(float(np.sum(forecast_values))),
        "mape": round(mape, 2),
        "first_label": str(trend_series.index[0]),
        "last_label": str(trend_series.index[-1]),
        "first_value": _safe_number(actual_values[0]),
        "last_value": _safe_number(actual_values[-1]),
    }


def _build_breakdowns(df: pd.DataFrame, schema: Schema, metric_column: str | None, revenue_column: str | None) -> dict:
    metric = metric_column or schema.primary_metric_column
    breakdowns: dict[str, Any] = {}
    metric_is_currency = metric == revenue_column

    if metric and schema.category_column and metric in df.columns:
        category_series = df.groupby(schema.category_column)[metric].sum().sort_values(ascending=False)
        breakdowns["category"] = {
            "label": _labelize(schema.category_column),
            "metric_label": _labelize(metric),
            "is_currency": metric_is_currency,
            "records": _series_records(category_series, currency=metric_is_currency),
            "series": category_series.to_dict(),
        }

    if metric and schema.region_column and metric in df.columns:
        region_series = df.groupby(schema.region_column)[metric].sum().sort_values(ascending=False)
        breakdowns["region"] = {
            "label": _labelize(schema.region_column),
            "metric_label": _labelize(metric),
            "is_currency": metric_is_currency,
            "records": _series_records(region_series, currency=metric_is_currency),
            "series": region_series.to_dict(),
        }

    return breakdowns


def _build_insights(
    df: pd.DataFrame,
    schema: Schema,
    metrics: dict,
    breakdowns: dict,
    trend_summary: str,
    revenue_column: str | None,
) -> list[str]:
    insights: list[str] = []
    if df.empty:
        return ["No records remain after applying the selected filters."]

    insights.append(f"The current analysis covers {len(df):,} records and {len(df.columns)} processed fields.")

    category_records = breakdowns.get("category", {}).get("records", [])
    if category_records:
        top_category = category_records[0]
        total_value = metrics.get("total_metric", {}).get("value") or 0
        share = (top_category["value"] / total_value * 100) if total_value else 0
        insights.append(
            f"{top_category['label']} is the leading {_labelize(schema.category_column).lower()} at {share:.2f}% of the main metric."
        )

    region_records = breakdowns.get("region", {}).get("records", [])
    if region_records:
        top_region = region_records[0]
        insights.append(f"{top_region['label']} is the strongest geographic segment in the current filtered view.")

    insights.append(trend_summary)

    if revenue_column and schema.quantity_column and schema.quantity_column in df.columns:
        unit_total = df[schema.quantity_column].sum()
        revenue_total = df[revenue_column].sum()
        if unit_total:
            insights.append(
                f"Average revenue per {_labelize(schema.quantity_column).lower()} is {revenue_total / unit_total:,.2f}."
            )

    missing_share = (df.isna().sum().sum() / (len(df) * len(df.columns))) * 100 if len(df.columns) else 0
    insights.append(f"Missing values represent {missing_share:.2f}% of the filtered analytical grid.")
    return insights


def _build_recommendations(
    df: pd.DataFrame,
    schema: Schema,
    breakdowns: dict,
    trend_series: pd.Series,
    revenue_column: str | None,
) -> list[str]:
    recommendations: list[str] = []

    category_records = breakdowns.get("category", {}).get("records", [])
    if len(category_records) >= 2 and schema.category_column:
        top_category = category_records[0]
        bottom_category = category_records[-1]
        recommendations.append(
            f"Prioritize the strongest {_labelize(schema.category_column).lower()} segment, {top_category['label']}, while reviewing why {bottom_category['label']} is trailing."
        )

    region_records = breakdowns.get("region", {}).get("records", [])
    if len(region_records) >= 2:
        top_region = region_records[0]
        bottom_region = region_records[-1]
        recommendations.append(
            f"Use the operating patterns from {top_region['label']} to improve performance in {bottom_region['label']}."
        )

    if len(trend_series) >= 3:
        recent = trend_series.tail(3)
        if recent.is_monotonic_increasing:
            recommendations.append("Prepare capacity and inventory for continued near-term growth seen in the latest periods.")
        elif recent.is_monotonic_decreasing:
            recommendations.append("Investigate the recent downward trend and review pricing, demand drivers, or stock availability.")

    if revenue_column and revenue_column in df.columns:
        average_revenue = df[revenue_column].mean()
        high_value_rows = df[df[revenue_column] > average_revenue]
        if schema.category_column and not high_value_rows.empty and schema.category_column in high_value_rows.columns:
            dominant = high_value_rows[schema.category_column].mode(dropna=True)
            if not dominant.empty:
                recommendations.append(
                    f"Design campaigns around high-value transactions in {dominant.iloc[0]} because this segment appears most often above-average revenue rows."
                )

    if not recommendations:
        recommendations.append("Review the detailed breakdowns to identify operational drivers before making strategic changes.")

    return recommendations


def _build_pareto_records(series: pd.Series) -> list[dict]:
    if series.empty:
        return []
    total = series.sum()
    cumulative = series.cumsum()
    return [
        {
            "label": str(index),
            "value": _safe_number(value),
            "cumulative_share": round(_safe_divide(cumulative.loc[index], total) * 100, 2) if total else 0,
        }
        for index, value in series.items()
    ]


def _promotion_mask(series: pd.Series) -> pd.Series:
    normalized = series.astype(str).str.strip().str.lower()
    return normalized.isin({"1", "true", "yes", "y", "on", "promoted"})


def _build_common_tables(
    breakdowns: dict,
    trend_series: pd.Series,
) -> list[dict]:
    tables: list[dict] = []
    category_records = breakdowns.get("category", {}).get("records", [])
    if category_records:
        category_metric = breakdowns.get("category", {}).get("metric_label", "Value")
        tables.append(
            {
                "title": "Top Category Breakdown",
                "columns": ["Category", category_metric],
                "rows": [[record["label"], record["display_value"]] for record in category_records[:5]],
            }
        )

    if len(trend_series) >= 2:
        growth_series = trend_series.pct_change().replace([np.inf, -np.inf], np.nan).dropna() * 100
        if not growth_series.empty:
            tables.append(
                {
                    "title": "Recent Trend Changes",
                    "columns": ["Period", "Change"],
                    "rows": [
                        [str(index), _format_number(value, percent=True)]
                        for index, value in growth_series.tail(5).items()
                    ],
                }
            )
    return tables


def _schema_health(schema: Schema, operation: str) -> dict:
    mapped = {
        "date": schema.date_column,
        "quantity": schema.quantity_column,
        "revenue": schema.revenue_column,
        "price": schema.price_column,
        "category": schema.category_column,
        "region": schema.region_column,
        "product": schema.product_column,
        "customer": schema.customer_column,
        "inventory": schema.inventory_column,
        "forecast": schema.forecast_column,
        "orders": schema.orders_column,
        "discount": schema.discount_column,
        "promotion": schema.promotion_column,
    }
    required = ["date", "quantity", "category", "region"]
    if operation == "forecasting":
        required.extend(["forecast", "inventory"])
    missing_required = [field for field in required if not mapped.get(field)]
    mapped_count = sum(1 for value in mapped.values() if value)
    confidence_score = max(45, min(99, round((mapped_count / len(mapped)) * 100)))
    mapping_notes = [
        f"{field.title()} mapped to {_labelize(column)}."
        for field, column in mapped.items()
        if column
    ]
    if not mapping_notes:
        mapping_notes.append("No strong retail field mappings were detected.")

    return {
        "mapped_count": mapped_count,
        "expected_count": len(mapped),
        "confidence_score": confidence_score,
        "missing_required": missing_required,
        "mapping_notes": mapping_notes[:6],
    }


def _build_insight_cards(
    df: pd.DataFrame,
    schema: Schema,
    operation: str,
    metrics: dict,
    breakdowns: dict,
    trend_series: pd.Series,
    revenue_column: str | None,
) -> list[dict]:
    cards: list[dict] = []
    category_records = breakdowns.get("category", {}).get("records", [])
    region_records = breakdowns.get("region", {}).get("records", [])

    if category_records:
        leader = category_records[0]
        cards.append(
            {
                "title": "Category Leader",
                "summary": f"{leader['label']} is contributing the strongest result right now.",
                "meaning": f"This {_labelize(schema.category_column).lower()} is leading the filtered performance mix.",
                "action": f"Protect inventory and marketing support for {leader['label']} while benchmarking weaker categories against it.",
                "tone": "positive",
            }
        )

    if len(trend_series) >= 3:
        recent = trend_series.tail(3)
        if recent.is_monotonic_increasing:
            cards.append(
                {
                    "title": "Demand Momentum",
                    "summary": "The latest periods are moving upward.",
                    "meaning": "Demand is accelerating rather than staying flat.",
                    "action": "Increase replenishment coverage and monitor top-selling products more frequently.",
                    "tone": "positive",
                }
            )
        elif recent.is_monotonic_decreasing:
            cards.append(
                {
                    "title": "Sales Slowdown",
                    "summary": "The latest periods are trending down.",
                    "meaning": "The business may be losing volume because of pricing, weaker demand, or stock friction.",
                    "action": "Review price moves, campaign activity, and availability in the weakest segments immediately.",
                    "tone": "risk",
                }
            )

    if operation == "forecasting" and schema.inventory_column and schema.forecast_column:
        if schema.inventory_column in df.columns and schema.forecast_column in df.columns:
            stock_risk = (df[schema.forecast_column].fillna(0) > df[schema.inventory_column].fillna(0)).mean() * 100
            cards.append(
                {
                    "title": "Stock-Out Risk",
                    "summary": f"{_format_number(stock_risk, percent=True)} of rows show forecast demand above current stock.",
                    "meaning": "Some future demand may be missed if inventory is not rebalanced in time.",
                    "action": "Prioritize replenishment for low-coverage products and locations first.",
                    "tone": "risk" if stock_risk >= 20 else "neutral",
                }
            )

    if revenue_column and revenue_column in df.columns and region_records:
        low_region = region_records[-1]
        cards.append(
            {
                "title": "Revenue Opportunity",
                "summary": f"{low_region['label']} is the softest geographic area in the current view.",
                "meaning": "This region is contributing less than peers and may have a mix, pricing, or stock execution gap.",
                "action": f"Audit assortment, availability, and conversion tactics in {low_region['label']}.",
                "tone": "neutral",
            }
        )

    if not cards:
        cards.append(
            {
                "title": "Executive Summary",
                "summary": "The dashboard is ready, but the dataset does not yet show a strong standout pattern.",
                "meaning": "The current filtered view is balanced or limited.",
                "action": "Use the filters to narrow the view by date, category, or geography to expose stronger signals.",
                "tone": "neutral",
            }
        )

    return cards[:4]


def _build_business_actions(
    recommendations: list[str],
    insight_cards: list[dict],
    operation: str,
) -> list[str]:
    actions = [card["action"] for card in insight_cards if card.get("action")]
    actions.extend(recommendations)
    if operation == "forecasting":
        actions.append("Use the forecast confidence and stock risk views together before placing the next buying decision.")
    else:
        actions.append("Use the performance mix and customer or product gaps to set the next weekly commercial review agenda.")
    deduped: list[str] = []
    for item in actions:
        if item not in deduped:
            deduped.append(item)
    return deduped[:5]


def _build_business_mode(
    df: pd.DataFrame,
    schema: Schema,
    trend_series: pd.Series,
    breakdowns: dict,
    revenue_column: str | None,
) -> dict:
    cards: list[dict] = []
    sections: list[dict] = []
    charts: list[dict] = []
    tables = _build_common_tables(breakdowns, trend_series)

    category_series = pd.Series(breakdowns.get("category", {}).get("series", {})).sort_values(ascending=False)
    region_series = pd.Series(breakdowns.get("region", {}).get("series", {})).sort_values(ascending=False)
    range_start, range_end = _time_bounds(df, schema)

    if not category_series.empty:
        top_share = _safe_divide(category_series.iloc[0], category_series.sum()) * 100
        cards.append(
            {
                "label": "Top Category Share",
                "display_value": _format_number(top_share, percent=True),
                "insight": f"{category_series.index[0]} contributes {_format_number(top_share, percent=True)} of the filtered {_labelize(schema.primary_metric_column).lower()} between {range_start} and {range_end}.",
            }
        )

    if schema.price_column and schema.price_column in df.columns:
        avg_price = df[schema.price_column].mean()
        cards.append(
            {
                "label": f"Average {_labelize(schema.price_column)}",
                "display_value": _format_number(avg_price, currency=True),
                "insight": f"The average selling price across the current filtered rows is {_format_number(avg_price, currency=True)}, computed from {len(df):,} records.",
            }
        )

    if schema.orders_column and schema.quantity_column and schema.orders_column in df.columns and schema.quantity_column in df.columns:
        fulfillment = _safe_divide(df[schema.quantity_column].sum(), df[schema.orders_column].sum()) * 100
        cards.append(
            {
                "label": "Sell-Through vs Ordered",
                "display_value": _format_number(fulfillment, percent=True),
                "insight": f"Current sell-through is {_format_number(fulfillment, percent=True)} because {df[schema.quantity_column].sum():,.0f} units were sold against {df[schema.orders_column].sum():,.0f} units ordered.",
            }
        )

    if schema.inventory_column and schema.quantity_column and schema.inventory_column in df.columns and schema.quantity_column in df.columns:
        turnover = _safe_divide(df[schema.quantity_column].sum(), df[schema.inventory_column].mean())
        cards.append(
            {
                "label": "Inventory Turnover Proxy",
                "display_value": _format_number(turnover),
                "insight": f"This proxy is {_format_number(turnover)} because total sold units are compared against an average inventory level of {_format_number(df[schema.inventory_column].mean())}.",
            }
        )

    if len(trend_series) >= 2:
        charts.append(
            {
                "id": "businessTrendChart",
                "title": "Past Performance Trend",
                "description": "Historical performance of the selected primary metric across time.",
                "type": "line",
                "metric_label": _labelize(schema.primary_metric_column),
                "labels": [str(index) for index in trend_series.index.tolist()],
                "datasets": [
                    {
                        "label": "Historical Trend",
                        "data": [_safe_number(value) for value in trend_series.values.tolist()],
                        "borderColor": "#b76e2b",
                        "backgroundColor": "rgba(183, 110, 43, 0.12)",
                        "fill": True,
                        "tension": 0.3,
                    }
                ],
            }
        )

    if schema.price_column and schema.quantity_column and schema.category_column and schema.price_column in df.columns and schema.quantity_column in df.columns and schema.category_column in df.columns:
        scatter_frame = (
            df.groupby(schema.category_column)[[schema.price_column, schema.quantity_column]]
            .mean()
            .reset_index()
            .sort_values(schema.quantity_column, ascending=False)
            .head(8)
        )
        charts.append(
            {
                "id": "businessPriceVolumeChart",
                "title": "Price vs Volume Position",
                "description": "Compares average selling price with average sold units for the leading categories.",
                "type": "bubble",
                "tooltip_mode": "bubble_price_volume",
                "x_label": "Average Price",
                "y_label": "Average Units Sold",
                "datasets": [
                    {
                        "label": row[schema.category_column],
                        "data": [{"x": _safe_number(row[schema.price_column]), "y": _safe_number(row[schema.quantity_column]), "r": 10 + idx}]
                    }
                    for idx, (_, row) in enumerate(scatter_frame.iterrows())
                ],
            }
        )

    if not category_series.empty:
        pareto = _build_pareto_records(category_series.head(8))
        charts.append(
            {
                "id": "businessCategoryChart",
                "title": "Category Performance",
                "description": "Highest-contributing categories in the filtered business view.",
                "type": "bar",
                "metric_label": _labelize(breakdowns.get("category", {}).get("metric_label", schema.primary_metric_column)),
                "labels": [record["label"] for record in pareto],
                "datasets": [
                    {
                        "label": "Category Value",
                        "data": [record["value"] for record in pareto],
                        "backgroundColor": "rgba(212, 151, 90, 0.78)",
                    },
                    {
                        "label": "Cumulative Share %",
                        "data": [record["cumulative_share"] for record in pareto],
                        "type": "line",
                        "yAxisID": "y1",
                        "borderColor": "#6e5d4d",
                        "backgroundColor": "rgba(110, 93, 77, 0.12)",
                        "tension": 0.25,
                    },
                ],
                "axes": {"secondary_percent": True},
            }
        )

    if not region_series.empty:
        charts.append(
            {
                "id": "businessRegionChart",
                "title": "Regional Distribution",
                "description": "How the primary metric is distributed across available regions.",
                "type": "doughnut",
                "metric_label": _labelize(breakdowns.get("region", {}).get("metric_label", schema.primary_metric_column)),
                "labels": [str(index) for index in region_series.index.tolist()],
                "datasets": [
                    {
                        "label": "Regional Value",
                        "data": [_safe_number(value) for value in region_series.values.tolist()],
                        "backgroundColor": [
                            "#d4975a",
                            "#efb679",
                            "#b76e2b",
                            "#8c5a38",
                            "#f3d2aa",
                            "#8b7a68",
                        ],
                    }
                ],
            }
        )

    if schema.promotion_column and schema.primary_metric_column and schema.promotion_column in df.columns and schema.primary_metric_column in df.columns:
        promoted_mask = _promotion_mask(df[schema.promotion_column])
        promo_values = pd.Series(
            {
                "Promoted": df.loc[promoted_mask, schema.primary_metric_column].mean() if promoted_mask.any() else 0,
                "Non-promoted": df.loc[~promoted_mask, schema.primary_metric_column].mean() if (~promoted_mask).any() else 0,
            }
        )
        charts.append(
            {
                "id": "businessPromoChart",
                "title": "Promotion Effect",
                "description": "Average primary metric with and without promotion activity.",
                "type": "bar",
                "metric_label": f"Average {_labelize(schema.primary_metric_column)}",
                "labels": [str(index) for index in promo_values.index.tolist()],
                "datasets": [
                    {
                        "label": "Average Metric",
                        "data": [_safe_number(value) for value in promo_values.values.tolist()],
                        "backgroundColor": ["rgba(183, 110, 43, 0.85)", "rgba(110, 93, 77, 0.72)"],
                    }
                ],
            }
        )
        uplift = _safe_divide(promo_values.iloc[0] - promo_values.iloc[1], promo_values.iloc[1]) * 100 if len(promo_values) == 2 else 0
        sections.append(
            {
                "title": "Commercial Drivers",
                "items": [
                    f"Promotion-linked average metric uplift is {_format_number(uplift, percent=True)}.",
                    "Use this comparison to decide whether campaign-driven volume is translating into stronger business performance.",
                ],
            }
        )

    if schema.orders_column and schema.quantity_column and schema.orders_column in df.columns and schema.quantity_column in df.columns:
        gap = df[schema.orders_column] - df[schema.quantity_column]
        sections.append(
            {
                "title": "Operational Balance",
                "items": [
                    f"Average order-to-sale gap is {_format_number(gap.mean())} units.",
                    f"Largest observed order-to-sale gap is {_format_number(gap.max())} units.",
                    "This helps identify whether ordering decisions are consistently overshooting realized sales.",
                ],
            }
        )

    if schema.date_column and schema.quantity_column and schema.price_column and schema.date_column in df.columns and schema.quantity_column in df.columns and schema.price_column in df.columns:
        monthly = df.copy()
        monthly[schema.date_column] = pd.to_datetime(monthly[schema.date_column], errors="coerce")
        monthly = monthly.dropna(subset=[schema.date_column])
        if not monthly.empty:
            monthly["period"] = monthly[schema.date_column].dt.to_period("M")
            monthly_mix = monthly.groupby("period").agg(
                avg_price=(schema.price_column, "mean"),
                total_units=(schema.quantity_column, "sum"),
            ).tail(8)
            charts.append(
                {
                    "id": "businessMonthlyMixChart",
                    "title": "Price and Volume Over Time",
                    "description": "Shows whether price changes are moving with or against units sold.",
                    "type": "bar",
                    "tooltip_mode": "dual_metric",
                    "left_metric_label": "Units Sold",
                    "right_metric_label": "Average Price",
                    "labels": [str(index) for index in monthly_mix.index.tolist()],
                    "datasets": [
                        {
                            "label": "Total Units",
                            "data": [_safe_number(value) for value in monthly_mix["total_units"].tolist()],
                            "backgroundColor": "rgba(212, 151, 90, 0.76)",
                        },
                        {
                            "label": "Average Price",
                            "data": [_safe_number(value) for value in monthly_mix["avg_price"].tolist()],
                            "type": "line",
                            "yAxisID": "y1",
                            "borderColor": "#6e5d4d",
                            "backgroundColor": "rgba(110, 93, 77, 0.12)",
                            "tension": 0.28,
                        },
                    ],
                    "axes": {"secondary_numeric": True},
                }
            )

    if schema.inventory_column and schema.inventory_column in df.columns:
        low_inventory_share = _safe_divide((df[schema.inventory_column] <= df[schema.inventory_column].quantile(0.25)).sum(), len(df)) * 100
        sections.append(
            {
                "title": "Stock Position",
                "items": [
                    f"{_format_number(low_inventory_share, percent=True)} of rows sit in the lowest inventory quartile.",
                    "This is useful for spotting pressure points before stock availability affects sales performance.",
                ],
            }
        )

    if not sections:
        sections.append(
            {
                "title": "Business Focus",
                "items": [
                    "This dashboard emphasizes category mix, regional contribution, and operational performance from the filtered dataset.",
                    "Use the cards and charts together to identify which segments drive the strongest outcomes and where execution is lagging.",
                ],
            }
        )

    return {
        "name": "Business Analysis",
        "intro": "This view focuses on current performance, segment contribution, and operational efficiency.",
        "cards": cards,
        "sections": sections,
        "charts": charts,
        "tables": tables,
    }


def _build_forecasting_mode(
    df: pd.DataFrame,
    schema: Schema,
    trend_series: pd.Series,
    breakdowns: dict,
    revenue_column: str | None,
) -> dict:
    cards: list[dict] = []
    sections: list[dict] = []
    charts: list[dict] = []
    tables = _build_common_tables(breakdowns, trend_series)
    forecast_model = _forecast_series(trend_series, horizon=3)
    range_start, range_end = _time_bounds(df, schema)

    if forecast_model["future_labels"]:
        cards.append(
            {
                "label": "Projected Next Period",
                "display_value": _format_number(forecast_model["forecast_values"][0]),
                "insight": f"Using the observed trend from {forecast_model['first_label']} ({_format_number(forecast_model['first_value'])}) to {forecast_model['last_label']} ({_format_number(forecast_model['last_value'])}), the next projected period is {forecast_model['future_labels'][0]} at {_format_number(forecast_model['forecast_values'][0])}.",
            }
        )
        cards.append(
            {
                "label": "Projected 3-Period Total",
                "display_value": _format_number(forecast_model["projected_total"]),
                "insight": f"The combined projection for {', '.join(forecast_model['future_labels'])} is {_format_number(forecast_model['projected_total'])}, which is the sum of the next three forecasted periods.",
            }
        )
        cards.append(
            {
                "label": "Forecast Confidence",
                "display_value": _format_number(forecast_model["confidence_score"], percent=True),
                "insight": f"The confidence score is {_format_number(forecast_model['confidence_score'], percent=True)} because the fitted historical trend stayed within about {_format_number(forecast_model['mape'], percent=True)} average error across the available history.",
            }
        )
        cards.append(
            {
                "label": "Historical Trend Change",
                "display_value": _format_number(forecast_model["trend_delta_pct"], percent=True),
                "insight": f"The filtered trend moved from {_format_number(forecast_model['first_value'])} in {forecast_model['first_label']} to {_format_number(forecast_model['last_value'])} in {forecast_model['last_label']}, which normalizes to a trend score of {_format_number(forecast_model['trend_delta_pct'], percent=True)} for dashboard comparison.",
            }
        )

        charts.append(
            {
                "id": "forecastTrendChart",
                "title": "Historical vs Forecasted Trend",
                "description": "Observed history and the next projected periods on the same timeline.",
                "type": "line",
                "metric_label": _labelize(schema.forecast_column or schema.primary_metric_column),
                "labels": forecast_model["historical_labels"] + forecast_model["future_labels"],
                "datasets": [
                    {
                        "label": "Observed",
                        "data": forecast_model["historical_values"] + [None] * len(forecast_model["future_labels"]),
                        "borderColor": "#b76e2b",
                        "backgroundColor": "rgba(183, 110, 43, 0.12)",
                        "fill": False,
                        "tension": 0.3,
                    },
                    {
                        "label": "Forecast",
                        "data": [None] * max(0, len(forecast_model["historical_values"]) - 1)
                        + [forecast_model["historical_values"][-1]]
                        + forecast_model["forecast_values"],
                        "borderColor": "#6e5d4d",
                        "backgroundColor": "rgba(110, 93, 77, 0.12)",
                        "borderDash": [6, 6],
                        "fill": False,
                        "tension": 0.3,
                    },
                ],
            }
        )

    if len(trend_series) >= 2:
        change_series = trend_series.pct_change().replace([np.inf, -np.inf], np.nan).dropna() * 100
        if not change_series.empty:
            charts.append(
                {
                    "id": "forecastChangeChart",
                    "title": "Past Trend Momentum",
                    "description": "Month-over-month change helps explain whether demand is accelerating or cooling.",
                    "type": "bar",
                    "metric_label": "Change",
                    "value_is_percent": True,
                    "labels": [str(index) for index in change_series.index.tolist()],
                    "datasets": [
                        {
                            "label": "Change %",
                            "data": [_safe_number(value) for value in change_series.values.tolist()],
                            "backgroundColor": [
                                "rgba(47, 150, 100, 0.75)" if value >= 0 else "rgba(180, 79, 82, 0.75)"
                                for value in change_series.values.tolist()
                            ],
                        }
                    ],
                }
            )

    if schema.region_column and schema.forecast_column and schema.region_column in df.columns and schema.forecast_column in df.columns:
        regional_forecast = df.groupby(schema.region_column)[schema.forecast_column].sum().sort_values(ascending=False)
        charts.append(
            {
                "id": "forecastRegionChart",
                "title": "Forecasted Demand by Region",
                "description": "Highlights where the forward-looking demand base is currently concentrated.",
                "type": "polarArea",
                "metric_label": _labelize(schema.forecast_column or schema.primary_metric_column),
                "labels": [str(index) for index in regional_forecast.index.tolist()],
                "datasets": [
                    {
                        "label": "Forecasted Demand",
                        "data": [_safe_number(value) for value in regional_forecast.values.tolist()],
                        "backgroundColor": [
                            "rgba(212, 151, 90, 0.78)",
                            "rgba(183, 110, 43, 0.78)",
                            "rgba(110, 93, 77, 0.78)",
                            "rgba(239, 182, 121, 0.78)",
                            "rgba(243, 210, 170, 0.84)",
                        ],
                    }
                ],
            }
        )

    category_series = pd.Series(breakdowns.get("category", {}).get("series", {})).sort_values(ascending=False)
    if not category_series.empty:
        charts.append(
            {
                "id": "forecastCategoryChart",
                "title": "Demand Contribution by Category",
                "description": "Useful for identifying which segments are most likely to shape the future baseline.",
                "type": "bar",
                "metric_label": _labelize(schema.forecast_column or schema.primary_metric_column),
                "labels": [str(index) for index in category_series.head(8).index.tolist()],
                "datasets": [
                    {
                        "label": "Current Demand Base",
                        "data": [_safe_number(value) for value in category_series.head(8).values.tolist()],
                        "backgroundColor": "rgba(212, 151, 90, 0.78)",
                    }
                ],
            }
        )

    if schema.inventory_column and schema.forecast_column and schema.inventory_column in df.columns and schema.forecast_column in df.columns:
        coverage_frame = df.copy()
        coverage_frame["coverage_gap"] = coverage_frame[schema.inventory_column].fillna(0) - coverage_frame[schema.forecast_column].fillna(0)
        dimension = schema.region_column or schema.category_column
        if dimension and dimension in coverage_frame.columns:
            coverage_series = coverage_frame.groupby(dimension)["coverage_gap"].mean().sort_values()
            charts.append(
                {
                    "id": "forecastCoverageChart",
                    "title": "Forecast Coverage Gap",
                    "description": "Negative values indicate forecasted demand is outpacing current inventory.",
                    "type": "bar",
                    "metric_label": "Coverage Gap",
                    "labels": [str(index) for index in coverage_series.index.tolist()],
                    "datasets": [
                        {
                            "label": "Inventory - Forecast",
                            "data": [_safe_number(value) for value in coverage_series.values.tolist()],
                            "backgroundColor": [
                                "rgba(180, 79, 82, 0.75)" if value < 0 else "rgba(47, 150, 100, 0.75)"
                                for value in coverage_series.values.tolist()
                            ],
                        }
                    ],
                }
            )
            risk_rows = coverage_series.head(5)
            tables.append(
                {
                    "title": "Highest Forecast Risk Areas",
                    "columns": [_labelize(dimension), "Coverage Gap"],
                    "rows": [[str(index), _format_number(value)] for index, value in risk_rows.items()],
                }
            )
            sections.append(
                {
                    "title": "Forecast Readiness",
                    "items": [
                        f"Average coverage gap across {_labelize(dimension).lower()} is {_format_number(coverage_series.mean())}.",
                        "Negative coverage gaps should be prioritized because projected demand is higher than available stock.",
                    ],
                }
            )

    if schema.forecast_column and schema.quantity_column and schema.forecast_column in df.columns and schema.quantity_column in df.columns:
        variance = df[schema.forecast_column] - df[schema.quantity_column]
        sections.append(
            {
                "title": "Forecast Accuracy Reference",
                "items": [
                    f"Average forecast variance is {_format_number(variance.mean())} units.",
                    f"Average absolute forecast variance is {_format_number(variance.abs().mean())} units.",
                    "This provides a reality check on how closely historical demand matched the forecast baseline in the file.",
                ],
            }
        )

    if schema.date_column and schema.forecast_column and schema.quantity_column and schema.date_column in df.columns and schema.forecast_column in df.columns and schema.quantity_column in df.columns:
        season = df.copy()
        season[schema.date_column] = pd.to_datetime(season[schema.date_column], errors="coerce")
        season = season.dropna(subset=[schema.date_column])
        if not season.empty:
            season["month_name"] = season[schema.date_column].dt.strftime("%b")
            season["month_num"] = season[schema.date_column].dt.month
            month_pattern = (
                season.groupby(["month_num", "month_name"])
                .agg(actual=(schema.quantity_column, "sum"), forecast=(schema.forecast_column, "sum"))
                .reset_index()
                .sort_values("month_num")
            )
            charts.append(
                {
                    "id": "forecastSeasonalityChart",
                    "title": "Actual vs Forecast Seasonality",
                    "description": f"Compares forecasted demand with actual demand across the available months from {range_start} to {range_end}.",
                    "type": "bar",
                    "tooltip_mode": "seasonality_compare",
                    "labels": month_pattern["month_name"].tolist(),
                    "datasets": [
                        {
                            "label": "Actual Demand",
                            "data": [_safe_number(value) for value in month_pattern["actual"].tolist()],
                            "backgroundColor": "rgba(212, 151, 90, 0.76)",
                        },
                        {
                            "label": "Forecast Demand",
                            "data": [_safe_number(value) for value in month_pattern["forecast"].tolist()],
                            "backgroundColor": "rgba(110, 93, 77, 0.72)",
                        },
                    ],
                }
            )

    if not sections:
        sections.append(
            {
                "title": "Forecast Outlook",
                "items": [
                    "This view emphasizes historical trend movement, near-term projections, and likely pressure points for future demand.",
                    "Use the forecast cards with the trend and coverage charts to plan inventory and capacity more confidently.",
                ],
            }
        )

    return {
        "name": "Forecasting",
        "intro": "This view focuses on past trends, future projections, and readiness for upcoming demand.",
        "cards": cards,
        "sections": sections,
        "charts": charts,
        "tables": tables,
    }


def _fallback_charts(
    schema: Schema,
    trend_series: pd.Series,
    breakdowns: dict,
) -> list[dict]:
    charts: list[dict] = []
    category_records = breakdowns.get("category", {}).get("records", [])
    region_records = breakdowns.get("region", {}).get("records", [])

    if len(trend_series):
        charts.append(
            {
                "id": "fallbackTrendChart",
                "title": "Trend Analysis",
                "description": "Observed metric trend across the available time periods.",
                "type": "line",
                "metric_label": _labelize(schema.primary_metric_column or "metric"),
                "labels": [str(index) for index in trend_series.index.tolist()],
                "datasets": [
                    {
                        "label": _labelize(schema.primary_metric_column or "metric"),
                        "data": [_safe_number(value) for value in trend_series.values.tolist()],
                        "borderColor": "#b76e2b",
                        "backgroundColor": "rgba(183, 110, 43, 0.12)",
                        "fill": True,
                        "tension": 0.25,
                    }
                ],
            }
        )

    if category_records:
        charts.append(
            {
                "id": "fallbackCategoryChart",
                "title": "Category Performance",
                "description": "Breakdown of the selected metric across categories.",
                "type": "bar",
                "metric_label": breakdowns.get("category", {}).get("metric_label", _labelize(schema.primary_metric_column)),
                "labels": [item["label"] for item in category_records],
                "datasets": [{"label": "Category Value", "data": [item["value"] for item in category_records]}],
            }
        )

    if region_records:
        charts.append(
            {
                "id": "fallbackRegionChart",
                "title": "Regional Distribution",
                "description": "Breakdown of the selected metric across regions.",
                "type": "doughnut",
                "metric_label": breakdowns.get("region", {}).get("metric_label", _labelize(schema.primary_metric_column)),
                "labels": [item["label"] for item in region_records],
                "datasets": [{"label": "Regional Value", "data": [item["value"] for item in region_records]}],
            }
        )
    return charts


def _build_dashboard_data(
    df: pd.DataFrame,
    operation: str,
    schema: Schema,
    metrics: dict,
    breakdowns: dict,
    trend_series: pd.Series,
    revenue_column: str | None,
    mode_details: dict,
    filters: dict,
    filter_lists: dict,
    summary: str,
    insight_cards: list[dict],
    recommendations: list[str],
    business_actions: list[str],
    schema_health: dict,
) -> dict:
    category_records = breakdowns.get("category", {}).get("records", [])
    region_records = breakdowns.get("region", {}).get("records", [])
    currency_mode = revenue_column == schema.primary_metric_column or bool(revenue_column)

    selected_kpis = ["records", "total_metric", "total_revenue", "average_metric"]
    if operation == "forecasting":
        selected_kpis = []
    elif operation == "business_analysis":
        selected_kpis = ["records", "total_metric", "total_revenue", "avg_revenue"]
        if revenue_column and schema.primary_metric_column == revenue_column:
            selected_kpis = ["records", "total_metric", "avg_revenue"]

    dashboard_kpis = []
    selected_kpi_set = set(selected_kpis)
    for key, item in metrics.items():
        if key not in selected_kpi_set:
            continue
        dashboard_kpis.append(
            {
                "key": key,
                "label": item["label"],
                "display_value": item["display_value"],
                "insight": item.get("insight", ""),
            }
        )

    if operation == "business_analysis" and revenue_column and schema.primary_metric_column == revenue_column:
        if schema.price_column and schema.price_column in df.columns:
            average_price = df[schema.price_column].mean()
            dashboard_kpis.append(
                {
                    "key": "average_price",
                    "label": f"Average {_labelize(schema.price_column)}",
                    "display_value": _format_number(average_price, currency=True),
                    "insight": f"The average selling price across the current filtered rows is {_format_number(average_price, currency=True)}, computed from {len(df):,} records.",
                }
            )
        else:
            for index, card in enumerate(mode_details.get("cards", []), start=1):
                dashboard_kpis.append(
                    {
                        "key": f"mode_card_{index}",
                        "label": card["label"],
                        "display_value": card["display_value"],
                        "insight": card["insight"],
                    }
                )
                if len(dashboard_kpis) >= 4:
                    break
    else:
        for index, card in enumerate(mode_details.get("cards", []), start=1):
            dashboard_kpis.append(
                {
                    "key": f"mode_card_{index}",
                    "label": card["label"],
                    "display_value": card["display_value"],
                    "insight": card["insight"],
                }
            )
    dashboard_kpis = dashboard_kpis[:4]

    charts = mode_details.get("charts") or _fallback_charts(schema, trend_series, breakdowns)
    available_modes = [
        {"key": "business_analysis", "label": "Business Analysis"},
        {"key": "forecasting", "label": "Forecasting"},
    ]

    return {
        "operation": operation,
        "mode_name": mode_details.get("name", _labelize(operation)),
        "mode_intro": mode_details.get("intro", ""),
        "summary": summary,
        "metric_label": _labelize(schema.forecast_column if operation == "forecasting" and schema.forecast_column else schema.primary_metric_column),
        "filters": filters,
        "filter_lists": filter_lists,
        "available_modes": available_modes,
        "kpis": dashboard_kpis,
        "highlights": insight_cards,
        "charts": charts,
        "tables": mode_details.get("tables", []),
        "mode_sections": mode_details.get("sections", []),
        "recommendations": recommendations,
        "business_actions": business_actions,
        "schema_health": schema_health,
        "trend": {
            "labels": [str(index) for index in trend_series.index.tolist()],
            "values": [_safe_number(value) for value in trend_series.values.tolist()],
            "label": _labelize(schema.primary_metric_column or "metric"),
        },
        "category_chart": {
            "labels": [item["label"] for item in category_records],
            "values": [item["value"] for item in category_records],
            "label": breakdowns.get("category", {}).get("label", "Category"),
        },
        "region_chart": {
            "labels": [item["label"] for item in region_records],
            "values": [item["value"] for item in region_records],
            "label": breakdowns.get("region", {}).get("label", "Region"),
        },
        "currency_mode": currency_mode,
    }


def _build_report_sections(
    df: pd.DataFrame,
    schema: Schema,
    processing_notes: dict,
    trend_series: pd.Series,
    mode_details: dict,
) -> dict:
    date_range = "Not available"
    if schema.date_column and schema.date_column in df.columns:
        valid_dates = pd.to_datetime(df[schema.date_column], errors="coerce").dropna()
        if not valid_dates.empty:
            date_range = f"{valid_dates.min().date()} to {valid_dates.max().date()}"

    return {
        "dataset_overview": [
            f"Rows used in analysis: {len(df):,}",
            f"Columns found in dataset: {len(df.columns)}",
            f"Data period covered: {date_range}",
            f"Main metric being analyzed: {_labelize(schema.primary_metric_column)}",
        ],
        "preprocessing": [
            f"Rows removed as duplicates: {processing_notes.get('duplicates_removed', 0)}",
            f"Date columns found: {', '.join(processing_notes.get('date_columns', [])) or 'None'}",
            f"Extra date insights added: {', '.join(processing_notes.get('derived_features', [])) or 'None'}",
        ],
        "feature_analysis": [
            f"Categorical dimensions used: {', '.join(schema.categorical_columns) or 'None'}",
            f"Numeric fields detected: {', '.join(schema.numeric_columns) or 'None'}",
            f"Top trend points available: {len(trend_series)}",
        ],
        "mode_sections": mode_details.get("sections", []),
    }


def generate_analysis(
    df: pd.DataFrame,
    operation: str,
    *,
    category: str = "all",
    region: str = "all",
    year: str = "all",
    product: str = "all",
    processing_notes: dict | None = None,
) -> dict:
    df = df.loc[:, ~df.columns.duplicated()].copy()
    schema = infer_schema(df)
    enriched_df, revenue_column = _ensure_revenue(df, schema)
    filtered_df, applied_filters = _apply_filters(
        enriched_df, schema, category=category, region=region, year=year, product=product
    )

    metrics = _build_kpis(filtered_df, schema, revenue_column)
    trend_metric = schema.forecast_column if operation == "forecasting" and schema.forecast_column in filtered_df.columns else schema.primary_metric_column
    trend_series, trend_summary = _time_series(filtered_df, schema, trend_metric)
    breakdown_metric = trend_metric if trend_metric in filtered_df.columns else schema.primary_metric_column
    breakdowns = _build_breakdowns(filtered_df, schema, breakdown_metric, revenue_column)
    insights = _build_insights(filtered_df, schema, metrics, breakdowns, trend_summary, revenue_column)
    recommendations = _build_recommendations(
        filtered_df, schema, breakdowns, trend_series, revenue_column
    )
    schema_health = _schema_health(schema, operation)
    insight_cards = _build_insight_cards(
        filtered_df,
        schema,
        operation,
        metrics,
        breakdowns,
        trend_series,
        revenue_column,
    )
    business_actions = _build_business_actions(recommendations, insight_cards, operation)

    if operation == "forecasting":
        mode_details = _build_forecasting_mode(filtered_df, schema, trend_series, breakdowns, revenue_column)
    else:
        mode_details = _build_business_mode(filtered_df, schema, trend_series, breakdowns, revenue_column)

    filter_lists = {
        "category_list": sorted(enriched_df[schema.category_column].dropna().astype(str).unique().tolist())
        if schema.category_column
        else [],
        "region_list": sorted(enriched_df[schema.region_column].dropna().astype(str).unique().tolist())
        if schema.region_column
        else [],
        "product_list": sorted(enriched_df[schema.product_column].dropna().astype(str).unique().tolist())
        if schema.product_column
        else [],
        "year_list": sorted(
            pd.to_datetime(enriched_df[schema.date_column], errors="coerce").dropna().dt.year.unique().tolist()
        )
        if schema.date_column
        else [],
    }

    summary = (
        f"Processed {len(filtered_df):,} records using {_labelize(schema.primary_metric_column or 'detected primary metric')} for {operation.replace('_', ' ')}."
    )

    dashboard = _build_dashboard_data(
        filtered_df,
        operation,
        schema,
        metrics,
        breakdowns,
        trend_series,
        revenue_column,
        mode_details,
        applied_filters,
        filter_lists,
        summary,
        insight_cards,
        recommendations,
        business_actions,
        schema_health,
    )
    report_sections = _build_report_sections(
        filtered_df,
        schema,
        processing_notes or {},
        trend_series,
        mode_details,
    )

    return {
        "summary": summary,
        "metrics": metrics,
        "insights": insights,
        "insight_cards": insight_cards,
        "recommendations": recommendations,
        "business_actions": business_actions,
        "dashboard": dashboard,
        "report_sections": report_sections,
        "schema": schema.__dict__,
        "schema_health": schema_health,
        "breakdowns": breakdowns,
        "filters": applied_filters,
        "filter_lists": filter_lists,
        "mode_details": mode_details,
    }


def build_metric_destinations(job_id: str, analysis: dict) -> dict:
    base_filters = analysis.get("filters", {})
    operation = analysis.get("dashboard", {}).get("operation", "business_analysis")
    destinations = {}
    for key, metric in analysis.get("metrics", {}).items():
        destinations[key] = {
            "href": f"/analysis/results/{job_id}?mode={operation}&category={base_filters.get('category', 'all')}&region={base_filters.get('region', 'all')}&year={base_filters.get('year', 'all')}&product={base_filters.get('product', 'all')}#{metric.get('detail_anchor', 'metric-breakdown')}",
            "label": metric.get("label", key),
            "insight": metric.get("insight", ""),
        }
    return destinations
