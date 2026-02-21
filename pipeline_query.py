import chromadb
import ollama
from ollama import Client
import pandas as pd

# ==========================================================
# CONFIGURATION
# ==========================================================
DB_PATH = "./chroma_db"
EMBED_MODEL = "nomic-embed-text" 
CHAT_MODEL = "phi3"  # Stable 2.2GB model for your 4.2GB RAM limit

# FIX: Explicitly define the Ollama connection address
# This solves the "Failed to connect" error
ollama_client = Client(host='http://127.0.0.1:11434')

# Connect to your existing vectorized database
print("🔹 Connecting to Vector Database...")
client = chromadb.PersistentClient(path=DB_PATH)
exporters_col = client.get_collection("exporters")

def run_rag_query(user_query):
    # 1. Convert user query to embedding
    print(f"\n1. 🔄 Converting query to tokens using {EMBED_MODEL}...")
    response = ollama_client.embeddings(model=EMBED_MODEL, prompt=user_query)
    query_vec = response["embedding"]

    # 2. Search Vector DB
    print(f"2. 🔎 Searching Vector DB for matches...")
    results = exporters_col.query(
        query_embeddings=[query_vec],
        n_results=3
    )

    # Prepare context for the AI
    if not results["documents"] or len(results["documents"][0]) == 0:
        return "No matching exporters found in the database."

    context = "\n\n".join(results["documents"][0])
    
    # 3. Generate Answer with LLM
    print(f"3. 🧠 Generating response with {CHAT_MODEL}...")
    
    system_prompt = f"""
    You are a Trade Matchmaking Expert. Use the provided exporter data to answer the query.
    Rank the results based on how well they match the user's requirements.
    
    DATA FROM DATABASE:
    {context}
    """

    response = ollama_client.chat(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ]
    )

    return response["message"]["content"]

# ==========================================================
# INTERACTIVE LOOP
# ==========================================================
if __name__ == "__main__":
    print("\n✅ --- Trade Matchmaker AI is Online ---")
    print("Ollama Connection: http://127.0.0.1:11434")
    print("(Type 'exit' to stop)")
    
    while True:
        user_input = input("\n👤 Enter your query: ")
        
        if user_input.lower() in ['exit', 'quit']:
            print("👋 Exiting Trade Matchmaker.")
            break
            
        if not user_input.strip():
            continue

        try:
            answer = run_rag_query(user_input)
            print("\n🤖 AI RESPONSE:")
            print("-" * 60)
            print(answer)
            print("-" * 60)
        except Exception as e:
            print(f"❌ Connection/Process Error: {e}")
            print("👉 Tip: Make sure the Ollama app is open and you see the Llama icon in your taskbar.")