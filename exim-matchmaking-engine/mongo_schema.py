# =============================================================================
# mongo_schema.py — MongoDB Document Builders
# =============================================================================
# Converts cleaned DataFrames → MongoDB-ready documents.
# Raw fields ALWAYS preserved. Computed fields are added alongside.
#
# COLLECTIONS DESIGNED:
#   1. buyers              — enriched importer profiles
#   2. exporters           — enriched exporter profiles
#   3. match_scores        — per (exporter, buyer) scored pairs
#   4. swipe_events        — raw swipe log (append-only)
#   5. exporter_swipe_state — per (exporter, buyer) B+C swipe state
#   6. exporter_preference_vectors — per-exporter learned patterns (C)
#   7. news_events         — processed news with overlay deltas

import pandas as pd
import numpy as np


def build_buyer_document(row: pd.Series) -> dict:
    """
    Builds a MongoDB buyer document from a cleaned importer row.
    Keeps ALL original CSV columns + adds computed_ prefix fields.
    """
    raw = row.to_dict()
    
    # Keep everything raw — convert NaN to None for JSON safety
    cleaned_raw = {}
    for k, v in raw.items():
        if isinstance(v, float) and np.isnan(v):
            cleaned_raw[k] = None
        else:
            cleaned_raw[k] = v

    # Build document
    doc = {
        # ── Primary key ──
        "_id":        raw.get("Buyer_ID"),          # MongoDB _id = Buyer_ID
        "record_id":  raw.get("Record_ID"),

        # ── Raw fields (exact from CSV, never modified) ──
        "raw": cleaned_raw,

        # ── Computed fields (algorithm outputs) ──
        "computed": {
            "market_momentum_score":   raw.get("market_momentum_score"),
            "contact_readiness_score": raw.get("contact_readiness_score"),
            "buyer_activity_tier":     raw.get("buyer_activity_tier"),
            "recency_weight":          raw.get("recency_weight"),
            "data_completeness":       raw.get("data_completeness"),
            "norm_profile_visits":     raw.get("norm_profile_visits"),

            # Clean versions of key fields (for safe querying)
            "clean_intent_score":      raw.get("clean_intent_score"),
            "clean_good_payment":      raw.get("clean_good_payment"),
            "clean_prompt_response":   raw.get("clean_prompt_response"),
            "clean_hiring_growth":     raw.get("clean_hiring_growth"),
            "clean_funding_event":     raw.get("clean_funding_event"),
            "clean_engagement_spike":  raw.get("clean_engagement_spike"),
            "clean_decision_maker_change": raw.get("clean_decision_maker_change"),
            "clean_war_event":         raw.get("clean_war_event"),
            "clean_natural_calamity":  raw.get("clean_natural_calamity"),
            "clean_tariff_news":       raw.get("clean_tariff_news"),
            "clean_stock_shock":       raw.get("clean_stock_shock"),
            "clean_currency_fluctuation": raw.get("clean_currency_fluctuation"),
        },

        # ── Swipe feedback state placeholder (updated by swipe_engine) ──
        # This is the per-exporter state embedded or referenced
        # In production: exporter_swipe_state is a separate collection
        "swipe_summary": {
            "total_right_swipes": 0,
            "total_left_swipes":  0,
        },

        # ── Index-friendly top-level fields (for fast card queries) ──
        "country":   raw.get("Country"),
        "industry":  raw.get("Industry"),
        "date":      raw.get("Date"),
        "channel":   raw.get("clean_channel"),
    }
    return doc


def build_exporter_document(row: pd.Series) -> dict:
    """
    Builds a MongoDB exporter document from a cleaned exporter row.
    """
    raw = row.to_dict()
    cleaned_raw = {}
    for k, v in raw.items():
        if isinstance(v, float) and np.isnan(v):
            cleaned_raw[k] = None
        else:
            cleaned_raw[k] = v

    doc = {
        "_id":        raw.get("Exporter_ID"),
        "record_id":  raw.get("Record_ID"),

        "raw": cleaned_raw,

        "computed": {
            "recency_weight":          raw.get("recency_weight"),
            "capacity_tier":           raw.get("capacity_tier"),
            "exporter_reliability":    raw.get("exporter_reliability"),
            "clean_intent_score":      raw.get("clean_intent_score"),
            "clean_manufacturing_cap": raw.get("clean_manufacturing_capacity"),
            "clean_prompt_response":   raw.get("clean_prompt_response_score"),
            "clean_good_payment_terms":raw.get("clean_good_payment_terms"),
        },

        # ── Swipe preference vector (updated by swipe_engine option C) ──
        "preference_vector": {
            "left_patterns":  {},
            "right_patterns": {},
        },

        # ── Top-level index fields ──
        "state":    raw.get("State"),
        "industry": raw.get("Industry"),
        "date":     raw.get("Date"),
        "msme":     raw.get("clean_msme"),
    }
    return doc


