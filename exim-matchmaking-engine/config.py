# =============================================================================
# config.py — Central Configuration for Swipe-to-Export Algorithm
# =============================================================================
# All weights, thresholds, and mappings are here. Tune without touching logic.

# ─── SCORING WEIGHTS ─────────────────────────────────────────────────────────
# Priority order: industry > intent > reliability > geopolitical
# Must sum to 1.0
SCORING_WEIGHTS = {
    "industry_match":      0.35,
    "intent_score":        0.30,
    "reliability_score":   0.20,
    "geopolitical_safety": 0.15,
}

# ─── INDUSTRY ADJACENCY MAP ──────────────────────────────────────────────────
# Defines which industries are "close enough" for partial match credit.
# Exact match = 1.0, Adjacent = 0.5, No relation = 0.0
INDUSTRY_ADJACENCY = {
    "Solar":          ["Engineering", "Electronics", "Chemicals"],
    "Medical Devices":["Pharmaceuticals", "Electronics", "Chemicals"],
    "IT Software":    ["Electronics", "Engineering"],
    "Machinery":      ["Engineering", "Auto Parts", "Chemicals"],
    "Textiles":       ["Chemicals"],
    "Pharmaceuticals":["Medical Devices", "Chemicals"],
    "Electronics":    ["IT Software", "Engineering", "Solar"],
    "Engineering":    ["Machinery", "Electronics", "Auto Parts"],
    "Chemicals":      ["Pharmaceuticals", "Solar", "Textiles", "Electronics"],
    "Auto Parts":     ["Machinery", "Engineering"],
}

# ─── INTENT SIGNAL WEIGHTS ───────────────────────────────────────────────────
# How much each buyer signal contributes to intent_composite (0–1 scale)
INTENT_SIGNAL_WEIGHTS = {
    "raw_intent_score":        0.25,   # Direct Intent_Score field from data
    "engagement_spike":        0.20,   # Engagement_Spike flag
    "funding_event":           0.20,   # Funding_Event (1=funded, Unknown=0.1)
    "decision_maker_change":   0.15,   # DecisionMaker_Change (new DM = opportunity)
    "hiring_growth":           0.10,   # Hiring_Growth flag
    "profile_visits_norm":     0.10,   # Normalized SalesNav_ProfileVisits
}

# ─── RELIABILITY SIGNAL WEIGHTS ──────────────────────────────────────────────
RELIABILITY_WEIGHTS = {
    "payment_history":    0.55,   # Good_Payment_History (binary)
    "prompt_response":    0.45,   # Prompt_Response (0–1 continuous)
}

# ─── GEOPOLITICAL RISK PENALTIES ─────────────────────────────────────────────
# Each flag that is TRUE subtracts this from the geopolitical safety score
# Safety starts at 1.0 and is penalized down
GEOPOLITICAL_PENALTIES = {
    "war_event":            0.35,
    "natural_calamity":     0.20,
    "tariff_news":          0.15,
    "stock_market_shock":   0.15,
}
# Currency: positive shift = good for Indian exporter (they earn more in INR)
# Applied as a bonus/penalty on top of base geopolitical score
CURRENCY_WEIGHT = 0.10  # how much currency_fluctuation influences geo score

# ─── GLOBAL NEWS OVERLAY ─────────────────────────────────────────────────────
# How much news events shift the final composite score
# Positive = boost, Negative = penalty
NEWS_EVENT_BASE_EFFECTS = {
    "Trade Agreement":    +0.12,   # New trade routes = opportunity
    "Tariff Update":      -0.08,   # Could mean barriers (sign-adjusted below)
    "Supply Chain Shock": -0.12,   # Disruption = risk
    "Stock Crash":        -0.08,   # Market instability
    "War Alert":          -0.18,   # Serious risk
    "Natural Calamity":   -0.10,   # Disruption risk
}

NEWS_IMPACT_MULTIPLIER = {
    "High":   1.0,
    "Medium": 0.6,
    "Low":    0.3,
}

# News recency decay: events older than this many days have reduced effect
NEWS_RECENCY_HALFLIFE_DAYS = 180

# ─── RECENCY DECAY ───────────────────────────────────────────────────────────
# How fast old buyer records lose relevance (exponential decay)
# Lambda: higher = faster decay. 0.001 ≈ ~2yr half-life
RECORD_RECENCY_LAMBDA = 0.001

# ─── SWIPE FEEDBACK ENGINE ───────────────────────────────────────────────────
# Option B: Soft Decay
SWIPE_LEFT_DECAY_FACTOR   = 0.60   # Each left swipe multiplies penalty by this
SWIPE_MIN_PENALTY_FLOOR   = 0.05   # Score never goes below 5% of original
SWIPE_RECOVERY_PER_WEEK   = 0.08   # Auto-recover this much per week without swipe
SWIPE_SIGNAL_RECOVERY     = 0.30   # Instant recovery if buyer gets new funding/DM change

# Option C: Pattern Learning
PATTERN_LEFT_THRESHOLD    = 3      # Min left swipes on same profile-type to flag pattern
PATTERN_PENALTY_FACTOR    = 0.30   # Reduce similar profiles' scores by this much
# Pattern dimensions: what makes two buyers "similar" for pattern learning
PATTERN_DIMENSIONS        = ["Country", "Industry"]  # Group by these fields

# ─── CARD DISPLAY THRESHOLDS ─────────────────────────────────────────────────
# Buyers below this composite score won't surface in the card deck
MIN_COMPOSITE_SCORE       = 0.10
# Buyers with this many left swipes from this exporter are suppressed
MAX_LEFT_SWIPES_BEFORE_HIDE = 5

# ─── RESPONSE CHANNEL COMPATIBILITY ──────────────────────────────────────────
# Exporters may prefer certain channels; matching boosts contact_readiness
CHANNEL_SCORE_IF_MATCH    = 1.0
CHANNEL_SCORE_IF_MISMATCH = 0.4

# ─── PROFILE VISIT NORMALIZATION ─────────────────────────────────────────────
# SalesNav_ProfileVisits is raw count — normalize against this max
PROFILE_VISITS_NORM_CAP   = 20000

# ─── SCORE LABELS ────────────────────────────────────────────────────────────
# Human-readable tier labels for the card UI
SCORE_TIERS = [
    (0.80, "🔥 Hot Match"),
    (0.60, "✅ Strong Fit"),
    (0.40, "🟡 Moderate"),
    (0.20, "🔵 Weak Fit"),
    (0.00, "⚠️ Low Priority"),
]
