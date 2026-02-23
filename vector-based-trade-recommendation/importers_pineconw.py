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
df = pd.read_csv("importer.csv")


        
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

    text_summary = f"""
    Import record ID {safe_value(row['IMP_ID'])}.
    Buyer ID {safe_value(row['Buyer_ID'])}.
    Date {safe_value(row['Date'])}.
    Country {safe_value(row['Country'])}.
    Industry {safe_value(row['Industry'])}.
    Average order size {safe_value(row['Avg_Order_Tons'])} tons.
    Revenue size {safe_value(row['Revenue_Size_USD'])} USD.
    Team size {safe_value(row['Team_Size'])}.
    Certification {safe_value(row['Certification'])}.
    Good payment history {safe_value(row['Good_Payment_History'])}.
    Prompt response {safe_value(row['Prompt_Response'])}.
    Hiring growth {safe_value(row['Hiring_Growth'])}.
    Engagement spike {safe_value(row['Engagement_Spike'])}.
    Intent score {safe_value(row['Intent_Score'])}.
    Preferred channel {safe_value(row['Preferred_Channel'])}.
    Response probability {safe_value(row['Response_Probability'])}.
    Tariff news impact {safe_value(row['Tariff_News'])}.
    Stock market shock {safe_value(row['StockMarket_Shock'])}.
    War event {safe_value(row['War_Event'])}.
    Natural calamity {safe_value(row['Natural_Calamity'])}.
    Currency fluctuation {safe_value(row['Currency_Fluctuation'])}.
    """

    records.append({
        "id": str(row["IMP_ID"]),
        "text": text_summary.strip(),

        # Identity
        "imp_id": str(row["IMP_ID"]),
        "buyer_id": str(row["Buyer_ID"]),
        "country": safe_value(row["Country"]),
        "industry": safe_value(row["Industry"]),
        "certification": safe_value(row["Certification"]),
        "preferred_channel": safe_value(row["Preferred_Channel"]),

        # Financial
        "revenue": safe_float(row["Revenue_Size_USD"]),
        "avg_order_tons": safe_float(row["Avg_Order_Tons"]),
        "team_size": safe_int(row["Team_Size"]),

        # Intent & engagement
        "intent_score": safe_float(row["Intent_Score"]),
        "response_probability": safe_float(row["Response_Probability"]),
        "prompt_response": safe_float(row["Prompt_Response"]),
        "engagement_spike": safe_int(row["Engagement_Spike"]),
        "decision_maker_change": safe_int(row["DecisionMaker_Change"]),
        "salesnav_profile_visits": safe_int(row["SalesNav_ProfileVisits"]),

        # Growth
        "hiring_growth": safe_int(row["Hiring_Growth"]),
        "funding_event": safe_int(row["Funding_Event"]),

        # Risk
        "tariff_news": safe_int(row["Tariff_News"]),
        "stock_market_shock": safe_int(row["StockMarket_Shock"]),
        "war_event": safe_int(row["War_Event"]),
        "natural_calamity": safe_int(row["Natural_Calamity"]),
        "currency_fluctuation": safe_float(row["Currency_Fluctuation"]),
    })

# Upload in batches
batch_size = 96

for i in range(0, len(records), batch_size):
    batch = records[i:i+batch_size]

    index.upsert_records(
        namespace="importers",      # default namespace
        records=batch
    )

    print(f"Uploaded batch {i//batch_size + 1}")