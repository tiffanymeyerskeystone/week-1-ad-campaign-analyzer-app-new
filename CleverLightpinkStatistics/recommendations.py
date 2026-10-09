from __future__ import annotations

import pandas as pd


def _money(value: float) -> str:
    return f"${value:,.0f}"


def _percent(value: float) -> str:
    return f"{value:.1%}"


def _segment_summary(frame: pd.DataFrame, field: str) -> pd.DataFrame:
    summary = (
        frame.groupby(field, as_index=False)
        .agg(
            campaigns=("campaign_name", "size"),
            mean_roi=("roi", "mean"),
            spend=("spend", "sum"),
            conversion_value=("conversion_value", "sum"),
        )
    )
    return summary.sort_values("mean_roi", ascending=True)


def _goal_recommendations(frame: pd.DataFrame) -> list[dict[str, str]]:
    goals = _segment_summary(frame, "campaign_goal")
    recommendations = []
    for rank, (_, goal) in enumerate(goals.head(2).iterrows()):
        average_roi = float(goal["mean_roi"])
        net_value = float(goal["conversion_value"] - goal["spend"])
        rank_text = "lowest" if rank == 0 else "second-lowest"
        finding = (
            f"{goal['campaign_goal']} has the {rank_text} mean campaign ROI "
            f"({_percent(average_roi)}) across {int(goal['campaigns'])} campaigns. "
            f"It spent {_money(float(goal['spend']))} and generated "
            f"{_money(float(goal['conversion_value']))} in conversion value."
        )
        if net_value < 0:
            action = (
                "Cap new spend on this objective. Check conversion-value tracking, "
                "then rework the audience and creative; restart with a small test "
                "only after measured ROI improves."
            )
        else:
            action = (
                "Keep incremental spend limited. Test a revised audience or offer "
                "against the best-performing objective, and scale only if the test "
                "improves campaign ROI."
            )
        recommendations.append(
            {
                "title": f"Review {goal['campaign_goal']} campaigns",
                "finding": finding,
                "action": action,
            }
        )
    return recommendations


def _campaign_recommendation(frame: pd.DataFrame) -> dict[str, str] | None:
    campaigns = frame.copy()
    campaigns["dollar_shortfall"] = campaigns["spend"] - campaigns["conversion_value"]
    losing = campaigns[campaigns["dollar_shortfall"] > 0]
    if not losing.empty:
        campaign = losing.sort_values("dollar_shortfall", ascending=False).iloc[0]
        finding = (
            f"{campaign['campaign_name']} on {campaign['platform']} has the largest "
            f"dollar shortfall: {_money(float(campaign['dollar_shortfall']))} "
            f"({ _percent(float(campaign['roi'])) } ROI), after spending "
            f"{_money(float(campaign['spend']))} for "
            f"{_money(float(campaign['conversion_value']))} in conversion value."
        )
        action = (
            "Pause or sharply cap this campaign while you check tracking, targeting, "
            "and the offer. Relaunch only as a small, measured test with a clear "
            "ROI threshold."
        )
    else:
        campaign = campaigns.sort_values("roi", ascending=True).iloc[0]
        finding = (
            f"{campaign['campaign_name']} on {campaign['platform']} has the lowest "
            f"campaign ROI in this selection ({_percent(float(campaign['roi']))})."
        )
        action = (
            "Review its targeting and creative, then run a capped variation test "
            "before committing additional budget."
        )
    return {
        "title": "Address the weakest individual campaign",
        "finding": finding,
        "action": action,
    }


def _relative_segment_recommendation(
    summary: pd.DataFrame,
    *,
    field: str,
    noun: str,
) -> dict[str, str] | None:
    if len(summary) < 2:
        return None
    weakest = summary.iloc[0]
    strongest = summary.iloc[-1]
    weak_roi = float(weakest["mean_roi"])
    strong_roi = float(strongest["mean_roi"])
    positive_note = " It remains profitable on average." if weak_roi >= 0 else ""
    finding = (
        f"{weakest[field]} has the lowest mean campaign ROI among "
        f"{noun}s ({_percent(weak_roi)} across {int(weakest['campaigns'])} campaigns); "
        f"{strongest[field]} leads at {_percent(strong_roi)} across "
        f"{int(strongest['campaigns'])}.{positive_note}"
    )
    action = (
        f"Inspect the lowest-return {noun} campaigns individually. Run a controlled "
        f"creative or audience test against {strongest[field]} and move only a "
        "limited amount of budget if the measured ROI improves."
    )
    return {
        "title": f"Test the {weakest[field]} {noun}",
        "finding": finding,
        "action": action,
    }


def _additional_campaign_recommendations(
    frame: pd.DataFrame,
    already_named: set[str],
    limit: int,
) -> list[dict[str, str]]:
    recommendations = []
    for _, campaign in frame.sort_values("roi", ascending=True).iterrows():
        name = str(campaign["campaign_name"])
        if name in already_named:
            continue
        recommendations.append(
            {
                "title": f"Optimize {name}",
                "finding": (
                    f"{name} has a campaign ROI of "
                    f"{_percent(float(campaign['roi']))}, below the mean for this "
                    "filtered selection."
                ),
                "action": (
                    "Check its audience, creative, and conversion-value tracking. "
                    "Test one change at a time with a capped budget and keep it only "
                    "if ROI improves."
                ),
            }
        )
        already_named.add(name)
        if len(recommendations) == limit:
            break
    return recommendations


def build_performance_recommendations(
    frame: pd.DataFrame,
    limit: int = 5,
) -> list[dict[str, str]]:
    """Return data-backed ROI actions for the currently filtered campaign rows."""
    if frame.empty or limit <= 0:
        return []
    required = {"campaign_name", "platform", "campaign_goal", "audience",
                "spend", "conversion_value", "roi"}
    if not required.issubset(frame.columns):
        return []

    valid = frame.dropna(subset=["spend", "conversion_value", "roi"]).copy()
    if valid.empty:
        return []

    recommendations = _goal_recommendations(valid)
    campaign_recommendation = _campaign_recommendation(valid)
    if campaign_recommendation:
        recommendations.append(campaign_recommendation)

    platform_recommendation = _relative_segment_recommendation(
        _segment_summary(valid, "platform"),
        field="platform",
        noun="platform",
    )
    if platform_recommendation:
        recommendations.append(platform_recommendation)

    audience_recommendation = _relative_segment_recommendation(
        _segment_summary(valid, "audience"),
        field="audience",
        noun="audience",
    )
    if audience_recommendation:
        recommendations.append(audience_recommendation)

    named_campaigns = {
        str(value)
        for value in valid.loc[valid["spend"] > valid["conversion_value"], "campaign_name"]
    }
    if len(recommendations) < limit:
        recommendations.extend(
            _additional_campaign_recommendations(
                valid,
                named_campaigns,
                limit - len(recommendations),
            )
        )
    return recommendations[:limit]
