import os
import pandas as pd
from pinecone import Pinecone
from dotenv import load_dotenv
import math


# Load environment variables
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")

if not PINECONE_API_KEY:
    raise ValueError("❌ PINECONE_API_KEY not found in .env")

# 🔐 Add your Pinecone API key
pc = Pinecone(api_key=PINECONE_API_KEY)

# Connect to index
index = pc.Index(PINECONE_INDEX)

# Load CSV
df = pd.read_csv("globalnews.csv")

# Safe string handler
def safe_value(val):
    if pd.isna(val):
        return "Not available"
    return str(val)

# Safe numeric handlers
def safe_int(val):
    try:
        if pd.isna(val):
            return 0
        return int(float(val))
    except:
        return 0

def safe_float(val):
    try:
        if pd.isna(val):
            return 0.0
        return float(val)
    except:
        return 0.0



records = []

for _, row in df.iterrows():

    # Build FULL semantic record text
    text_summary = f"""
        News record ID {safe_value(row['NEWS_ID'])}.
        Date {safe_value(row['Date'])}.
        Region {safe_value(row['Region'])}.
        Event type {safe_value(row['Event_Type'])}.
        Impact level {safe_value(row['Impact_Level'])}.
        Affected industry {safe_value(row['Affected_Industry'])}.
        Tariff change {safe_value(row['Tariff_Change'])}.
        Stock market shock {safe_value(row['StockMarket_Shock'])}.
        War flag {safe_value(row['War_Flag'])}.
        Natural calamity flag {safe_value(row['Natural_Calamity_Flag'])}.
        Currency shift {safe_value(row['Currency_Shift'])}.
        """

    records.append({
    "id": str(row["NEWS_ID"]),
    "text": text_summary.strip(),

    # Identity
    "news_id": str(row["NEWS_ID"]),
    "date": safe_value(row["Date"]),
    "region": safe_value(row["Region"]),
    "event_type": safe_value(row["Event_Type"]),
    "impact_level": safe_value(row["Impact_Level"]),
    "affected_industry": safe_value(row["Affected_Industry"]),

    # Economic impact signals
    "tariff_change": safe_float(row["Tariff_Change"]),
    "stock_market_shock": safe_float(row["StockMarket_Shock"]),
    "currency_shift": safe_float(row["Currency_Shift"]),

    # Risk flags
    "war_flag": safe_int(row["War_Flag"]),
    "natural_calamity_flag": safe_int(row["Natural_Calamity_Flag"]),
})
        


# Upload in batches
batch_size = 96

for i in range(0, len(records), batch_size):
    batch = records[i:i+batch_size]

    index.upsert_records(
        namespace="globalnews",      # default namespace
        records=batch
    )

    print(f"Uploaded batch {i//batch_size + 1}")