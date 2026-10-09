from __future__ import annotations

import re
from datetime import date

import pandas as pd


COLUMN_ALIASES = {
    "campaign_name": ("campaignname", "campaign"),
    "platform": ("platform", "channel"),
    "date": ("date", "startdate", "reportdate", "campaignstartdate"),
    "spend": ("acquisitioncost", "spend", "campaignspend", "adspend", "cost"),
    "impressions": ("impressions", "impression"),
    "clicks": ("clicks", "linkclicks", "click"),
    "conversions": ("conversions", "conversion", "purchases"),
    "audience": ("audience", "targetaudience"),
    "campaign_goal": ("campaigngoal", "goal", "objective"),
    "conversion_value": (
        "conversionvalue",
        "conversionsvalue",
        "revenue",
        "conversionrevenue",
        "purchasevalue",
        "salesvalue",
    ),
}

REQUIRED_FIELDS = (
    "campaign_name",
    "platform",
    "date",
    "spend",
    "impressions",
    "clicks",
    "conversions",
    "audience",
    "campaign_goal",
)


def _normalized_name(value: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def _resolve_columns(columns: list[object]) -> dict[str, object]:
    normalized = {_normalized_name(column): column for column in columns}
    resolved: dict[str, object] = {}
    for field, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                resolved[field] = normalized[alias]
                break
    return resolved


def _numeric_values(series: pd.Series, *, money: bool = False) -> pd.Series:
    values = series.astype("string").str.strip()
    if money:
        values = (
            values.str.replace(",", "", regex=False)
            .str.replace("$", "", regex=False)
            .str.replace("€", "", regex=False)
            .str.replace("£", "", regex=False)
            .str.replace(r"^\((.*)\)$", r"-\1", regex=True)
        )
    return pd.to_numeric(values, errors="coerce")


def _category_values(series: pd.Series) -> pd.Series:
    values = series.astype("string").str.strip()
    return values.mask(values.isna() | values.eq(""), "Unknown").astype(str)


def prepare_campaign_data(raw: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    """Standardize campaign fields, clean numeric values, and calculate row rates."""
    columns = _resolve_columns(list(raw.columns))
    missing = [field for field in REQUIRED_FIELDS if field not in columns]
    if missing:
        raise ValueError(
            "CSV is missing required fields: " + ", ".join(missing)
        )

    prepared = pd.DataFrame(index=raw.index)
    for field in ("campaign_name", "platform", "audience", "campaign_goal"):
        prepared[field] = _category_values(raw[columns[field]])

    try:
        prepared["date"] = pd.to_datetime(
            raw[columns["date"]], errors="coerce", format="mixed"
        )
    except (TypeError, ValueError):
        prepared["date"] = pd.to_datetime(raw[columns["date"]], errors="coerce")

    prepared["spend"] = _numeric_values(raw[columns["spend"]], money=True)
    for field in ("impressions", "clicks", "conversions"):
        prepared[field] = _numeric_values(raw[columns[field]])

    has_conversion_value = "conversion_value" in columns
    if has_conversion_value:
        prepared["conversion_value"] = _numeric_values(
            raw[columns["conversion_value"]], money=True
        )
    else:
        prepared["conversion_value"] = pd.Series(
            float("nan"), index=raw.index, dtype="float64"
        )

    prepared["ctr"] = prepared["clicks"].div(
        prepared["impressions"].where(prepared["impressions"].ne(0))
    )
    prepared["cpc"] = prepared["spend"].div(
        prepared["clicks"].where(prepared["clicks"].ne(0))
    )
    prepared["roi"] = (prepared["conversion_value"] - prepared["spend"]).div(
        prepared["spend"].where(prepared["spend"].ne(0))
    )
    return prepared.reset_index(drop=True), has_conversion_value


def filter_campaign_data(
    frame: pd.DataFrame,
    *,
    start_date: date | None,
    end_date: date | None,
    platforms: list[str],
    audiences: list[str],
    campaign_goals: list[str],
) -> pd.DataFrame:
    """Apply all dashboard-wide filters in one pass."""
    mask = pd.Series(True, index=frame.index)
    if start_date is not None and end_date is not None:
        dates = frame["date"].dt.date
        mask &= dates.between(start_date, end_date)
    mask &= frame["platform"].isin(platforms)
    mask &= frame["audience"].isin(audiences)
    mask &= frame["campaign_goal"].isin(campaign_goals)
    return frame.loc[mask].copy()


def sum_or_none(values: pd.Series) -> float | None:
    total = values.sum(min_count=1)
    return None if pd.isna(total) else float(total)


def build_normalized_metric_trend(
    frame: pd.DataFrame,
    *,
    weekly: bool,
    metrics: list[str] | None = None,
) -> pd.DataFrame:
    """Build long-form, independently normalized trends with readable actual values."""
    columns = ["period", "metric", "normalized_value", "actual_display"]
    dated = frame.dropna(subset=["date"]).copy()
    if dated.empty:
        return pd.DataFrame(columns=columns)

    if weekly:
        dated["_period"] = dated["date"].dt.to_period("W-SUN").dt.start_time
    else:
        dated["_period"] = dated["date"].dt.normalize()

    grouped = (
        dated.groupby("_period")
        .agg(
            Spend=("spend", "sum"),
            Clicks=("clicks", "sum"),
            Conversions=("conversions", "sum"),
            ROI=("roi", "mean"),
        )
        .sort_index()
    )
    rows: list[dict[str, object]] = []
    for metric in ("Spend", "Clicks", "Conversions", "ROI"):
        if metrics is not None and metric not in metrics:
            continue
        values = pd.to_numeric(grouped[metric], errors="coerce")
        valid_values = values.dropna()
        if valid_values.empty:
            continue

        minimum = float(valid_values.min())
        maximum = float(valid_values.max())
        if maximum == minimum:
            normalized = pd.Series(50.0, index=values.index)
        else:
            normalized = (values - minimum) * 100 / (maximum - minimum)

        for period, value in values.items():
            if pd.isna(value):
                continue
            if metric == "Spend":
                actual_display = f"${value:,.2f}"
            elif metric == "ROI":
                actual_display = f"{value:.2%}"
            else:
                actual_display = f"{value:,.0f}"
            rows.append(
                {
                    "period": period,
                    "metric": metric,
                    "normalized_value": float(normalized.loc[period]),
                    "actual_display": actual_display,
                }
            )

    return pd.DataFrame(rows, columns=columns)
