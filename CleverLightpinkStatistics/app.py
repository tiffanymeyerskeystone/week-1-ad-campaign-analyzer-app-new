from __future__ import annotations

from io import BytesIO
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from dashboard_data import (
    build_normalized_metric_trend,
    filter_campaign_data,
    prepare_campaign_data,
    sum_or_none,
)
from recommendations import build_performance_recommendations


DATA_PATH = Path(__file__).resolve().parent / "campaign_data.csv"
NAVY = "#0F3F6C"
PINK = "#F33996"
AQUA = "#09CCE1"
BLUSH = "#FEE2E5"
DARK_BLUSH = "#A13D62"
ALL_METRICS_OPTION = "All four metrics together"
METRIC_COLORS = {
    "Spend": NAVY,
    "Clicks": PINK,
    "Conversions": AQUA,
    "ROI": DARK_BLUSH,
}

st.set_page_config(
    page_title="Campaign Analytics",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background: #fff; color: #0F3F6C; }
    [data-testid="stSidebar"] { background: #FEE2E5; border-right: 1px solid rgba(243, 57, 150, .25); }
    .block-container { max-width: 1500px; padding-top: 3.2rem; }
    .dashboard-hero { background: #0F3F6C; border-radius: 14px; padding: 1.25rem 1.5rem; margin-bottom: .8rem; }
    .eyebrow { color: #09CCE1; text-transform: uppercase; letter-spacing: .15em; font-size: .69rem; font-weight: 700; }
    .page-title { color: #fff; font-size: 2.25rem; font-weight: 700; letter-spacing: -.055em; margin: .25rem 0 0; }
    .page-subtitle { color: #0F3F6C; font-size: .96rem; margin-bottom: 1rem; }
    [data-testid="stMain"] h4 {
        background: #0F3F6C;
        color: #fff !important;
        border-left: 4px solid #F33996;
        border-radius: 8px;
        padding: .55rem .8rem;
        margin-top: 1rem;
    }
    [data-testid="stMain"] h5 {
        color: #0F3F6C !important;
        border-left: 3px solid #09CCE1;
        padding-left: .6rem;
    }
    .stMarkdown, .stCaptionContainer, .stWidgetLabel, label { color: #0F3F6C; }
    .stCaptionContainer p { color: #0F3F6C; }
    .funnel-arrow { color: #F33996; font-size: 1.8rem; text-align: center; padding-top: 1.2rem; }
    div[data-testid="stMetric"] {
        background: #fff;
        border: 1px solid #FEE2E5;
        border-top: 3px solid #F33996;
        border-radius: 12px;
        padding: 13px 14px;
        min-height: 96px;
    }
    div[data-testid="stMetricLabel"] { font-size: .8rem; }
    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] > div {
        font-size: 1.2rem !important;
        line-height: 1.25;
        white-space: nowrap;
        overflow: visible;
        text-overflow: clip;
    }
    div[data-testid="stTabs"] div[role="tablist"] { background: transparent; border-bottom: 1px solid #FEE2E5; }
    div[data-testid="stTabs"] button[role="tab"] {
        color: #0F3F6C !important;
        font-weight: 600;
        border: 0;
        background: transparent;
    }
    div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
        color: #A13D62 !important;
        background: transparent !important;
        box-shadow: inset 0 -3px #F33996;
    }
    div[data-testid="stTabs"] button[role="tab"]:hover:not([aria-selected="true"]) {
        color: #0F3F6C !important;
        text-decoration: underline;
        text-decoration-color: #09CCE1;
    }
    .stButton > button[kind="primary"] {
        background: #fff;
        border-color: #F33996;
        color: #0F3F6C;
    }
    .stButton > button[kind="primary"]:hover { background: #FEE2E5; border-color: #F33996; color: #0F3F6C; }
    [data-baseweb="tag"] { background: #FEE2E5 !important; border: 1px solid #F33996; }
    [data-baseweb="tag"] span { color: #0F3F6C !important; }
    div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {
        border-color: #FEE2E5 !important;
    }
    div[data-baseweb="input"]:focus-within > div,
    div[data-baseweb="select"]:focus-within > div {
        border-color: #F33996 !important;
        box-shadow: 0 0 0 1px #F33996;
    }
    [data-testid="stFileUploaderDropzone"] {
        background: #fff;
        border: 1px dashed #F33996;
    }
    a { color: #A13D62; text-decoration-color: #F33996; }
    a:hover { color: #0F3F6C; text-decoration-color: #09CCE1; }
    div[data-testid="stAlert"] {
        background: #FEE2E5;
        border-color: #F33996;
        color: #0F3F6C;
        border-radius: 10px;
    }
    div[data-testid="stAlert"] p { color: #0F3F6C; }
    div[data-testid="stDataFrame"] { border: 1px solid #FEE2E5; border-radius: 12px; overflow: hidden; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #fff;
        border-color: #FEE2E5;
        border-radius: 12px;
    }
    .recommendation-label {
        display: inline-block;
        color: #0F3F6C;
        background: #FEE2E5;
        border-radius: 999px;
        padding: .22rem .65rem;
        margin: .2rem 0;
        font-size: .72rem;
        font-weight: 700;
        letter-spacing: .08em;
        text-transform: uppercase;
    }
    .recommendation-label.finding { border-left: 3px solid #F33996; }
    .recommendation-label.action { border-left: 3px solid #09CCE1; }
    hr { border-color: #FEE2E5; }
    </style>
    """,
    unsafe_allow_html=True,
)


def money(value: float | None) -> str:
    return "—" if value is None or pd.isna(value) else f"${value:,.2f}"


def count(value: float | None) -> str:
    return "—" if value is None or pd.isna(value) else f"{value:,.0f}"


def percent_ratio(value: float | None) -> str:
    return "—" if value is None or pd.isna(value) else f"{value:.2%}"


def ratio(numerator: float | None, denominator: float | None) -> float | None:
    if (
        numerator is None
        or denominator is None
        or pd.isna(numerator)
        or pd.isna(denominator)
        or denominator == 0
    ):
        return None
    return numerator / denominator


def line_chart(
    frame: pd.DataFrame,
    *,
    x_field: str,
    y_field: str,
    y_title: str,
    y_format: str,
    color: str,
    tooltip_format: str,
    height: int = 330,
) -> alt.TopLevelMixin:
    chart = (
        alt.Chart(frame)
        .mark_line(point=True, color=color, strokeWidth=2)
        .encode(
            x=alt.X(f"{x_field}:T", title=None),
            y=alt.Y(
                f"{y_field}:Q",
                title=y_title,
                axis=alt.Axis(format=y_format),
            ),
            tooltip=[
                alt.Tooltip(f"{x_field}:T", title="Date", format="%b %d, %Y"),
                alt.Tooltip(
                    f"{y_field}:Q",
                    title=y_title,
                    format=tooltip_format,
                ),
            ],
        )
        .properties(height=height)
    )
    return chart


def brand_chart(chart: alt.TopLevelMixin) -> alt.TopLevelMixin:
    """Apply the dashboard palette to chart labels, grids, legends, and surfaces."""
    return (
        chart.configure(background="#FFFFFF")
        .configure_axis(
            labelColor=NAVY,
            titleColor=NAVY,
            gridColor=BLUSH,
            domainColor=NAVY,
            tickColor=NAVY,
        )
        .configure_legend(labelColor=NAVY, titleColor=NAVY)
        .configure_view(stroke=BLUSH)
    )


def brand_table(frame: pd.DataFrame):
    """Style interactive dataframes with navy headers and blush row striping."""
    def body_styles(data: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame(
            [
                [
                    f"color: {NAVY}; background-color: "
                    f"{BLUSH if row_number % 2 else '#FFFFFF'}"
                    for _ in data.columns
                ]
                for row_number in range(len(data.index))
            ],
            index=data.index,
            columns=data.columns,
        )

    return (
        frame.style.apply(body_styles, axis=None).set_table_styles(
            [
                {
                    "selector": "th",
                    "props": [
                        ("background-color", NAVY),
                        ("color", "#FFFFFF"),
                        ("font-weight", "700"),
                        ("border-bottom", f"2px solid {PINK}"),
                    ],
                }
            ]
        )
    )


uploaded_file = st.sidebar.file_uploader(
    "Use another CSV for this session",
    type=["csv"],
    help="If no file is selected, the app reads campaign_data.csv from the project folder.",
)
source_name = uploaded_file.name if uploaded_file else DATA_PATH.name

try:
    if uploaded_file is not None:
        raw_data = pd.read_csv(BytesIO(uploaded_file.getvalue()))
    elif DATA_PATH.is_file():
        raw_data = pd.read_csv(DATA_PATH)
    else:
        st.error("campaign_data.csv was not found in the project folder.")
        st.stop()
    data, has_conversion_value = prepare_campaign_data(raw_data)
except (pd.errors.ParserError, UnicodeDecodeError, OSError, ValueError) as exc:
    st.error(f"Could not load campaign data: {exc}")
    st.stop()

st.sidebar.markdown('<div class="eyebrow">CAMPAIGN ANALYTICS</div>', unsafe_allow_html=True)
st.sidebar.markdown("### Dashboard filters")
st.sidebar.caption("Selections apply to every tab.")

valid_dates = data["date"].dropna()
selected_start: object | None = None
selected_end: object | None = None
if valid_dates.empty:
    st.sidebar.warning("No valid dates were found; date filtering is unavailable.")
else:
    minimum_date = valid_dates.min().date()
    maximum_date = valid_dates.max().date()
    date_selection = st.sidebar.date_input(
        "Date range",
        value=(minimum_date, maximum_date),
        min_value=minimum_date,
        max_value=maximum_date,
    )
    if isinstance(date_selection, (tuple, list)) and len(date_selection) == 2:
        selected_start, selected_end = date_selection
    else:
        selected_start, selected_end = minimum_date, maximum_date

platform_options = sorted(data["platform"].unique().tolist())
audience_options = sorted(data["audience"].unique().tolist())
goal_options = sorted(data["campaign_goal"].unique().tolist())

selected_platforms = st.sidebar.multiselect(
    "Platform",
    options=platform_options,
    default=platform_options,
)
selected_audiences = st.sidebar.multiselect(
    "Audience",
    options=audience_options,
    default=audience_options,
)
selected_goals = st.sidebar.multiselect(
    "Campaign goal",
    options=goal_options,
    default=goal_options,
)

invalid_date_count = int(data["date"].isna().sum())
if invalid_date_count:
    st.sidebar.caption(
        f"{invalid_date_count:,} row(s) with invalid dates are excluded from date-filtered results."
    )

# Compute once after all global filters are set. Every tab below uses this frame.
filtered_data = filter_campaign_data(
    data,
    start_date=selected_start,  # type: ignore[arg-type]
    end_date=selected_end,  # type: ignore[arg-type]
    platforms=selected_platforms,
    audiences=selected_audiences,
    campaign_goals=selected_goals,
)

st.markdown(
    '<div class="dashboard-hero"><div class="eyebrow">PAID MEDIA PERFORMANCE</div>'
    '<div class="page-title">Campaign Analytics</div></div>',
    unsafe_allow_html=True,
)
date_caption = (
    f"{selected_start:%b %d, %Y} — {selected_end:%b %d, %Y}"
    if selected_start is not None and selected_end is not None
    else "No valid date range"
)
st.markdown(
    f'<div class="page-subtitle">Loaded {source_name} · Showing '
    f'{len(filtered_data):,} of {len(data):,} campaigns · {date_caption}</div>',
    unsafe_allow_html=True,
)
if not has_conversion_value:
    st.info(
        "ROI needs a dollar-valued conversion_value or revenue column. "
        "This CSV contains conversion counts only, so ROI is left unavailable."
    )

overview_tab, platform_tab, campaign_tab, trends_tab, recommendations_tab = st.tabs(
    [
        "Overview",
        "Platform Performance",
        "Campaign Deep Dive",
        "Trends Over Time",
        "Recommendations",
    ]
)

if filtered_data.empty:
    st.warning("No data for selected filters.")

with overview_tab:
    if filtered_data.empty:
        st.info("No data for selected filters.")
    else:
        total_spend = sum_or_none(filtered_data["spend"])
        total_impressions = sum_or_none(filtered_data["impressions"])
        total_clicks = sum_or_none(filtered_data["clicks"])
        total_conversions = sum_or_none(filtered_data["conversions"])
        average_ctr = ratio(total_clicks, total_impressions)
        average_cpc = ratio(total_spend, total_clicks)
        average_roi = (
            float(filtered_data["roi"].mean())
            if has_conversion_value and filtered_data["roi"].notna().any()
            else None
        )

        metric_columns = st.columns(5)
        metrics = [
            ("Total Spend", money(total_spend), "Across filtered campaigns"),
            ("Conversions", count(total_conversions), "Total conversions (count)"),
            ("Average CTR", percent_ratio(average_ctr), "Clicks ÷ impressions"),
            ("Average CPC", money(average_cpc), "Spend ÷ clicks"),
            (
                "Average ROI",
                percent_ratio(average_roi),
                "Unavailable without conversion values" if not has_conversion_value else "Mean campaign ROI",
            ),
        ]
        for column, (label, value, help_text) in zip(metric_columns, metrics):
            with column:
                st.metric(label, value, help=help_text)

        st.markdown("#### Spend and conversions over time")
        daily = (
            filtered_data.dropna(subset=["date"])
            .groupby("date", as_index=False)
            .agg(spend=("spend", "sum"), conversions=("conversions", "sum"))
            .sort_values("date")
        )
        if daily.empty:
            st.info("No valid dates are available for the selected filters.")
        else:
            st.markdown(
                f'<span style="color:{NAVY};font-weight:700">● Spend ($)</span>'
                f'&nbsp;&nbsp; <span style="color:{AQUA};font-weight:700">● Conversions (count)</span>'
                '<span style="color:#0F3F6C"> · Each series uses its own axis.</span>',
                unsafe_allow_html=True,
            )
            x_encoding = alt.X("date:T", title=None)
            spend_line = (
                alt.Chart(daily)
                .mark_line(color=NAVY, strokeWidth=2)
                .encode(
                    x=x_encoding,
                    y=alt.Y(
                        "spend:Q",
                        title="Spend ($)",
                        axis=alt.Axis(format="$,.0f"),
                    ),
                    tooltip=[
                        alt.Tooltip("date:T", title="Date", format="%b %d, %Y"),
                        alt.Tooltip("spend:Q", title="Spend", format="$,.2f"),
                    ],
                )
            )
            conversion_line = (
                alt.Chart(daily)
                .mark_line(color=AQUA, strokeWidth=2)
                .encode(
                    x=x_encoding,
                    y=alt.Y(
                        "conversions:Q",
                        title="Conversions",
                        axis=alt.Axis(orient="right", format=",.0f"),
                    ),
                    tooltip=[
                        alt.Tooltip("date:T", title="Date", format="%b %d, %Y"),
                        alt.Tooltip("conversions:Q", title="Conversions", format=",.0f"),
                    ],
                )
            )
            chart = (
                alt.layer(spend_line, conversion_line)
                .resolve_scale(y="independent")
                .properties(height=340)
            )
            st.altair_chart(brand_chart(chart), width="stretch")

with platform_tab:
    if filtered_data.empty:
        st.info("No data for selected filters.")
    else:
        st.markdown("#### Platform comparison")
        platform_summary = (
            filtered_data.groupby("platform", as_index=False)
            .agg(
                spend=("spend", "sum"),
                clicks=("clicks", "sum"),
                conversions=("conversions", "sum"),
                average_roi=("roi", "mean"),
            )
            .sort_values("spend", ascending=False)
        )
        spend_chart, roi_chart = st.columns(2)
        with spend_chart:
            st.markdown("##### Total spend by platform")
            spend_bars = (
                alt.Chart(platform_summary)
                .mark_bar(color=NAVY, cornerRadiusEnd=4)
                .encode(
                    x=alt.X("platform:N", sort="-y", title=None, axis=alt.Axis(labelAngle=-25)),
                    y=alt.Y("spend:Q", title="Spend ($)", axis=alt.Axis(format="$,.0f")),
                    tooltip=[
                        alt.Tooltip("platform:N", title="Platform"),
                        alt.Tooltip("spend:Q", title="Spend", format="$,.2f"),
                    ],
                )
                .properties(height=300)
            )
            st.altair_chart(brand_chart(spend_bars), width="stretch")
        with roi_chart:
            st.markdown("##### Average ROI by platform")
            if not has_conversion_value:
                st.info("Add dollar-valued conversion data to compare ROI.")
            elif platform_summary["average_roi"].notna().any():
                roi_bars = (
                    alt.Chart(platform_summary.dropna(subset=["average_roi"]))
                    .mark_bar(color=METRIC_COLORS["ROI"], cornerRadiusEnd=4)
                    .encode(
                        x=alt.X("platform:N", sort="-y", title=None, axis=alt.Axis(labelAngle=-25)),
                        y=alt.Y(
                            "average_roi:Q",
                            title="Average ROI",
                            axis=alt.Axis(format=".1%"),
                        ),
                        tooltip=[
                            alt.Tooltip("platform:N", title="Platform"),
                            alt.Tooltip("average_roi:Q", title="Average ROI", format=".2%"),
                        ],
                    )
                    .properties(height=300)
                )
                st.altair_chart(brand_chart(roi_bars), width="stretch")
            else:
                st.info("No ROI values are available for the selected filters.")

        st.markdown("#### Platform summary")
        summary_table = platform_summary[
            ["platform", "spend", "clicks", "conversions", "average_roi"]
        ].rename(
            columns={
                "platform": "Platform",
                "spend": "Spend ($)",
                "clicks": "Clicks",
                "conversions": "Conversions",
                "average_roi": "ROI (%)",
            }
        )
        summary_table["ROI (%)"] = summary_table["ROI (%)"] * 100
        st.dataframe(
            brand_table(summary_table),
            hide_index=True,
            width="stretch",
            column_config={
                "Spend ($)": st.column_config.NumberColumn(format="$%.2f"),
                "Clicks": st.column_config.NumberColumn(format="%.0f"),
                "Conversions": st.column_config.NumberColumn(format="%.0f"),
                "ROI (%)": st.column_config.NumberColumn(
                    format="%.2f%%",
                    help="Unavailable until dollar-valued conversion data is supplied."
                    if not has_conversion_value
                    else None,
                ),
            },
        )

with campaign_tab:
    if filtered_data.empty:
        st.info("No data for selected filters.")
    else:
        st.markdown("#### Campaign search and details")
        search_text = st.text_input(
            "Search campaign names",
            placeholder="Type a campaign name…",
        )
        campaign_rows = filtered_data
        if search_text:
            campaign_rows = filtered_data[
                filtered_data["campaign_name"].str.contains(
                    search_text, case=False, regex=False, na=False
                )
            ]
        if campaign_rows.empty:
            st.info("No campaigns match your search.")
        else:
            visible_fields = [
                "campaign_name",
                "platform",
                "date",
                "spend",
                "impressions",
                "clicks",
                "conversions",
            ]
            if has_conversion_value:
                visible_fields.append("conversion_value")
            visible_fields.extend(
                ["ctr", "cpc", "roi", "audience", "campaign_goal"]
            )
            campaign_table = campaign_rows[visible_fields].copy()
            campaign_table = campaign_table.rename(
                columns={
                    "campaign_name": "Campaign",
                    "platform": "Platform",
                    "date": "Date",
                    "spend": "Spend ($)",
                    "impressions": "Impressions",
                    "clicks": "Clicks",
                    "conversions": "Conversions",
                    "conversion_value": "Conversion Value ($)",
                    "ctr": "CTR (%)",
                    "cpc": "CPC ($)",
                    "roi": "ROI (%)",
                    "audience": "Audience",
                    "campaign_goal": "Campaign Goal",
                }
            )
            campaign_table["CTR (%)"] = campaign_table["CTR (%)"] * 100
            campaign_table["ROI (%)"] = campaign_table["ROI (%)"] * 100
            column_config = {
                "Date": st.column_config.DateColumn(format="MMM D, YYYY"),
                "Spend ($)": st.column_config.NumberColumn(format="$%.2f"),
                "Impressions": st.column_config.NumberColumn(format="%.0f"),
                "Clicks": st.column_config.NumberColumn(format="%.0f"),
                "Conversions": st.column_config.NumberColumn(format="%.0f"),
                "CTR (%)": st.column_config.NumberColumn(format="%.2f%%"),
                "CPC ($)": st.column_config.NumberColumn(format="$%.2f"),
                "ROI (%)": st.column_config.NumberColumn(
                    format="%.2f%%",
                    help="Unavailable until dollar-valued conversion data is supplied."
                    if not has_conversion_value
                    else None,
                ),
            }
            if has_conversion_value:
                column_config["Conversion Value ($)"] = (
                    st.column_config.NumberColumn(format="$%.2f")
                )
            st.caption(
                f"Showing {len(campaign_rows):,} of {len(filtered_data):,} filtered campaigns. "
                "Click a column header to sort."
            )
            st.dataframe(
                brand_table(campaign_table),
                hide_index=True,
                width="stretch",
                height=420,
                column_config=column_config,
            )

        st.markdown("#### Conversion funnel")
        total_impressions = sum_or_none(filtered_data["impressions"])
        total_clicks = sum_or_none(filtered_data["clicks"])
        total_conversions = sum_or_none(filtered_data["conversions"])
        click_through_rate = ratio(total_clicks, total_impressions)
        click_conversion_rate = ratio(total_conversions, total_clicks)
        funnel_columns = st.columns([1, 0.18, 1, 0.18, 1])
        with funnel_columns[0]:
            st.metric("Impressions", count(total_impressions))
        with funnel_columns[1]:
            st.markdown('<div class="funnel-arrow">→</div>', unsafe_allow_html=True)
        with funnel_columns[2]:
            st.metric("Clicks", count(total_clicks))
            st.caption(f"{percent_ratio(click_through_rate)} of impressions")
        with funnel_columns[3]:
            st.markdown('<div class="funnel-arrow">→</div>', unsafe_allow_html=True)
        with funnel_columns[4]:
            st.metric("Conversions", count(total_conversions))
            st.caption(f"{percent_ratio(click_conversion_rate)} of clicks")

with trends_tab:
    if filtered_data.empty:
        st.info("No data for selected filters.")
    else:
        st.markdown("#### Trends over time")
        selected_metric = st.selectbox(
            "Metric",
            [ALL_METRICS_OPTION, "Clicks", "Conversions", "ROI"],
            help=(
                "Trends are grouped weekly when the selected date range exceeds "
                "two months. The combined view scales each metric from 0 to 100 "
                "within the selected range."
            ),
        )
        if selected_metric == "ROI" and not has_conversion_value:
            st.info("ROI trends need a dollar-valued conversion_value or revenue column.")
        else:
            if selected_start is not None and selected_end is not None:
                selected_span = (selected_end - selected_start).days  # type: ignore[operator]
            elif not valid_dates.empty:
                selected_span = (valid_dates.max() - valid_dates.min()).days
            else:
                selected_span = 0
            weekly = selected_span > 62
            grouping_label = "week" if weekly else "day"

            if selected_metric == ALL_METRICS_OPTION:
                selected_metrics = st.multiselect(
                    "Metrics to display",
                    options=list(METRIC_COLORS),
                    default=["Spend", "Conversions"],
                    help=(
                        "Spend and Conversions are selected by default. Add or remove "
                        "lines to change the comparison."
                    ),
                )
                trend = build_normalized_metric_trend(
                    filtered_data,
                    weekly=weekly,
                    metrics=selected_metrics,
                )
                if (
                    "ROI" in selected_metrics
                    and (not has_conversion_value or "ROI" not in set(trend["metric"]))
                ):
                    st.info(
                        "ROI is unavailable without valid dollar-valued conversion data; "
                        "the other available metrics are still shown."
                    )
                if not selected_metrics:
                    st.info("Select at least one metric to display.")
                elif trend.empty:
                    st.info("No dated metric values for the selected filters.")
                else:
                    all_metrics_chart = (
                        alt.Chart(trend)
                        .mark_line(point=True, strokeWidth=2)
                        .encode(
                            x=alt.X(
                                "period:T",
                                title=grouping_label.title(),
                                axis=alt.Axis(format="%b %d, %Y"),
                            ),
                            y=alt.Y(
                                "normalized_value:Q",
                                title="Relative index (0–100)",
                                scale=alt.Scale(domain=[0, 100]),
                                axis=alt.Axis(values=[0, 25, 50, 75, 100]),
                            ),
                            color=alt.Color(
                                "metric:N",
                                title="Metric",
                                scale=alt.Scale(
                                    domain=list(METRIC_COLORS),
                                    range=list(METRIC_COLORS.values()),
                                ),
                                legend=alt.Legend(
                                    orient="top",
                                    direction="horizontal",
                                    columns=min(4, trend["metric"].nunique()),
                                ),
                            ),
                            tooltip=[
                                alt.Tooltip(
                                    "period:T",
                                    title=grouping_label.title(),
                                    format="%b %d, %Y",
                                ),
                                alt.Tooltip("metric:N", title="Metric"),
                                alt.Tooltip(
                                    "actual_display:N",
                                    title="Actual value",
                                ),
                                alt.Tooltip(
                                    "normalized_value:Q",
                                    title="Relative index",
                                    format=".0f",
                                ),
                            ],
                        )
                        .properties(height=360)
                    )
                    st.caption(
                        f"Each line is scaled independently from 0 to 100 across "
                        f"the selected {grouping_label}s. Compare trend shape, not "
                        "absolute size; hover over a point to see the actual value."
                    )
                    st.altair_chart(brand_chart(all_metrics_chart), width="stretch")
            else:
                trend_source = filtered_data.dropna(subset=["date"]).copy()
                if weekly:
                    trend_source["_period"] = (
                        trend_source["date"].dt.to_period("W-SUN").dt.start_time
                    )
                else:
                    trend_source["_period"] = trend_source["date"].dt.normalize()

                metric_field = {
                    "Clicks": "clicks",
                    "Conversions": "conversions",
                    "ROI": "roi",
                }[selected_metric]
                aggregation = "mean" if selected_metric == "ROI" else "sum"
                trend = (
                    trend_source.groupby("_period", as_index=False)
                    .agg(value=(metric_field, aggregation))
                    .sort_values("_period")
                    .rename(columns={"_period": "period"})
                )
                if trend.empty or trend["value"].dropna().empty:
                    st.info(f"No {selected_metric.lower()} values for the selected filters.")
                else:
                    is_roi = selected_metric == "ROI"
                    chart = line_chart(
                        trend,
                        x_field="period",
                        y_field="value",
                        y_title="ROI" if is_roi else f"{selected_metric} (count)",
                        y_format=".1%" if is_roi else ",.0f",
                        tooltip_format=".2%" if is_roi else ",.0f",
                        color=METRIC_COLORS[selected_metric],
                        height=360,
                    )
                    st.caption(f"{selected_metric} grouped by {grouping_label}.")
                    st.altair_chart(brand_chart(chart), width="stretch")

with recommendations_tab:
    if filtered_data.empty:
        st.info("No data for selected filters.")
    elif not has_conversion_value:
        st.info(
            "Performance recommendations need a dollar-valued conversion_value "
            "or revenue column."
        )
    else:
        st.markdown("#### Five actions based on this selection")
        st.caption(
            "Findings use campaign ROI from conversion value and spend. "
            "Platform and audience differences are opportunities to test, not proof of cause."
        )
        recommendations = build_performance_recommendations(filtered_data)
        if len(recommendations) < 5:
            st.info(
                f"Only {len(recommendations)} distinct recommendations are supported "
                "by the current filtered data."
            )
        for number, recommendation in enumerate(recommendations, start=1):
            with st.container(border=True):
                st.markdown(f"##### {number}. {recommendation['title']}")
                st.markdown(
                    '<div class="recommendation-label finding">Finding</div>',
                    unsafe_allow_html=True,
                )
                st.write(recommendation["finding"])
                st.markdown(
                    '<div class="recommendation-label action">Do now</div>',
                    unsafe_allow_html=True,
                )
                st.write(recommendation["action"])
            if number < len(recommendations):
                st.divider()
