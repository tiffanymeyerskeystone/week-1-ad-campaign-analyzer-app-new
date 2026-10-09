from datetime import date
import unittest

import pandas as pd

from dashboard_data import (
    build_normalized_metric_trend,
    filter_campaign_data,
    prepare_campaign_data,
)


class CampaignDataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = pd.DataFrame(
            {
                "Campaign Name": ["Spring Launch", "Retargeting"],
                "Platform": ["Facebook", "Instagram"],
                "Date": ["2026-04-10", "2026-04-12"],
                "Acquisition_Cost": ["$1,245.00", "$500.50"],
                "Impressions": [10000, 5000],
                "Clicks": [250, 100],
                "Conversions": [20, 8],
                "Audience": ["New customers", "Returning customers"],
                "Campaign Goal": ["Awareness", "Conversions"],
                "conversion_value": ["$2,000.00", "$750.00"],
            }
        )

    def test_cleans_currency_dates_and_calculates_rates(self) -> None:
        data, has_conversion_value = prepare_campaign_data(self.raw)

        self.assertTrue(has_conversion_value)
        self.assertAlmostEqual(data.loc[0, "spend"], 1245.0)
        self.assertEqual(data.loc[0, "date"], pd.Timestamp("2026-04-10"))
        self.assertAlmostEqual(data.loc[0, "ctr"], 0.025)
        self.assertAlmostEqual(data.loc[0, "cpc"], 4.98)
        self.assertAlmostEqual(data.loc[0, "roi"], (2000 - 1245) / 1245)

    def test_roi_stays_unavailable_without_dollar_conversion_values(self) -> None:
        raw_without_values = self.raw.drop(columns=["conversion_value"])
        data, has_conversion_value = prepare_campaign_data(raw_without_values)

        self.assertFalse(has_conversion_value)
        self.assertTrue(data["roi"].isna().all())

    def test_global_filters_are_applied_together(self) -> None:
        data, _ = prepare_campaign_data(self.raw)
        filtered = filter_campaign_data(
            data,
            start_date=date(2026, 4, 11),
            end_date=date(2026, 4, 13),
            platforms=["Instagram"],
            audiences=["Returning customers"],
            campaign_goals=["Conversions"],
        )

        self.assertEqual(filtered["campaign_name"].tolist(), ["Retargeting"])

    def test_empty_filter_selection_returns_no_rows(self) -> None:
        data, _ = prepare_campaign_data(self.raw)
        filtered = filter_campaign_data(
            data,
            start_date=date(2026, 4, 1),
            end_date=date(2026, 4, 30),
            platforms=[],
            audiences=["New customers", "Returning customers"],
            campaign_goals=["Awareness", "Conversions"],
        )

        self.assertTrue(filtered.empty)

    def test_combined_metric_trend_scales_each_metric_to_zero_through_100(self) -> None:
        data, _ = prepare_campaign_data(self.raw)

        trend = build_normalized_metric_trend(data, weekly=False)

        self.assertEqual(set(trend["metric"]), {"Spend", "Clicks", "Conversions", "ROI"})
        self.assertEqual(len(trend), 8)
        for _, values in trend.groupby("metric")["normalized_value"]:
            self.assertAlmostEqual(float(values.min()), 0.0)
            self.assertAlmostEqual(float(values.max()), 100.0)
        spend_values = trend[trend["metric"] == "Spend"]["actual_display"].tolist()
        self.assertEqual(spend_values, ["$1,245.00", "$500.50"])

    def test_metric_filter_can_show_only_spend_and_conversions(self) -> None:
        data, _ = prepare_campaign_data(self.raw)

        trend = build_normalized_metric_trend(
            data,
            weekly=False,
            metrics=["Spend", "Conversions"],
        )

        self.assertEqual(set(trend["metric"]), {"Spend", "Conversions"})

    def test_constant_metric_trend_uses_middle_of_scale(self) -> None:
        data, _ = prepare_campaign_data(self.raw.iloc[[0, 0]].reset_index(drop=True))

        trend = build_normalized_metric_trend(data, weekly=False)

        self.assertTrue(trend["normalized_value"].eq(50.0).all())

    def test_combined_metric_trend_omits_roi_if_no_conversion_values_exist(self) -> None:
        raw_without_values = self.raw.drop(columns=["conversion_value"])
        data, _ = prepare_campaign_data(raw_without_values)

        trend = build_normalized_metric_trend(data, weekly=False)

        self.assertEqual(set(trend["metric"]), {"Spend", "Clicks", "Conversions"})


if __name__ == "__main__":
    unittest.main()
