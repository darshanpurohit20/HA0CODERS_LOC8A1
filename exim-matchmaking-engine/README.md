# 🚀 Swipe-to-Export: Intelligent Matchmaking Algorithm
## Complete Architecture & Integration Guide

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      DATA INGESTION LAYER                           │
│  importer.csv ──┐                                                   │
│  exporter.csv ──┼──► data_loader.py ──► Cleaned DataFrames         │
│  globalnews.csv─┘     (raw fields kept, clean_* fields added)       │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      INTELLIGENCE LAYER                             │
│                                                                     │
│  news_overlay.py ──► pre-built (country, industry) → delta dict     │
│  scoring_engine.py ──► sub-scores + composite per (exp, buyer) pair │
│  swipe_engine.py ──► B: soft decay  +  C: pattern learning          │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      MONGODB STORAGE LAYER                          │
│                                                                     │
│  buyers ──────────────  raw + computed buyer fields                 │
│  exporters ────────────  raw + computed exporter fields             │
│  match_scores ─────────  per (exporter, buyer) scored pairs         │
│  exporter_swipe_state ─  Option B: per-pair decay state             │
│  exporter_preference_vectors ─  Option C: learned patterns          │
│  swipe_events ─────────  append-only audit log                      │
│  news_events ──────────  processed global news                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      API / CARD DECK LAYER                          │
│                                                                     │
│  GET /cards/:exporter_id  ──► ranked buyer cards (composite DESC)   │
│  POST /swipe              ──► triggers swipe_engine update          │
│  GET /match/:exporter/:buyer ──► full score breakdown               │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Scoring Formula (Full Breakdown)

```
composite_score =
  clip(
    (
      industry_match_score  × 0.35   ← Priority 1
    + intent_composite      × 0.30   ← Priority 2
    + reliability_score     × 0.20   ← Priority 3
    + geopolitical_safety   × 0.15   ← Priority 4
    + news_overlay_delta            ← Dynamic overlay (-0.4 to +0.4)
    ) × recency_weight              ← Older records naturally rank lower
    × swipe_penalty_factor          ← Option B: left-swipe decay
    × pattern_penalty_factor        ← Option C: learned dislike patterns
  , 0, 1)
```

### Sub-score Breakdown

| Sub-score | Inputs | Range |
|---|---|---|
| `industry_match` | exact=1.0, adjacent=0.5, none=0.0 | 0–1 |
| `intent_composite` | intent_score, engagement, funding, DM change, hiring, profile visits | 0–1 |
| `reliability_score` | payment_history(55%) + prompt_response(45%) | 0–1 |
| `geopolitical_safety` | starts 1.0, penalised by war/tariff/calamity/shock, currency bonus | 0–1 |
| `news_delta` | matched from globalnews by country+industry+recency | -0.4 to +0.4 |
| `recency_weight` | exponential decay: e^(-0.001 × days_old) | 0–1 |

---

## 3. MongoDB Collections Schema

### 3.1 `buyers` Collection
```json
{
  "_id": "BUY_69687",
  "raw": { /* ALL original CSV fields, untouched */ },
  "computed": {
    "market_momentum_score": 0.72,
    "contact_readiness_score": 0.61,
    "buyer_activity_tier": "High Activity",
    "recency_weight": 0.73,
    "data_completeness": 1.0,
    "clean_intent_score": 0.83,
    "clean_good_payment": 1.0,
    "clean_prompt_response": 0.92,
    "clean_hiring_growth": 0.0,
    "clean_funding_event": 1.0,
    "clean_engagement_spike": 0.0,
    "clean_decision_maker_change": 1.0,
    "clean_war_event": 1.0,
    "clean_natural_calamity": 1.0,
    "clean_tariff_news": 1.0,
    "clean_stock_shock": 1.0,
    "clean_currency_fluctuation": 0.13
  },
  "country": "Netherlands",
  "industry": "Solar",
  "channel": "Email"
}
```

### 3.2 `exporters` Collection
```json
{
  "_id": "EXP_5094",
  "raw": { /* ALL original CSV fields */ },
  "computed": {
    "recency_weight": 0.91,
    "capacity_tier": "Large",
    "exporter_reliability": 0.65
  },
  "preference_vector": {
    "left_patterns":  { "Netherlands|Solar": 2 },
    "right_patterns": { "Japan|Solar": 1 }
  },
  "state": "Rajasthan",
  "industry": "Textiles"
}
```

### 3.3 `match_scores` Collection (KEY collection for card deck)
```json
{
  "exporter_id": "EXP_5094",
  "buyer_id": "BUY_19862",
  "scores": {
    "industry_match": 1.0,
    "intent": 0.43,
    "reliability": 0.81,
    "geopolitical": 0.72,
    "news_delta": -0.08,
    "recency_weight": 0.89
  },
  "penalties": {
    "swipe_decay": 1.0,
    "pattern": 1.0
  },
  "composite_score": 0.383,
  "score_tier": "🔵 Weak Fit",
  "industry_match_tag": "exact",
  "match_reasons": [
    "✅ Exact industry match (Textiles)",
    "📈 Moderate buyer intent signals",
    "💳 Strong payment & response track record"
  ],
  "news_tags": ["📋 High impact: Tariff Update in Global affecting Textiles"],
  "buyer_display": {
    "country": "UK",
    "industry": "Textiles",
    "revenue_usd": 82742166,
    "team_size": 4456,
    "certification": "None",
    "channel": "WhatsApp",
    "activity_tier": "Stable",
    "momentum": 0.12,
    "contact_ready": 0.69
  },
  "scored_at": "2025-02-23"
}
```

