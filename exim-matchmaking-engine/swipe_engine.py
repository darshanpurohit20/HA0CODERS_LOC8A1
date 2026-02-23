# =============================================================================
# swipe_engine.py — Swipe Feedback Engine (Option B + C Combined)
# =============================================================================
#
# OPTION B: Soft Decay with Signal Recovery
#   Each left swipe multiplies the buyer's penalty_factor by SWIPE_LEFT_DECAY_FACTOR.
#   Over time (weeks without swipe), the factor recovers toward 1.0.
#   If the buyer gets a NEW signal (new funding, decision-maker change),
#   the penalty recovers partially — they might now be worth re-evaluating.
#
# OPTION C: Pattern Learning
#   When an exporter left-swipes buyers sharing similar profile dimensions
#   (same country + industry), we learn a "dislike pattern" and apply a
#   pattern_penalty to ALL unseen buyers matching that profile.
#   This is per-exporter — one exporter's patterns don't affect others.
#
# MONGODB STORAGE:
#   swipe_events collection:     raw swipe log (append-only)
#   exporter_swipe_state:        per (exporter, buyer) penalty state
#   exporter_preference_vectors: per exporter pattern learning state

from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from config import (
    SWIPE_LEFT_DECAY_FACTOR,
    SWIPE_MIN_PENALTY_FLOOR,
    SWIPE_RECOVERY_PER_WEEK,
    SWIPE_SIGNAL_RECOVERY,
    PATTERN_LEFT_THRESHOLD,
    PATTERN_PENALTY_FACTOR,
    PATTERN_DIMENSIONS,
    MAX_LEFT_SWIPES_BEFORE_HIDE,
)


# ─── SWIPE STATE DOCUMENT (stored per exporter+buyer in MongoDB) ─────────────
def default_swipe_state() -> dict:
    """Initial state for a buyer that hasn't been swiped yet."""
    return {
        "left_count":     0,
        "right_count":    0,
        "last_swiped_at": None,
        "penalty_factor": 1.0,    # B: starts at full score
        "suppressed":     False,  # True if left_count >= MAX_LEFT_SWIPES_BEFORE_HIDE
    }


# ─── OPTION B: SOFT DECAY ────────────────────────────────────────────────────

def apply_left_swipe(state: dict) -> dict:
    """
    Call when exporter left-swipes a buyer.
    Decays the penalty_factor and increments left_count.
    """
    state = dict(state)  # don't mutate original
    state["left_count"]     += 1
    state["last_swiped_at"]  = datetime.utcnow().isoformat()

    # Multiplicative decay — gets harsher with repeated left-swipes
    new_penalty = state["penalty_factor"] * SWIPE_LEFT_DECAY_FACTOR
    state["penalty_factor"] = max(new_penalty, SWIPE_MIN_PENALTY_FLOOR)

    # Suppress from deck if too many left swipes
    if state["left_count"] >= MAX_LEFT_SWIPES_BEFORE_HIDE:
        state["suppressed"] = True

    return state


def apply_right_swipe(state: dict) -> dict:
    """Call when exporter right-swipes (interested in) a buyer."""
    state = dict(state)
    state["right_count"]    += 1
    state["last_swiped_at"]  = datetime.utcnow().isoformat()
    # Right swipe partially resets penalty (exporter showed renewed interest)
    state["penalty_factor"]  = min(state["penalty_factor"] + 0.20, 1.0)
    state["suppressed"]      = False
    return state


def apply_time_recovery(state: dict) -> dict:
    """
    Call when loading a buyer's state — apply passive time-based recovery.
    If it's been a while since the last left swipe, the penalty softens.
    This simulates: "I haven't seen this buyer in a while, maybe worth trying again."
    """
    state = dict(state)
    last_swiped = state.get("last_swiped_at")
    if not last_swiped or state["penalty_factor"] >= 1.0:
        return state

    try:
        last_dt = datetime.fromisoformat(last_swiped)
        weeks_elapsed = (datetime.utcnow() - last_dt).days / 7
        recovery = weeks_elapsed * SWIPE_RECOVERY_PER_WEEK
        state["penalty_factor"] = min(state["penalty_factor"] + recovery, 1.0)
    except Exception:
        pass

    # If penalty recovered above suppression threshold, un-suppress
    if state["penalty_factor"] > 0.3 and state["suppressed"]:
        state["suppressed"] = False

    return state


