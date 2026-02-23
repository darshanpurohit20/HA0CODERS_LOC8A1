# =============================================================================
# data_loader.py — Data Cleaning & Standardisation Pipeline
# =============================================================================
# Loads raw CSVs, cleans messy fields, fills missing values intelligently,
# and returns structured DataFrames ready for the scoring engine.
# Raw fields are NEVER overwritten — new fields are always ADDED alongside.

import pandas as pd
import numpy as np
from datetime import datetime
from config import PROFILE_VISITS_NORM_CAP, RECORD_RECENCY_LAMBDA

TODAY = datetime.today()


# ─── GENERIC HELPERS ─────────────────────────────────────────────────────────

def _safe_float(val, fallback=np.nan):
    """Convert messy values to float. Handles 'NA', 'Unknown', '', None."""
    if val is None:
        return fallback
    s = str(val).strip().lower()
    if s in ("", "na", "nan", "none", "unknown", "null"):
        return fallback
    try:
        return float(val)
    except (ValueError, TypeError):
        return fallback


def _safe_binary(val, unknown_fallback=0.1):
    """
    Convert binary flag fields.
    - '1' / 1 / True  → 1.0
    - '0' / 0 / False → 0.0
    - 'Unknown' / NA  → unknown_fallback (treated as uncertain, not zero)
    """
    s = str(val).strip().lower()
    if s in ("1", "true", "yes"):
        return 1.0
    if s in ("0", "false", "no"):
        return 0.0
    return unknown_fallback


def _recency_weight(date_str):
    """
    Exponential decay weight based on how old the record is.
    Recent records score closer to 1.0; very old records approach 0.
    """
    try:
        record_date = pd.to_datetime(date_str)
        days_old = max((TODAY - record_date).days, 0)
        return float(np.exp(-RECORD_RECENCY_LAMBDA * days_old))
    except Exception:
        return 0.5  # neutral if date unparseable


def _get_score_tier(score):
    """Return human-readable label for a composite score."""
    from config import SCORE_TIERS
    for threshold, label in SCORE_TIERS:
        if score >= threshold:
            return label
    return "⚠️ Low Priority"


# ─── IMPORTER (BUYER) CLEANING ───────────────────────────────────────────────

def load_importers(filepath: str) -> pd.DataFrame:
    """
    Load and clean importer CSV.
    Returns DataFrame with original fields + clean_* derived fields.
    """
    df = pd.read_csv(filepath)

    # ── Drop rows with no Buyer_ID (can't match without identity) ──
    df = df[df["Buyer_ID"].notna() & df["Buyer_ID"].astype(str).str.strip().ne("")]
    df = df.reset_index(drop=True)

    # ── Clean: Numeric continuous fields ──
    df["clean_avg_order_tons"]      = df["Avg_Order_Tons"].apply(lambda x: _safe_float(x, fallback=np.nan))
    df["clean_revenue_usd"]         = df["Revenue_Size_USD"].apply(lambda x: _safe_float(x, fallback=0))
    df["clean_team_size"]           = df["Team_Size"].apply(lambda x: _safe_float(x, fallback=0))
    df["clean_prompt_response"]     = df["Prompt_Response"].apply(lambda x: _safe_float(x, fallback=0.5))
    df["clean_intent_score"]        = df["Intent_Score"].apply(lambda x: _safe_float(x, fallback=0.3))
    df["clean_response_probability"]= df["Response_Probability"].apply(lambda x: _safe_float(x, fallback=0.3))
    df["clean_currency_fluctuation"]= df["Currency_Fluctuation"].apply(lambda x: _safe_float(x, fallback=0.0))
    df["clean_profile_visits"]      = df["SalesNav_ProfileVisits"].apply(lambda x: _safe_float(x, fallback=0))

    # ── Clean: Binary flag fields ──
    df["clean_good_payment"]         = df["Good_Payment_History"].apply(_safe_binary)
    df["clean_hiring_growth"]        = df["Hiring_Growth"].apply(_safe_binary)
    df["clean_engagement_spike"]     = df["Engagement_Spike"].apply(_safe_binary)
    df["clean_decision_maker_change"]= df["DecisionMaker_Change"].apply(_safe_binary)
    df["clean_funding_event"]        = df["Funding_Event"].apply(lambda x: _safe_binary(x, unknown_fallback=0.1))
    df["clean_tariff_news"]          = df["Tariff_News"].apply(_safe_binary)
    df["clean_stock_shock"]          = df["StockMarket_Shock"].apply(_safe_binary)
    df["clean_war_event"]            = df["War_Event"].apply(_safe_binary)
    df["clean_natural_calamity"]     = df["Natural_Calamity"].apply(_safe_binary)

    # ── Derived: Normalize profile visits (0–1) ──
    df["norm_profile_visits"] = (
        df["clean_profile_visits"].clip(upper=PROFILE_VISITS_NORM_CAP)
        / PROFILE_VISITS_NORM_CAP
    )

    # ── Derived: Recency weight ──
    df["recency_weight"] = df["Date"].apply(_recency_weight)

    # ── Derived: Missing data score (transparency metric for UI) ──
    critical_fields = ["clean_avg_order_tons", "clean_response_probability"]
    df["data_completeness"] = df.apply(
        lambda row: 1.0 - sum(pd.isna(row[f]) for f in critical_fields) / len(critical_fields),
        axis=1
    )

    # ── Clean: Preferred channel (standardise casing, fill blanks) ──
    df["clean_channel"] = df["Preferred_Channel"].fillna("Unknown").str.strip().str.title()
    df.loc[df["clean_channel"] == "", "clean_channel"] = "Unknown"

    # ── Derived: Buyer activity tier (for card display) ──
    def activity_tier(row):
        signals = (
            (row["clean_hiring_growth"] > 0.5) +
            (row["clean_funding_event"] > 0.5) +
            (row["clean_engagement_spike"] > 0.5) +
            (row["clean_decision_maker_change"] > 0.5)
        )
        if signals >= 3: return "High Activity"
        if signals == 2: return "Growing"
        if signals == 1: return "Stable"
        return "Low Activity"

    df["buyer_activity_tier"] = df.apply(activity_tier, axis=1)

    # ── Derived: Market momentum score (0–1) ──
    df["market_momentum_score"] = (
        df["clean_hiring_growth"] * 0.3 +
        df["clean_funding_event"] * 0.4 +
        df["clean_engagement_spike"] * 0.3
    ).clip(0, 1)

    # ── Derived: Contact readiness score (0–1) ──
    df["contact_readiness_score"] = (
        df["clean_prompt_response"] * 0.6 +
        df["clean_response_probability"].fillna(0.3) * 0.4
    ).clip(0, 1)

    print(f"[Importers] Loaded {len(df)} records | {df['Industry'].nunique()} industries | "
          f"{df['Country'].nunique()} countries")
    return df


