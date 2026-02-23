# =============================================================================
# news_overlay.py — Global News Risk & Opportunity Overlay
# =============================================================================
# Takes a cleaned news DataFrame and computes, for any (country, industry),
# a net overlay delta that will be added to / subtracted from the composite score.
# Positive delta = trade opportunity. Negative delta = risk penalty.

import pandas as pd
import numpy as np
from config import (
    NEWS_EVENT_BASE_EFFECTS,
    NEWS_IMPACT_MULTIPLIER,
    NEWS_RECENCY_HALFLIFE_DAYS,
)

# Region → Country group mapping for matching news region to buyer country
REGION_COUNTRY_MAP = {
    "Global":        None,   # affects every country
    "Asia":          ["Japan", "China", "India", "Singapore", "South Korea", "Vietnam"],
    "Europe":        ["Germany", "France", "Netherlands", "UK", "Italy", "Spain"],
    "North America": ["USA", "Canada", "Mexico"],
    "Middle East":   ["UAE", "Saudi Arabia", "Israel", "Iran", "Qatar"],
    "Africa":        ["Nigeria", "South Africa", "Kenya", "Egypt"],
    "South America": ["Brazil", "Argentina", "Colombia", "Chile"],
    "Oceania":       ["Australia", "New Zealand"],
}


def _country_in_region(country: str, region: str) -> bool:
    """Check if a buyer country falls under a news region."""
    if region == "Global":
        return True
    countries = REGION_COUNTRY_MAP.get(region, [])
    return country in countries


def _recency_multiplier(recency_weight: float) -> float:
    """
    Convert a record's exponential recency weight to a news overlay multiplier.
    Older news has less impact on current recommendations.
    """
    return float(recency_weight)


def build_news_overlay(news_df: pd.DataFrame) -> dict:
    """
    Pre-compute a nested lookup dict:
        overlay[(country, industry)] → net_delta (float, -1 to +1)
    
    This is called ONCE at startup and cached. When scoring a buyer,
    we just do overlay.get((buyer_country, buyer_industry), 0.0)
    """
    overlay = {}  # key: (country, industry) → accumulated delta

    for _, row in news_df.iterrows():
        event_type       = row.get("Event_Type", "")
        affected_industry= row.get("Affected_Industry", "")
        region           = row.get("Region", "Global")
        impact_level     = row.get("Impact_Level", "Medium")
        recency_w        = row.get("recency_weight", 0.5)
        tariff_change    = row.get("clean_tariff_change", 0)
        war_flag         = row.get("clean_war_flag", 0)
        calamity_flag    = row.get("clean_calamity_flag", 0)

        # ── Base effect from event type ──
        base_effect = NEWS_EVENT_BASE_EFFECTS.get(event_type, 0.0)

        # ── For Tariff Update: sign depends on tariff direction ──
        # Positive tariff_change = new tariff barriers = bad for exporter
        # Negative tariff_change = tariff removed = good for exporter
        if event_type == "Tariff Update":
            base_effect = -abs(base_effect) * np.sign(tariff_change) if tariff_change != 0 else base_effect

        # ── For Trade Agreement: boost if no war / calamity in same event ──
        if event_type == "Trade Agreement":
            if war_flag > 0.5:
                base_effect *= 0.5  # diminish if war ongoing in same region

        # ── Scale by impact level and recency ──
        impact_mult  = NEWS_IMPACT_MULTIPLIER.get(impact_level, 0.6)
        final_delta  = base_effect * impact_mult * recency_w

        # ── Determine which (country, industry) pairs this news affects ──
        affected_countries = REGION_COUNTRY_MAP.get(region, []) if region != "Global" else ["__ALL__"]

        if region == "Global":
            # Mark with special sentinel; matched against any country
            key = ("__GLOBAL__", affected_industry)
            overlay[key] = overlay.get(key, 0.0) + final_delta
        else:
            for country in affected_countries:
                key = (country, affected_industry)
                overlay[key] = overlay.get(key, 0.0) + final_delta

    # ── Clip accumulated delta to [-0.40, +0.40] to avoid dominating score ──
    overlay = {k: float(np.clip(v, -0.40, 0.40)) for k, v in overlay.items()}
    return overlay


def get_news_delta(overlay: dict, buyer_country: str, buyer_industry: str) -> float:
    """
    Look up the news overlay delta for a specific buyer.
    Checks both exact (country, industry) match AND global industry events.
    Returns the sum of matched overlays (clipped to [-0.40, +0.40]).
    """
    exact_key    = (buyer_country, buyer_industry)
    global_key   = ("__GLOBAL__", buyer_industry)

    delta = overlay.get(exact_key, 0.0) + overlay.get(global_key, 0.0)
    return float(np.clip(delta, -0.40, 0.40))


def get_news_tags(news_df: pd.DataFrame, buyer_country: str, buyer_industry: str) -> list:
    """
    Return a list of human-readable news tags for the buyer card UI.
    E.g. ["⚠️ War Alert in Asia affecting Machinery", "📈 Trade Agreement for Textiles"]
    """
    tags = []
    for _, row in news_df.iterrows():
        region   = row.get("Region", "Global")
        industry = row.get("Affected_Industry", "")
        event    = row.get("Event_Type", "")
        impact   = row.get("Impact_Level", "Medium")
        recency_w= row.get("recency_weight", 0)

        # Only surface reasonably recent news
        if recency_w < 0.2:
            continue

        industry_match = (industry == buyer_industry)
        country_match  = _country_in_region(buyer_country, region)

        if not (industry_match and country_match):
            continue

        emoji_map = {
            "Trade Agreement":    "📈",
            "Tariff Update":      "📋",
            "Supply Chain Shock": "⛓️",
            "Stock Crash":        "📉",
            "War Alert":          "⚠️",
            "Natural Calamity":   "🌪️",
        }
        emoji = emoji_map.get(event, "🔔")
        tags.append(f"{emoji} {impact} impact: {event} in {region} affecting {industry}")

    return tags