def apply_signal_recovery(state: dict, buyer_row: dict) -> dict:
    """
    OPTION B signal recovery: if buyer got a NEW signal (funding, DM change)
    since last left-swipe, partially recover penalty.
    This is called when buyer signals update in the system.
    """
    state = dict(state)
    last_swiped = state.get("last_swiped_at")
    if not last_swiped or state["penalty_factor"] >= 1.0:
        return state

    # Check if buyer has fresh signals (simplified: funding + DM change as proxies)
    new_funding    = float(buyer_row.get("clean_funding_event", 0))
    new_dm_change  = float(buyer_row.get("clean_decision_maker_change", 0))
    hiring_growth  = float(buyer_row.get("clean_hiring_growth", 0))

    signal_strength = (new_funding * 0.4 + new_dm_change * 0.4 + hiring_growth * 0.2)

    if signal_strength > 0.3:
        recovery = SWIPE_SIGNAL_RECOVERY * signal_strength
        state["penalty_factor"] = min(state["penalty_factor"] + recovery, 1.0)
        state["suppressed"] = False  # Always un-suppress on meaningful signal

    return state


def get_final_swipe_penalty(state: dict, buyer_row: dict) -> dict:
    """
    Master function: apply time recovery + signal recovery, return clean state.
    Call this at scoring time to get current penalty factors.
    """
    state = apply_time_recovery(state)
    state = apply_signal_recovery(state, buyer_row)
    return state


# ─── OPTION C: PATTERN LEARNING ──────────────────────────────────────────────

def update_preference_vector(
    preference_vector: dict,
    buyer_row: dict,
    direction: str,   # "left" or "right"
) -> dict:
    """
    Updates a per-exporter preference vector based on a swipe action.
    
    Structure of preference_vector:
    {
        "left_patterns":  { "Netherlands|Solar": 3, "Germany|Machinery": 1 },
        "right_patterns": { "Japan|Solar": 2, "Canada|Medical Devices": 1 },
    }
    
    Each key is "{Country}|{Industry}" (or whatever PATTERN_DIMENSIONS specifies).
    Value is the count of swipes in that direction.
    """
    pv = dict(preference_vector)
    pv.setdefault("left_patterns", {})
    pv.setdefault("right_patterns", {})

    # Build the pattern key from configured dimensions
    key_parts = []
    for dim in PATTERN_DIMENSIONS:
        val = str(buyer_row.get(dim, "Unknown")).strip()
        key_parts.append(val)
    pattern_key = "|".join(key_parts)

    if direction == "left":
        pv["left_patterns"][pattern_key] = pv["left_patterns"].get(pattern_key, 0) + 1
    elif direction == "right":
        pv["right_patterns"][pattern_key] = pv["right_patterns"].get(pattern_key, 0) + 1

    pv["last_updated"] = datetime.utcnow().isoformat()
    return pv


def compute_pattern_penalty(
    preference_vector: dict,
    buyer_row: dict,
) -> float:
    """
    OPTION C: Given an exporter's preference vector, compute what penalty
    factor a NEW unseen buyer should get based on pattern matching.

    Returns:
        float: 1.0 = no penalty, 0.7 = mild penalty, 0.5 = strong penalty
        (penalty applied multiplicatively to composite score)
    """
    if not preference_vector:
        return 1.0

    # Build this buyer's pattern key
    key_parts = []
    for dim in PATTERN_DIMENSIONS:
        val = str(buyer_row.get(dim, "Unknown")).strip()
        key_parts.append(val)
    pattern_key = "|".join(key_parts)

    left_patterns  = preference_vector.get("left_patterns", {})
    right_patterns = preference_vector.get("right_patterns", {})

    left_count  = left_patterns.get(pattern_key, 0)
    right_count = right_patterns.get(pattern_key, 0)

    # Net negative sentiment for this pattern
    net_left = left_count - right_count

    if net_left < PATTERN_LEFT_THRESHOLD:
        return 1.0  # No learned dislike — no penalty

    # Penalty scales with how many net left swipes beyond threshold
    excess = net_left - PATTERN_LEFT_THRESHOLD
    penalty = 1.0 - PATTERN_PENALTY_FACTOR - (excess * 0.05)
    return float(max(penalty, 0.35))  # Floor at 35% — never fully suppress by pattern alone


