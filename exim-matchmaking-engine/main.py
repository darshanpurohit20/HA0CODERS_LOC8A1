# =============================================================================
# main.py — Full Pipeline Orchestrator
# =============================================================================
# Runs the complete Swipe-to-Export matchmaking algorithm:
#   1. Load + clean all CSVs
#   2. Build global news overlay
#   3. Score every (exporter, buyer) pair
#   4. Apply swipe feedback (demo simulation)
#   5. Rank buyers per exporter
#   6. Output MongoDB-ready JSON documents

import json
import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime

from data_loader import load_importers, load_exporters, load_news
from news_overlay import build_news_overlay, get_news_tags
from scoring_engine import score_buyer_for_exporter
from swipe_engine import SwipeStore, compute_full_swipe_factors, default_swipe_state
from mongo_schema import (
    build_buyer_document,
    build_exporter_document,
    build_match_score_document,
    build_news_event_document,
    RECOMMENDED_INDEXES,
)
from config import MIN_COMPOSITE_SCORE


# ─── PATH RESOLUTION ─────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.join(BASE_DIR, "data")
OUTPUT_DIR  = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def json_safe(obj):
    """Recursively make object JSON-serialisable (handles NaN, numpy types)."""
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [json_safe(i) for i in obj]
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


def save_json(data, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, "w") as f:
        json.dump(json_safe(data), f, indent=2)
    print(f"  ✅ Saved: {filename} ({len(data)} records)")
    return path


# ─── DEMO SWIPE SIMULATION ───────────────────────────────────────────────────
def simulate_demo_swipes(store: SwipeStore, exporters_df, buyers_df):
    """
    Simulates a realistic swipe history to demonstrate the feedback engine.
    In production, swipes come from real user interactions.
    """
    print("\n[Demo] Simulating swipe history...")

    buyers_list = buyers_df.to_dict("records")
    exporters_list = exporters_df.to_dict("records")

    # Simulate: EXP_5094 (Textiles, Rajasthan) left-swipes Netherlands buyers 3x
    netherlands_buyers = [b for b in buyers_list if b.get("Country") == "Netherlands"]
    for buyer in netherlands_buyers[:3]:
        store.process_swipe("EXP_5094", buyer["Buyer_ID"], "left", buyer)

    # Simulate: EXP_5094 likes Japan buyers (right swipe)
    japan_buyers = [b for b in buyers_list if b.get("Country") == "Japan"]
    for buyer in japan_buyers[:2]:
        store.process_swipe("EXP_5094", buyer["Buyer_ID"], "right", buyer)

    # Simulate: EXP_3114 (Solar, Tamil Nadu) left-swipes IT Software buyers twice
    it_buyers = [b for b in buyers_list if b.get("Industry") == "IT Software"]
    for buyer in it_buyers[:2]:
        store.process_swipe("EXP_3114", buyer["Buyer_ID"], "left", buyer)

    print(f"  [Demo] Swipe history simulated for 2 exporters")