# ─── EXPORTER CLEANING ───────────────────────────────────────────────────────

def load_exporters(filepath: str) -> pd.DataFrame:
    """
    Load and clean exporter CSV.
    Returns DataFrame with original fields + clean_* derived fields.
    """
    df = pd.read_csv(filepath)
    df = df[df["Exporter_ID"].notna()].reset_index(drop=True)

    # ── Clean: Numeric fields ──
    df["clean_manufacturing_capacity"] = df["Manufacturing_Capacity_Tons"].apply(lambda x: _safe_float(x, 0))
    df["clean_revenue_usd"]            = df["Revenue_Size_USD"].apply(lambda x: _safe_float(x, 0))
    df["clean_team_size"]              = df["Team_Size"].apply(lambda x: _safe_float(x, 0))
    df["clean_prompt_response_score"]  = df["Prompt_Response_Score"].apply(lambda x: _safe_float(x, 0.5))
    df["clean_intent_score"]           = df["Intent_Score"].apply(lambda x: _safe_float(x, 0.3))
    df["clean_shipment_value_usd"]     = df["Shipment_Value_USD"].apply(lambda x: _safe_float(x, np.nan))
    df["clean_quantity_tons"]          = df["Quantity_Tons"].apply(lambda x: _safe_float(x, np.nan))
    df["clean_linkedin_activity"]      = df["LinkedIn_Activity"].apply(lambda x: _safe_float(x, 0))
    df["clean_tariff_impact"]          = df["Tariff_Impact"].apply(lambda x: _safe_float(x, 0))
    df["clean_stock_impact"]           = df["StockMarket_Impact"].apply(lambda x: _safe_float(x, 0))
    df["clean_war_risk"]               = df["War_Risk"].apply(_safe_binary)
    df["clean_natural_calamity_risk"]  = df["Natural_Calamity_Risk"].apply(_safe_binary)
    df["clean_currency_shift"]         = df["Currency_Shift"].apply(lambda x: _safe_float(x, 0))

    # ── Clean: Binary / categorical ──
    df["clean_good_payment_terms"] = df["Good_Payment_Terms"].apply(_safe_binary)
    df["clean_hiring_signal"]      = df["Hiring_Signal"].apply(_safe_binary)
    df["clean_msme"]               = df["MSME_Udyam"].apply(lambda x: _safe_binary(x, 0))
    df["clean_job_change"]         = df["SalesNav_JobChange"].apply(_safe_binary)

    # ── Derived: Recency weight ──
    df["recency_weight"] = df["Date"].apply(_recency_weight)

    # ── Derived: Export capacity tier ──
    def capacity_tier(row):
        cap = row["clean_manufacturing_capacity"]
        if cap == 0 or pd.isna(cap):   return "Unknown"
        if cap >= 6000:                  return "Large"
        if cap >= 2000:                  return "Medium"
        return "Small"

    df["capacity_tier"] = df.apply(capacity_tier, axis=1)

    # ── Derived: Exporter reliability score (used for matching context) ──
    df["exporter_reliability"] = (
        df["clean_good_payment_terms"] * 0.5 +
        df["clean_prompt_response_score"] * 0.5
    ).clip(0, 1)

    print(f"[Exporters] Loaded {len(df)} records | {df['Industry'].nunique()} industries | "
          f"{df['State'].nunique()} states")
    return df


# ─── GLOBAL NEWS CLEANING ────────────────────────────────────────────────────

def load_news(filepath: str) -> pd.DataFrame:
    """
    Load and clean global news CSV.
    Adds recency weight and normalised impact fields.
    """
    df = pd.read_csv(filepath)

    df["clean_tariff_change"]    = df["Tariff_Change"].apply(lambda x: _safe_float(x, 0))
    df["clean_stock_shock"]      = df["StockMarket_Shock"].apply(lambda x: _safe_float(x, 0))
    df["clean_war_flag"]         = df["War_Flag"].apply(_safe_binary)
    df["clean_calamity_flag"]    = df["Natural_Calamity_Flag"].apply(_safe_binary)
    df["clean_currency_shift"]   = df["Currency_Shift"].apply(lambda x: _safe_float(x, 0))
    df["recency_weight"]         = df["Date"].apply(_recency_weight)

    print(f"[News] Loaded {len(df)} events | {df['Event_Type'].nunique()} event types | "
          f"{df['Region'].nunique()} regions")
    return df
