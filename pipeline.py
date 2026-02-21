import chromadb
import ollama
import pandas as pd

# ==============================
# LOAD CLEANED DATA
# ==============================

importer = pd.read_csv("cleaned_importer.csv")
exporter = pd.read_csv("cleaned_exporter.csv")

print("Cleaned data loaded ✅")

# ==============================
# INIT CHROMA (Persistent)
# ==============================

client = chromadb.Client(
    chromadb.Settings(persist_directory="./chroma_db")
)

importer_collection = client.get_or_create_collection(name="importers")
exporter_collection = client.get_or_create_collection(name="exporters")

# ==============================
# EMBEDDING FUNCTION
# ==============================

def get_embedding(text):
    response = ollama.embeddings(
        model="nomic-embed-text",
        prompt=text
    )
    return response["embedding"]

# ==============================
# ADD DATA TO VECTOR DB
# ==============================

def add_to_collection(df, collection, id_column):
    for _, row in df.iterrows():
        collection.add(
            ids=[str(row[id_column])],
            documents=[row["rag_text"]],
            embeddings=[get_embedding(row["rag_text"])],
            metadatas=[{"industry": row["Industry"]}]
        )

print("Adding Importers...")
add_to_collection(importer, importer_collection, "Buyer_ID")

print("Adding Exporters...")
add_to_collection(exporter, exporter_collection, "Exporter_ID")

client.persist()
print("Vector DB Ready ✅")

# ==============================
# MATCH FUNCTION
# ==============================

def find_best_exporters_for_importer(importer_id):

    # Get importer row
    importer_row = importer[importer["Buyer_ID"] == importer_id].iloc[0]

    importer_text = importer_row["rag_text"]
    importer_industry = importer_row["Industry"]

    query_embedding = get_embedding(importer_text)

    # Retrieve exporters from same industry
    results = exporter_collection.query(
        query_embeddings=[query_embedding],
        n_results=5,
        where={"industry": importer_industry}
    )

    exporter_context = "\n".join(results["documents"][0])

    prompt = f"""
You are a global trade matchmaking AI.

Importer Profile:
{importer_text}

Potential Exporters:
{exporter_context}

Rank the best exporters and explain reasoning based on:
- Industry alignment
- Revenue strength
- Risk exposure
- Intent signals
- Trade capacity
"""

    response = ollama.chat(
        model="llama3",
        messages=[{"role": "user", "content": prompt}]
    )

    return response["message"]["content"]

# ==============================
# TEST MATCH
# ==============================

if __name__ == "__main__":

    test_importer_id = importer.iloc[0]["Buyer_ID"]

    print(f"\n🔎 Matching for Importer: {test_importer_id}\n")

    result = find_best_exporters_for_importer(test_importer_id)

    print(result)