# ─── MAIN PIPELINE ───────────────────────────────────────────────────────────
def run_pipeline(
    importer_path: str,
    exporter_path: str,
    news_path: str,
    top_n_per_exporter: int = 10,
):
    print("\n" + "="*60)
    print("🚀 SWIPE-TO-EXPORT: Matchmaking Algorithm Pipeline")
    print("="*60)

    # ── STEP 1: Load & Clean ──────────────────────────────────────────────
    print("\n[Step 1] Loading and cleaning data...")
    buyers_df    = load_importers(importer_path)
    exporters_df = load_exporters(exporter_path)
    news_df      = load_news(news_path)

    # ── STEP 2: Build News Overlay ────────────────────────────────────────
    print("\n[Step 2] Building global news overlay...")
    news_overlay = build_news_overlay(news_df)
    print(f"  News overlay built: {len(news_overlay)} (country, industry) keys indexed")

    # ── STEP 3: Build MongoDB Documents for base collections ─────────────
    print("\n[Step 3] Building base collection documents...")
    buyer_docs    = [build_buyer_document(row) for _, row in buyers_df.iterrows()]
    exporter_docs = [build_exporter_document(row) for _, row in exporters_df.iterrows()]
    news_docs     = [build_news_event_document(row) for _, row in news_df.iterrows()]

    # ── STEP 4: Simulate Swipe History ───────────────────────────────────
    print("\n[Step 4] Initialising swipe feedback engine...")
    swipe_store = SwipeStore()
    simulate_demo_swipes(swipe_store, exporters_df, buyers_df)

    # ── STEP 5: Score All (exporter, buyer) Pairs ────────────────────────
    print("\n[Step 5] Scoring all exporter-buyer pairs...")
    match_docs        = []
    ranked_per_exporter = {}

    exporters_list = exporters_df.to_dict("records")
    buyers_list    = buyers_df.to_dict("records")
    total_pairs    = len(exporters_list) * len(buyers_list)
    scored          = 0

    for exp_row in exporters_list:
        exp_id     = exp_row["Exporter_ID"]
        exp_scores = []
        pv         = swipe_store.get_preference_vector(exp_id)

        for buy_row in buyers_list:
            buy_id = buy_row["Buyer_ID"]

            # Get swipe state for this pair
            raw_state   = swipe_store.get_state(exp_id, buy_id)
            swipe_factors = compute_full_swipe_factors(raw_state, pv, buy_row)

            # Skip suppressed buyers entirely
            if swipe_factors.get("suppressed", False):
                scored += 1
                continue

            # Build swipe_state dict expected by score_buyer_for_exporter
            swipe_state_for_scorer = {
                "penalty_factor":  swipe_factors["penalty_factor"],
                "pattern_penalty": swipe_factors["pattern_penalty"],
            }

            # Compute full score
            score_doc = score_buyer_for_exporter(
                exporter_row = exp_row,
                buyer_row    = buy_row,
                news_overlay = news_overlay,
                swipe_state  = swipe_state_for_scorer,
            )

            # Skip very low scores
            if score_doc["composite_score"] < MIN_COMPOSITE_SCORE:
                scored += 1
                continue

            # Attach news tags for card UI
            news_tags = get_news_tags(news_df, buy_row.get("Country",""), buy_row.get("Industry",""))
            score_doc["news_tags"] = news_tags

            # Attach top-level buyer display fields for card rendering
            score_doc["buyer_display"] = {
                "country":         buy_row.get("Country"),
                "industry":        buy_row.get("Industry"),
                "revenue_usd":     buy_row.get("Revenue_Size_USD"),
                "team_size":       buy_row.get("Team_Size"),
                "certification":   buy_row.get("Certification"),
                "channel":         buy_row.get("clean_channel"),
                "activity_tier":   buy_row.get("buyer_activity_tier"),
                "momentum":        buy_row.get("market_momentum_score"),
                "contact_ready":   buy_row.get("contact_readiness_score"),
            }

            mongo_doc = build_match_score_document(score_doc)
            match_docs.append(mongo_doc)
            exp_scores.append(score_doc)
            scored += 1

        # Sort this exporter's matches by composite_score DESC
        exp_scores.sort(key=lambda x: x["composite_score"], reverse=True)
        ranked_per_exporter[exp_id] = exp_scores[:top_n_per_exporter]

    print(f"  Scored {scored}/{total_pairs} pairs | {len(match_docs)} valid matches generated")

    # ── STEP 6: Generate Per-Exporter Ranked Output ───────────────────────
    print("\n[Step 6] Building ranked card decks per exporter...")
    card_decks = {}
    for exp_id, matches in ranked_per_exporter.items():
        exp_info = next((e for e in exporters_list if e["Exporter_ID"] == exp_id), {})
        card_decks[exp_id] = {
            "exporter_id":   exp_id,
            "exporter_name": exp_id,
            "industry":      exp_info.get("Industry"),
            "state":         exp_info.get("State"),
            "total_matches": len(matches),
            "generated_at":  datetime.utcnow().isoformat(),
            "top_matches":   matches,
        }

    # ── STEP 7: Save Outputs ──────────────────────────────────────────────
    print("\n[Step 7] Saving MongoDB-ready JSON outputs...")
    save_json(buyer_docs,    "mongo_buyers.json")
    save_json(exporter_docs, "mongo_exporters.json")
    save_json(news_docs,     "mongo_news_events.json")
    save_json(match_docs,    "mongo_match_scores.json")
    save_json(card_decks,    "mongo_card_decks.json")
    save_json(RECOMMENDED_INDEXES, "mongo_indexes.json")

    # ── STEP 8: Print Summary ─────────────────────────────────────────────
    print("\n" + "="*60)
    print("📊 PIPELINE COMPLETE — SUMMARY")
    print("="*60)
    for exp_id, deck in card_decks.items():
        print(f"\n  🏭 {exp_id} [{deck['industry']} | {deck['state']}]")
        print(f"     Top {min(3, len(deck['top_matches']))} buyer matches:")
        for i, m in enumerate(deck["top_matches"][:3]):
            bd = m.get("buyer_display", {})
            print(f"       #{i+1} {m['buyer_id']} | {bd.get('country')} | "
                  f"{bd.get('industry')} | Score: {m['composite_score']:.3f} {m['score_tier']}")
            for reason in m.get("match_reasons", [])[:2]:
                print(f"          → {reason}")

    return card_decks


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_pipeline(
        importer_path = os.path.join(DATA_DIR, "importer.csv"),
        exporter_path = os.path.join(DATA_DIR, "exporter.csv"),
        news_path     = os.path.join(DATA_DIR, "globalnews.csv"),
        top_n_per_exporter = 10,
    )
