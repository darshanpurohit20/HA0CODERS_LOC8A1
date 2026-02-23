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
df = pd.read_csv("exporter.csv")

# Function to safely handle NaN
def safe_value(val):
    if pd.isna(val):
        return "Not available"
    return val

records = []

for _, row in df.iterrows():

    # Build FULL semantic record text
    text_summary = f"""
    Export record ID {safe_value(row['EXP_ID'])}.
    Exporter ID {safe_value(row['Exporter_ID'])}.
    Date {safe_value(row['Date'])}.
    State {safe_value(row['State'])}.
    Industry {safe_value(row['Industry'])}.
    MSME Udyam registered {safe_value(row['MSME_Udyam'])}.
    Manufacturing capacity {safe_value(row['Manufacturing_Capacity_Tons'])} tons.
    Revenue size {safe_value(row['Revenue_Size_USD'])} USD.
    Team size {safe_value(row['Team_Size'])}.
    Certification {safe_value(row['Certification'])}.
    Good payment terms {safe_value(row['Good_Payment_Terms'])}.
    Prompt response score {safe_value(row['Prompt_Response_Score'])}.
    Hiring signal {safe_value(row['Hiring_Signal'])}.
    LinkedIn activity {safe_value(row['LinkedIn_Activity'])}.
    SalesNav profile views {safe_value(row['SalesNav_ProfileViews'])}.
    SalesNav job change {safe_value(row['SalesNav_JobChange'])}.
    Intent score {safe_value(row['Intent_Score'])}.
    Shipment value {safe_value(row['Shipment_Value_USD'])} USD.
    Quantity exported {safe_value(row['Quantity_Tons'])} tons.
    Tariff impact {safe_value(row['Tariff_Impact'])}.
    Stock market impact {safe_value(row['StockMarket_Impact'])}.
    War risk {safe_value(row['War_Risk'])}.
    Natural calamity risk {safe_value(row['Natural_Calamity_Risk'])}.
    Currency shift {safe_value(row['Currency_Shift'])}.
    """

    records.append({
        "id": str(row["EXP_ID"]),  # record ID
        "text": text_summary.strip(),
        "exp_id": str(row["EXP_ID"]),
        "exporter_id": str(row["Exporter_ID"]),
        "state": safe_value(row["State"]),
        "industry": safe_value(row["Industry"]),
        "revenue": float(row["Revenue_Size_USD"]) if not pd.isna(row["Revenue_Size_USD"]) else 0,
        "intent_score": float(row["Intent_Score"]) if not pd.isna(row["Intent_Score"]) else 0,

        # Add these also
        "tariff_impact": float(row["Tariff_Impact"]) if not pd.isna(row["Tariff_Impact"]) else 0,
        "stock_market_impact": float(row["StockMarket_Impact"]) if not pd.isna(row["StockMarket_Impact"]) else 0,
        "war_risk": int(row["War_Risk"]) if not pd.isna(row["War_Risk"]) else 0,
        "natural_calamity_risk": int(row["Natural_Calamity_Risk"]) if not pd.isna(row["Natural_Calamity_Risk"]) else 0,
        "currency_shift": float(row["Currency_Shift"]) if not pd.isna(row["Currency_Shift"]) else 0,
})
        


# Upload in batches
batch_size = 96

for i in range(0, len(records), batch_size):
    batch = records[i:i+batch_size]

    index.upsert_records(
        namespace="exporters",      # default namespace
        records=batch
    )

    print(f"Uploaded batch {i//batch_size + 1}")
