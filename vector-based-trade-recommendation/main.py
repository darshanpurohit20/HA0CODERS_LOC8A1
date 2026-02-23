# import os
# from pinecone import Pinecone
# from dotenv import load_dotenv

# print("🚀 Script started")

# load_dotenv()

# pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
# index = pc.Index(os.getenv("PINECONE_INDEX"))

# print("✅ Connected to index")

# print("📊 Stats:")
# print(index.describe_index_stats())


# response = index.search(
#     namespace="exporters",
#     query={
#         "inputs": {"text": "solar exporters in Gujarat"},
#         "top_k": 3
#     }
# )

# print("🔎 Raw response:")
# print(response)

import os
from pinecone import Pinecone
from dotenv import load_dotenv

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")

if not PINECONE_API_KEY:
    raise ValueError("❌ Missing PINECONE_API_KEY")

if not PINECONE_INDEX:
    raise ValueError("❌ Missing PINECONE_INDEX")

# -----------------------------
# Initialize Pinecone
# -----------------------------
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX)


# -----------------------------
# Retrieval Function
# -----------------------------

def retrieve(namespace, query, top_k=5, filters=None):

    query_payload = {
        "inputs": {"text": query},
        "top_k": top_k
    }

    if filters:
        query_payload["filter"] = filters

    response = index.search(
        namespace=namespace,
        query=query_payload
    )

    # 🔥 Correct parsing for 2025 API
    return response.get("result", {}).get("hits", [])
# -----------------------------
# Result Printer
# -----------------------------
def print_results(results, record_type):

    if not results:
        print("⚠️ No results found.\n")
        return

    for r in results:
        print("=" * 70)
        print("ID:", r.get("_id"))
        print("Similarity Score:", round(r.get("_score", 0), 4))

        fields = r.get("fields", {})

        # ---------------- EXPORTERS ----------------
        if record_type == "exporter":
            print("\n📦 EXPORTER DETAILS")
            print("Exporter ID:", fields.get("exporter_id"))
            print("State:", fields.get("state"))
            print("Industry:", fields.get("industry"))
            print("Revenue (USD):", fields.get("revenue"))
            print("Intent Score:", fields.get("intent_score"))
            print("Tariff Impact:", fields.get("tariff_impact"))
            print("Stock Market Impact:", fields.get("stock_market_impact"))
            print("War Risk:", fields.get("war_risk"))
            print("Natural Calamity Risk:", fields.get("natural_calamity_risk"))
            print("Currency Shift:", fields.get("currency_shift"))

        # ---------------- IMPORTERS ----------------
        elif record_type == "importer":
            print("\n🛒 IMPORTER DETAILS")
            print("Buyer ID:", fields.get("buyer_id"))
            print("Country:", fields.get("country"))
            print("Industry:", fields.get("industry"))
            print("Revenue (USD):", fields.get("revenue"))
            print("Avg Order (Tons):", fields.get("avg_order_tons"))
            print("Team Size:", fields.get("team_size"))
            print("Certification:", fields.get("certification"))
            print("Preferred Channel:", fields.get("preferred_channel"))
            print("Intent Score:", fields.get("intent_score"))
            print("Response Probability:", fields.get("response_probability"))
            print("Hiring Growth:", fields.get("hiring_growth"))
            print("Engagement Spike:", fields.get("engagement_spike"))
            print("War Event:", fields.get("war_event"))
            print("Natural Calamity:", fields.get("natural_calamity"))
            print("Currency Fluctuation:", fields.get("currency_fluctuation"))

        # ---------------- NEWS ----------------
        elif record_type == "news":
            print("\n📰 NEWS DETAILS")
            print("News ID:", fields.get("news_id"))
            print("Date:", fields.get("date"))
            print("Region:", fields.get("region"))
            print("Event Type:", fields.get("event_type"))
            print("Impact Level:", fields.get("impact_level"))
            print("Affected Industry:", fields.get("affected_industry"))
            print("Tariff Change:", fields.get("tariff_change"))
            print("Stock Market Shock:", fields.get("stock_market_shock"))
            print("Currency Shift:", fields.get("currency_shift"))
            print("War Flag:", fields.get("war_flag"))
            print("Natural Calamity Flag:", fields.get("natural_calamity_flag"))

        print("=" * 70)
        print()

    if not results:
        print("⚠️ No results found.\n")
        return

    for r in results:
        print("ID:", r.get("_id"))
        print("Score:", r.get("_score"))

        fields = r.get("fields", {})

        print("Industry:", fields.get("industry"))
        print("State:", fields.get("state"))
        print("Revenue:", fields.get("revenue"))
        print("-" * 50)
# -----------------------------
# MAIN
# -----------------------------

if __name__ == "__main__":

    exporter_query = "solar exporters in Gujarat with high revenue"
    print("\n--- Exporter Results ---")
    print("🔍 Query:", exporter_query)
    exporters = retrieve(
        namespace="exporters",
        query=exporter_query
    )
    print_results(exporters, "exporter")


    importer_query = "high intent medical device buyers in Asia"
    print("\n--- Importer Results ---")
    print("🔍 Query:", importer_query)
    importers = retrieve(
        namespace="importers",
        query=importer_query
    )
    print_results(importers, "importer")


    news_query = "tariff impact on textiles in Europe"
    print("\n--- News Results ---")
    print("🔍 Query:", news_query)
    news = retrieve(
        namespace="globalnews",
        query=news_query
    )
    print_results(news, "news")