def get_pattern_boost(preference_vector: dict, buyer_row: dict) -> float:
    """
    If an exporter has previously right-swiped buyers matching this profile,
    give a small boost to the composite score. Rewards similar good matches.
    Returns: float boost factor (1.0 = no boost, up to 1.15)
    """
    if not preference_vector:
        return 1.0

    key_parts = []
    for dim in PATTERN_DIMENSIONS:
        val = str(buyer_row.get(dim, "Unknown")).strip()
        key_parts.append(val)
    pattern_key = "|".join(key_parts)

    right_count = preference_vector.get("right_patterns", {}).get(pattern_key, 0)
    left_count  = preference_vector.get("left_patterns", {}).get(pattern_key, 0)
    net_right   = right_count - left_count

    if net_right <= 0:
        return 1.0

    boost = 1.0 + min(net_right * 0.03, 0.15)  # Up to +15% boost
    return float(boost)


# ─── COMBINED SWIPE STATE ────────────────────────────────────────────────────

def compute_full_swipe_factors(
    swipe_state: dict,
    preference_vector: dict,
    buyer_row: dict,
) -> dict:
    """
    Combines Option B (soft decay) + Option C (pattern learning)
    into a single swipe_factors dict consumed by scoring_engine.

    Returns:
        {
            "penalty_factor":   float (0.05–1.0),   # B: per-buyer decay
            "pattern_penalty":  float (0.35–1.0),   # C: pattern-based penalty
            "pattern_boost":    float (1.0–1.15),   # C: pattern-based boost
            "suppressed":       bool,                # Should this buyer be hidden?
        }
    """
    # Apply time + signal recovery to B state
    updated_state = get_final_swipe_penalty(swipe_state, buyer_row)

    # Compute C factors
    pattern_pen   = compute_pattern_penalty(preference_vector, buyer_row)
    pattern_boost = get_pattern_boost(preference_vector, buyer_row)

    return {
        "penalty_factor":  updated_state.get("penalty_factor", 1.0),
        "pattern_penalty": pattern_pen * pattern_boost,  # boost offset against pattern penalty
        "suppressed":      updated_state.get("suppressed", False),
        "left_count":      updated_state.get("left_count", 0),
        "right_count":     updated_state.get("right_count", 0),
    }


# ─── MOCK IN-MEMORY STORE (Replace with MongoDB calls in production) ──────────

class SwipeStore:
    """
    In-memory mock of MongoDB swipe storage.
    In production, replace each method with a pymongo call.
    
    Collections replicated:
        - exporter_swipe_states:     { (exporter_id, buyer_id): state_dict }
        - exporter_preference_vectors: { exporter_id: pv_dict }
        - swipe_events_log:          [ event_dicts ]  (append-only)
    """
    def __init__(self):
        self._states    = defaultdict(default_swipe_state)
        self._pvectors  = defaultdict(dict)
        self._log       = []

    def get_state(self, exporter_id: str, buyer_id: str) -> dict:
        return self._states[(exporter_id, buyer_id)].copy()

    def save_state(self, exporter_id: str, buyer_id: str, state: dict):
        self._states[(exporter_id, buyer_id)] = state

    def get_preference_vector(self, exporter_id: str) -> dict:
        return self._pvectors[exporter_id].copy()

    def save_preference_vector(self, exporter_id: str, pv: dict):
        self._pvectors[exporter_id] = pv

    def record_swipe_event(self, exporter_id: str, buyer_id: str, direction: str):
        self._log.append({
            "exporter_id": exporter_id,
            "buyer_id":    buyer_id,
            "direction":   direction,
            "timestamp":   datetime.utcnow().isoformat(),
        })

    def process_swipe(self, exporter_id: str, buyer_id: str, direction: str, buyer_row: dict):
        """
        Single entry point for processing a swipe event.
        Updates both Option B state and Option C preference vector.
        """
        # Load current state
        state = self.get_state(exporter_id, buyer_id)
        pv    = self.get_preference_vector(exporter_id)

        # Update B state
        if direction == "left":
            state = apply_left_swipe(state)
        elif direction == "right":
            state = apply_right_swipe(state)

        # Update C preference vector
        pv = update_preference_vector(pv, buyer_row, direction)

        # Persist
        self.save_state(exporter_id, buyer_id, state)
        self.save_preference_vector(exporter_id, pv)
        self.record_swipe_event(exporter_id, buyer_id, direction)

        return state, pv
