import chromadb
from chromadb.config import Settings
import ollama
import pandas as pd
import time
import os
from datetime import datetime

# ==========================================================
# CONFIGURATION
# ==========================================================
EMBED_MODEL = "nomic-embed-text" 
CHAT_MODEL = "llama3"
BATCH_SIZE = 32      
MAX_TEXT_LENGTH = 800
DB_PATH = "./chroma_db"

# ==========================================================
# STEP 1: INITIALIZE CLIENT & WIPE OLD DATA SAFELY
# ==========================================================
# Instead of deleting the folder, we tell Chroma to clear itself internally
client = chromadb.PersistentClient(
    path=DB_PATH,
    settings=Settings(allow_reset=True)
)

print(f"🧹 Resetting database at {DB_PATH} for a fresh rewrite...")
try:
    client.reset() 
except Exception as e:
    print(f"💡 Info: Database was already clean or empty.")

# Define collections after reset
importer_collection = client.get_or_create_collection("importers")
exporter_collection = client.get_or_create_collection("exporters")

# ==========================================================
# STEP 2: LOAD & DEDUPLICATE (CONSIDERING ALL ROWS)
# ==========================================================
print("🔹 Loading CSV files...")
importer = pd.read_csv("cleaned_importer.csv")
exporter = pd.read_csv("cleaned_exporter.csv")

# ChromaDB strictly requires unique IDs. We drop duplicates to prevent crashes.
importer = importer.drop_duplicates(subset=["Buyer_ID"]).reset_index(drop=True)
exporter = exporter.drop_duplicates(subset=["Exporter_ID"]).reset_index(drop=True)

print(f"Total Unique Importers to process: {len(importer)}")
print(f"Total Unique Exporters to process: {len(exporter)}")

# ==========================================================
# STEP 3: FALLBACK TEXT GENERATION (NO ROWS LEFT BEHIND)
# ==========================================================
def fill_missing_text(row, is_importer=True):
    # If the text is empty/NaN, we build it from other columns
    if pd.isna(row["rag_text"]) or str(row["rag_text"]).strip() == "":
        type_str = "Buyer" if is_importer else "Exporter"
        location = row.get("Country", row.get("State", "Unknown"))
        industry = row.get("Industry", "General Trade")
        rev = row.get("Revenue_Size_USD", "Confidential")
        return f"{type_str} from {location} in {industry} industry. Revenue: {rev} USD."
    return row["rag_text"]

importer["rag_text"] = importer.apply(lambda r: fill_missing_text(r, True), axis=1)
exporter["rag_text"] = exporter.apply(lambda r: fill_missing_text(r, False), axis=1)

# Final cleanup
importer["rag_text"] = importer["rag_text"].astype(str).str.slice(0, MAX_TEXT_LENGTH)
exporter["rag_text"] = exporter["rag_text"].astype(str).str.slice(0, MAX_TEXT_LENGTH)

# ==========================================================
# STEP 4: EMBEDDING & POPULATION
# ==========================================================
def embed_batch(texts):
    embeddings = []
    for text in texts:
        safe_text = str(text).strip() if (pd.notna(text) and str(text).strip() != "") else "Empty"
        response = ollama.embeddings(model=EMBED_MODEL, prompt=safe_text)
        embeddings.append(response["embedding"])
    return embeddings

def populate(df, collection, id_col):
    print(f"\n🚀 Processing {collection.name}...")
    texts = df["rag_text"].tolist()
    ids = df[id_col].astype(str).tolist()
    industries = df["Industry"].fillna("Unknown").astype(str).tolist()

    for i in range(0, len(texts), BATCH_SIZE):
        b_texts = texts[i:i+BATCH_SIZE]
        b_ids = ids[i:i+BATCH_SIZE]
        b_metas = [{"industry": ind} for ind in industries[i:i+BATCH_SIZE]]
        
        embeddings = embed_batch(b_texts)
        collection.add(ids=b_ids, documents=b_texts, embeddings=embeddings, metadatas=b_metas)
        
        if (i + BATCH_SIZE) % 256 == 0 or (i + BATCH_SIZE) >= len(texts):
            print(f"   ✅ Indexed {min(i+BATCH_SIZE, len(texts))} / {len(texts)}")

populate(importer, importer_collection, "Buyer_ID")
populate(exporter, exporter_collection, "Exporter_ID")

# ==========================================================
# STEP 5: MATCHING & OUTPUT
# ==========================================================
def get_match(importer_id):
    target = importer[importer["Buyer_ID"] == importer_id].iloc[0]
    query_vec = embed_batch([target["rag_text"]])[0]
    
    results = exporter_collection.query(
        query_embeddings=[query_vec],
        n_results=5,
        where={"industry": str(target["Industry"])}
    )

    if not results["documents"][0]:
        return "No industry matches found."

    context = "\n\n".join(results["documents"][0])
    prompt = f"Analyze and rank these exporters for buyer {importer_id}:\nBuyer: {target['rag_text']}\n\nExporters:\n{context}"
    
    response = ollama.chat(model=CHAT_MODEL, messages=[{"role": "user", "content": prompt}])
    return response["message"]["content"]

if __name__ == "__main__":
    first_buyer = importer.iloc[0]["Buyer_ID"]
    print(f"\n🔎 Matching for {first_buyer}...")
    output = get_match(first_buyer)
    print("\n" + "="*40 + "\n" + output + "\n" + "="*40)
    
    with open("match_result.txt", "w", encoding="utf-8") as f:
        f.write(output)