### 3.4 `exporter_swipe_state` Collection
```json
{
  "_id": "EXP_5094__BUY_69687",
  "exporter_id": "EXP_5094",
  "buyer_id": "BUY_69687",
  "left_count": 3,
  "right_count": 0,
  "penalty_factor": 0.216,
  "suppressed": false,
  "last_swiped_at": "2025-02-23T10:30:00"
}
```

### 3.5 `swipe_events` Collection (append-only)
```json
{
  "exporter_id": "EXP_5094",
  "buyer_id": "BUY_69687",
  "direction": "left",
  "timestamp": "2025-02-23T10:30:00"
}
```

---

## 4. Recommended MongoDB Indexes

```javascript
// match_scores — primary card deck query
db.match_scores.createIndex({ exporter_id: 1, composite_score: -1 })
db.match_scores.createIndex({ exporter_id: 1, buyer_id: 1 }, { unique: true })

// exporter_swipe_state — fast lookup during scoring
db.exporter_swipe_state.createIndex({ exporter_id: 1, buyer_id: 1 }, { unique: true })
db.exporter_swipe_state.createIndex({ exporter_id: 1, suppressed: 1 })

// swipe_events — analytics queries
db.swipe_events.createIndex({ exporter_id: 1, timestamp: -1 })
```

---

## 5. Swipe Feedback Engine (B + C Combined)

### Option B: Soft Decay
```
Each left swipe:   penalty_factor = penalty_factor × 0.60
Floor:             penalty_factor never below 0.05 (always slightly visible)
Time recovery:     +0.08 per week since last left-swipe (auto-heals over time)
Signal recovery:   +0.30 × signal_strength if buyer gets new funding/DM change
After 5 left swipes: buyer.suppressed = true (removed from deck)
```

### Option C: Pattern Learning
```
Track: { "Netherlands|Solar": 3 }  ← exporter left-swiped this profile 3 times
Threshold: 3+ net left swipes on a pattern → apply pattern_penalty = 0.70

Pattern key = Country|Industry (configurable in PATTERN_DIMENSIONS)
Right swipes on a pattern type → pattern_boost up to +15%
Combined: composite × penalty_factor × (pattern_penalty × pattern_boost)
```

### Signal Recovery Conditions
| Signal | Recovery Weight |
|---|---|
| New Funding Event | 0.40 |
| Decision Maker Change | 0.40 |
| Hiring Growth | 0.20 |

---

## 6. News Overlay Logic

```
For each news event:
  1. Get base_effect from EVENT_TYPE (e.g., "Trade Agreement" = +0.12)
  2. Adjust sign for Tariff Updates based on tariff_change direction
  3. Multiply by IMPACT_LEVEL weight (High=1.0, Medium=0.6, Low=0.3)
  4. Multiply by recency_weight (older news has less impact)
  5. Accumulate into overlay[(country, industry)] dict
  6. Also accumulate into overlay[("__GLOBAL__", industry)] for global events

At scoring time:
  news_delta = overlay[(buyer_country, buyer_industry)]
             + overlay[("__GLOBAL__", buyer_industry)]
  (clipped to [-0.40, +0.40])
```

---

## 7. Frontend Card Query Pattern

```javascript
// Get ranked buyer cards for an exporter (MongoDB query)
db.match_scores.find(
  {
    exporter_id: "EXP_5094",
    "penalties.swipe_decay": { $gt: 0.05 },  // not suppressed by swipe
    composite_score: { $gt: 0.10 }            // above min threshold
  },
  { buyer_display: 1, composite_score: 1, score_tier: 1, match_reasons: 1, news_tags: 1 }
).sort({ composite_score: -1 }).limit(20)
```

---

## 8. Re-Scoring Triggers

The system should re-score matches when:
- A buyer gets a new funding event → triggers signal recovery + rescore
- A decision maker change is detected → triggers signal recovery + rescore
- A new global news event is ingested → overlay recomputed, scores updated
- Weekly batch job → applies time recovery across all swipe states

---

## 9. File Structure

```
swipe_algo/
├── config.py          ← All weights, thresholds, mappings (tune here)
├── data_loader.py     ← CSV cleaning pipeline (raw fields never overwritten)
├── news_overlay.py    ← Global news risk/opportunity overlay engine
├── scoring_engine.py  ← Multi-criteria scoring + composite formula
├── swipe_engine.py    ← B: soft decay + C: pattern learning
├── mongo_schema.py    ← MongoDB document builders + index recommendations
├── main.py            ← Full pipeline orchestrator
├── data/
│   ├── importer.csv
│   ├── exporter.csv
│   └── globalnews.csv
└── output/
    ├── mongo_buyers.json          ← Insert into `buyers` collection
    ├── mongo_exporters.json       ← Insert into `exporters` collection
    ├── mongo_match_scores.json    ← Insert into `match_scores` collection
    ├── mongo_news_events.json     ← Insert into `news_events` collection
    ├── mongo_card_decks.json      ← Pre-ranked decks per exporter
    └── mongo_indexes.json         ← Index creation recommendations
```
