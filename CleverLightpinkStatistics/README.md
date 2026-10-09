# Campaign Analytics

A Streamlit dashboard for exploring ad campaign performance in `campaign_data.csv`.

## Run locally

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 5000
```

Place `campaign_data.csv` in the project folder to load it automatically, or
upload a CSV from the sidebar for the current session. The app standardizes
campaign fields, parses dates, and cleans currency-formatted spend and
conversion-value fields.

## Tabs

- Overview
- Platform Performance
- Campaign Deep Dive
- Trends Over Time

The sidebar date, platform, audience, and campaign-goal filters apply across
all tabs. The dashboard calculates spend, impressions, clicks, conversions,
CTR, CPC, and ROI when dollar-valued conversion data is available.

ROI is calculated per campaign as `(conversion_value - spend) / spend` and
requires a dollar-valued `conversion_value` or `revenue` column. The supplied
`campaign_data.csv` now includes `conversion_value`; overview, platform, campaign,
and time-series ROI views all use the resulting campaign ROI values.

The Trends tab can show spend, clicks, conversions, and ROI together as distinct
colored lines. Each line is independently normalized to a 0–100 range for shape
comparison; hovering shows the metric's actual value and unit.
