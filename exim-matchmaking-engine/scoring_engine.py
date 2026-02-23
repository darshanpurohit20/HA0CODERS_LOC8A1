# =============================================================================
# scoring_engine.py — Multi-Criteria Weighted Scoring Engine
# =============================================================================
# For each (exporter, importer) pair this engine computes:
#   1. industry_match_score   (0–1)
#   2. intent_composite       (0–1)
#   3. reliability_score      (0–1)
#   4. geopolitical_safety    (0–1)
#   5. news_overlay_delta     (-0.4 to +0.4)
#   6. recency_weight         (0–1, multiplied at final step)
#   7. composite_score        (0–1, final rank value)
# Raw buyer fields are NEVER modified. All scoring is added as new fields.

import numpy as np
from config import (
    SCORING_WEIGHTS,
    INDUSTRY_ADJACENCY,
    INTENT_SIGNAL_WEIGHTS,
    RELIABILITY_WEIGHTS,
    GEOPOLITICAL_PENALTIES,
    CURRENCY_WEIGHT,
)


# ─── 1. INDUSTRY MATCH SCORE ─────────────────────────────────────────────────

def score_industry_match(exporter_industry: str, buyer_industry: str) -> tuple:
    """
    Returns (score: float, tag: str)
    - Exact match:    1.0, "exact"
    - Adjacent match: 0.5, "adjacent"
    - No match:       0.0, "none"
    """
    if not exporter_industry or not buyer_industry:
        return (0.3, "unknown")  # neutral if data missing

    exp_ind = str(exporter_industry).strip()
    buy_ind = str(buyer_industry).strip()

    if exp_ind == buy_ind:
        return (1.0, "exact")

    adjacent = INDUSTRY_ADJACENCY.get(exp_ind, [])
    if buy_ind in adjacent:
        return (0.5, "adjacent")

    return (0.0, "none")


# ─── 2. INTENT COMPOSITE SCORE ───────────────────────────────────────────────

def score_intent(buyer_row: dict) -> float:
    """
    Aggregates multiple buyer intent signals into a single 0–1 score.
    Uses weights from INTENT_SIGNAL_WEIGHTS config.
    """
    w = INTENT_SIGNAL_WEIGHTS

    raw_intent      = float(buyer_row.get("clean_intent_score", 0.3))
    engagement      = float(buyer_row.get("clean_engagement_spike", 0))
    funding         = float(buyer_row.get("clean_funding_event", 0.1))
    dm_change       = float(buyer_row.get("clean_decision_maker_change", 0))
    hiring          = float(buyer_row.get("clean_hiring_growth", 0))
    profile_visits  = float(buyer_row.get("norm_profile_visits", 0))

    composite = (
        raw_intent     * w["raw_intent_score"] +
        engagement     * w["engagement_spike"] +
        funding        * w["funding_event"] +
        dm_change      * w["decision_maker_change"] +
        hiring         * w["hiring_growth"] +
        profile_visits * w["profile_visits_norm"]
    )
    return float(np.clip(composite, 0, 1))


# ─── 3. RELIABILITY SCORE ────────────────────────────────────────────────────

def score_reliability(buyer_row: dict) -> float:
    """
    Combines payment history and prompt response rate.
    """
    w = RELIABILITY_WEIGHTS

    payment  = float(buyer_row.get("clean_good_payment", 0))
    response = float(buyer_row.get("clean_prompt_response", 0.5))

    composite = payment * w["payment_history"] + response * w["prompt_response"]
    return float(np.clip(composite, 0, 1))


# ─── 4. GEOPOLITICAL SAFETY SCORE ────────────────────────────────────────────

def score_geopolitical(buyer_row: dict) -> float:
    """
    Starts at 1.0 (perfectly safe) and subtracts penalties for each risk flag.
    Currency shift: positive = good for Indian exporter (earn more in INR terms),
    adds bonus; negative = adds risk.
    """
    safety = 1.0

    war      = float(buyer_row.get("clean_war_event", 0))
    calamity = float(buyer_row.get("clean_natural_calamity", 0))
    tariff   = float(buyer_row.get("clean_tariff_news", 0))
    shock    = float(buyer_row.get("clean_stock_shock", 0))
    currency = float(buyer_row.get("clean_currency_fluctuation", 0))

    safety -= war      * GEOPOLITICAL_PENALTIES["war_event"]
    safety -= calamity * GEOPOLITICAL_PENALTIES["natural_calamity"]
    safety -= tariff   * GEOPOLITICAL_PENALTIES["tariff_news"]
    safety -= shock    * GEOPOLITICAL_PENALTIES["stock_market_shock"]

    # Currency: clamp shift to [-1, 1] range, then apply weight as bonus/penalty
    currency_clamped = float(np.clip(currency, -1, 1))
    safety += currency_clamped * CURRENCY_WEIGHT

    return float(np.clip(safety, 0, 1))


# ─── 5. COMPOSITE SCORE ──────────────────────────────────────────────────────