def build_match_score_document(score_dict: dict) -> dict:
    """
    Builds a MongoDB match_scores document for one (exporter, buyer) pair.
    Designed for fast lookup: indexed on exporter_id + composite_score DESC.
    """
    return {
        # ── Compound key (no separate _id — let MongoDB generate) ──
        "exporter_id":   score_dict["exporter_id"],
        "buyer_id":      score_dict["buyer_id"],

        # ── All scoring sub-components (preserved for re-ranking) ──
        "scores": {
            "industry_match":   score_dict["score_industry_match"],
            "intent":           score_dict["score_intent"],
            "reliability":      score_dict["score_reliability"],
            "geopolitical":     score_dict["score_geopolitical"],
            "news_delta":       score_dict["score_news_delta"],
            "recency_weight":   score_dict["score_recency_weight"],
        },

        # ── Penalty factors ──
        "penalties": {
            "swipe_decay":  score_dict["swipe_penalty_factor"],
            "pattern":      score_dict["pattern_penalty_factor"],
        },

        # ── Final rank value (THE number used for card ordering) ──
        "composite_score":  score_dict["composite_score"],

        # ── Display fields ──
        "score_tier":         score_dict["score_tier"],
        "industry_match_tag": score_dict["industry_match_tag"],
        "match_reasons":      score_dict["match_reasons"],

        # ── Metadata ──
        "scored_at":          score_dict["scored_at"],
        "data_completeness":  score_dict["data_completeness"],
    }


def build_swipe_event_document(
    exporter_id: str,
    buyer_id: str,
    direction: str,
    timestamp: str,
) -> dict:
    """
    Builds a MongoDB swipe_events document. Append-only audit log.
    """
    return {
        "exporter_id": exporter_id,
        "buyer_id":    buyer_id,
        "direction":   direction,   # "left" or "right"
        "timestamp":   timestamp,
    }


def build_swipe_state_document(
    exporter_id: str,
    buyer_id: str,
    state: dict,
) -> dict:
    """
    Builds a MongoDB exporter_swipe_state document.
    Upserted (not inserted) — one document per (exporter, buyer) pair.
    """
    return {
        "_id":          f"{exporter_id}__{buyer_id}",  # deterministic compound key
        "exporter_id":  exporter_id,
        "buyer_id":     buyer_id,
        "left_count":   state.get("left_count", 0),
        "right_count":  state.get("right_count", 0),
        "penalty_factor": state.get("penalty_factor", 1.0),
        "suppressed":   state.get("suppressed", False),
        "last_swiped_at": state.get("last_swiped_at"),
        "last_signal_recovery_at": state.get("last_signal_recovery_at"),
    }


def build_news_event_document(row: pd.Series) -> dict:
    """Builds a MongoDB news_events document."""
    raw = row.to_dict()
    cleaned_raw = {}
    for k, v in raw.items():
        if isinstance(v, float) and np.isnan(v):
            cleaned_raw[k] = None
        else:
            cleaned_raw[k] = v

    return {
        "_id":              raw.get("News_ID"),
        "raw":              cleaned_raw,
        "date":             raw.get("Date"),
        "region":           raw.get("Region"),
        "event_type":       raw.get("Event_Type"),
        "impact_level":     raw.get("Impact_Level"),
        "affected_industry":raw.get("Affected_Industry"),
        "computed": {
            "recency_weight":      raw.get("recency_weight"),
            "clean_tariff_change": raw.get("clean_tariff_change"),
            "clean_war_flag":      raw.get("clean_war_flag"),
            "clean_calamity_flag": raw.get("clean_calamity_flag"),
        }
    }


# ─── MONGODB INDEX RECOMMENDATIONS ───────────────────────────────────────────
RECOMMENDED_INDEXES = {
    "buyers": [
        {"fields": ["country"], "type": "single"},
        {"fields": ["industry"], "type": "single"},
        {"fields": ["computed.clean_intent_score"], "type": "single"},
    ],
    "exporters": [
        {"fields": ["industry"], "type": "single"},
        {"fields": ["state"], "type": "single"},
    ],
    "match_scores": [
        {"fields": ["exporter_id", "composite_score"], "type": "compound", "order": [1, -1]},
        {"fields": ["exporter_id", "buyer_id"], "type": "compound", "unique": True},
        {"fields": ["exporter_id", "scores.industry_match"], "type": "compound"},
    ],
    "swipe_events": [
        {"fields": ["exporter_id", "timestamp"], "type": "compound"},
    ],
    "exporter_swipe_state": [
        {"fields": ["exporter_id", "buyer_id"], "type": "compound", "unique": True},
        {"fields": ["exporter_id", "suppressed"], "type": "compound"},
    ],
}
