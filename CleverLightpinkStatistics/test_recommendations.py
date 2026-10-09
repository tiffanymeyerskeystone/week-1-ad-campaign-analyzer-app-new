import unittest

import pandas as pd

from dashboard_data import prepare_campaign_data
from recommendations import build_performance_recommendations


class PerformanceRecommendationTests(unittest.TestCase):
    def test_full_campaign_dataset_returns_five_ordered_finding_action_pairs(self) -> None:
        raw = pd.read_csv("campaign_data.csv")
        campaigns, has_conversion_value = prepare_campaign_data(raw)

        recommendations = build_performance_recommendations(campaigns)

        self.assertTrue(has_conversion_value)
        self.assertEqual(len(recommendations), 5)
        self.assertTrue(all(item["finding"] and item["action"] for item in recommendations))
        self.assertIn("Brand Awareness", recommendations[0]["finding"])
        self.assertIn("Video Views", recommendations[1]["finding"])

    def test_empty_selection_returns_no_recommendations(self) -> None:
        self.assertEqual(build_performance_recommendations(pd.DataFrame()), [])


if __name__ == "__main__":
    unittest.main()