def compute_composite_score(
    industry_score: float,
    intent_score: float,
    reliability_score: float,
    geo_score: float,
    news_delta: float,
    recency_weight: float,
    swipe_penalty: float = 1.0,
    pattern_penalty: float = 1.0,
) -> float:
    """
    Combines all sub-scores into one final composite score (0–1).

    Formula:
        base = weighted_sum(industry, intent, reliability, geo)
        adjusted = (base + news_delta) × recency_weight
        final = adjusted × swipe_penalty × pattern_penalty

    Args:
        industry_score:    0–1, how well industries match
        intent_score:      0–1, buyer intent signals
        reliability_score: 0–1, payment + response reliability
        geo_score:         0–1, geopolitical safety
        news_delta:        -0.4 to +0.4, news overlay boost/penalty
        recency_weight:    0–1, how fresh the buyer record is
        swipe_penalty:     0.05–1.0, left-swipe soft decay factor
        pattern_penalty:   0.7–1.0, pattern-learning penalty factor
    """
    w = SCORING_WEIGHTS

    base = (
        industry_score    * w["industry_match"] +
        intent_score      * w["intent_score"] +
        reliability_score * w["reliability_score"] +
        geo_score         * w["geopolitical_safety"]
    )

    # News overlay: added before recency weighting so news can both boost and cap
    base_with_news = float(np.clip(base + news_delta, 0, 1))

    # Recency: older records naturally score lower
    recency_adjusted = base_with_news * recency_weight

    # Swipe penalties: applied multiplicatively after all other scoring
    final = recency_adjusted * swipe_penalty * pattern_penalty

    return float(np.clip(final, 0, 1))


# ─── 6. FULL SCORE BREAKDOWN ─────────────────────────────────────────────────

def score_buyer_for_exporter(
    exporter_row: dict,
    buyer_row: dict,
    news_overlay: dict,
    swipe_state: dict = None,
) -> dict:
    """
    Master scoring function for one (exporter, buyer) pair.
    Returns a rich score document — all sub-scores + final composite + labels.
    This document is stored as a field in MongoDB's match collection.

    Args:
        exporter_row:  dict of cleaned exporter fields
        buyer_row:     dict of cleaned buyer fields
        news_overlay:  pre-built overlay dict from news_overlay.build_news_overlay()
        swipe_state:   dict with keys 'penalty_factor' and 'pattern_penalty'
                       from the swipe engine. Defaults to no penalty.

    Returns:
        dict with all scoring fields, ready for MongoDB insertion.
    """
    from news_overlay import get_news_delta, get_news_tags

    # ── Sub-scores ──
    industry_score_val, industry_tag = score_industry_match(
        exporter_row.get("Industry", ""),
        buyer_row.get("Industry", "")
    )
    intent_val      = score_intent(buyer_row)
    reliability_val = score_reliability(buyer_row)
    geo_val         = score_geopolitical(buyer_row)

    # ── News overlay ──
    buyer_country   = str(buyer_row.get("Country", ""))
    buyer_industry  = str(buyer_row.get("Industry", ""))
    news_delta_val  = get_news_delta(news_overlay, buyer_country, buyer_industry)

    # ── Recency ──
    recency_val = float(buyer_row.get("recency_weight", 0.5))

    # ── Swipe penalties ──
    swipe_state = swipe_state or {}
    swipe_pen   = float(swipe_state.get("penalty_factor", 1.0))
    pattern_pen = float(swipe_state.get("pattern_penalty", 1.0))

    # ── Final composite ──
    composite = compute_composite_score(
        industry_score    = industry_score_val,
        intent_score      = intent_val,
        reliability_score = reliability_val,
        geo_score         = geo_val,
        news_delta        = news_delta_val,
        recency_weight    = recency_val,
        swipe_penalty     = swipe_pen,
        pattern_penalty   = pattern_pen,
    )

    # ── Score tier label ──
    from data_loader import _get_score_tier
    tier_label = _get_score_tier(composite)

    # ── Explainability: build reason string ──
    reasons = []
    if industry_tag == "exact":
        reasons.append(f"✅ Exact industry match ({buyer_industry})")
    elif industry_tag == "adjacent":
        reasons.append(f"🔗 Adjacent industry — {exporter_row.get('Industry')} ↔ {buyer_industry}")
    else:
        reasons.append(f"❌ No industry overlap")

    if intent_val >= 0.7:
        reasons.append("🔥 High buyer intent — funding/hiring/engagement active")
    elif intent_val >= 0.4:
        reasons.append("📈 Moderate buyer intent signals")

    if reliability_val >= 0.7:
        reasons.append("💳 Strong payment & response track record")
    elif reliability_val < 0.4:
        reasons.append("⚠️ Reliability concerns — low payment/response history")

    if geo_val < 0.6:
        reasons.append(f"🌐 Geopolitical risk in {buyer_country} — trade caution advised")

    if news_delta_val > 0.05:
        reasons.append(f"📰 Recent news boosts opportunity (+{news_delta_val:.2f})")
    elif news_delta_val < -0.05:
        reasons.append(f"📰 Recent news indicates market risk ({news_delta_val:.2f})")

    if swipe_pen < 0.8:
        reasons.append(f"👈 Previous left-swipes apply penalty ({swipe_pen:.0%} factor)")

    return {
        # ── Identity ──
        "exporter_id":              exporter_row.get("Exporter_ID"),
        "buyer_id":                 buyer_row.get("Buyer_ID"),

        # ── Sub-scores (stored raw for UI display & re-ranking) ──
        "score_industry_match":     round(industry_score_val, 4),
        "score_intent":             round(intent_val, 4),
        "score_reliability":        round(reliability_val, 4),
        "score_geopolitical":       round(geo_val, 4),
        "score_news_delta":         round(news_delta_val, 4),
        "score_recency_weight":     round(recency_val, 4),

        # ── Penalty factors ──
        "swipe_penalty_factor":     round(swipe_pen, 4),
        "pattern_penalty_factor":   round(pattern_pen, 4),

        # ── Final score ──
        "composite_score":          round(composite, 4),

        # ── Display helpers ──
        "score_tier":               tier_label,
        "industry_match_tag":       industry_tag,
        "match_reasons":            reasons,

        # ── Metadata ──
        "scored_at":                str(np.datetime64("today")),
        "data_completeness":        round(float(buyer_row.get("data_completeness", 1.0)), 4),
    }
