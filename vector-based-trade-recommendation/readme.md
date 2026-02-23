# 🚀 Vector-Based Trade Recommendation System
Tipe Ai(Trade Intent Prediction Engine)
An AI-powered semantic trade intelligence engine that connects exporters, importers, and global trade events using Pinecone vector search.

---

## 📌 Project Overview

This system uses vector embeddings and semantic search to:

- 🔎 Discover exporters based on natural language queries
- 🛒 Identify high-intent importers
- 📰 Analyze global trade news impact
- 🌍 Enable intelligent trade matchmaking

Instead of traditional keyword search, this system uses vector similarity for intelligent results.

---

## 🧠 Technologies Used

- Python
- Pinecone Vector Database
- Semantic Search
- CSV Data Processing
- AI-powered text embeddings

---

## 📂 Project Structure

```
vector-based-trade-recommendation/
│
├── exporter.csv                # Exporter dataset
├── importer.csv                # Importer dataset
├── globalnews.csv              # Global trade news dataset
│
├── exporters_pinecone.py       # Upload exporter vectors
├── importers_pinecone.py       # Upload importer vectors
├── globalnews_pinecone.py      # Upload news vectors
│
├── main.py                     # Semantic retrieval engine
└── README.md
```

---

## ⚙️ How It Works

1. Data is converted into structured semantic records
2. Records are uploaded to Pinecone vector index
3. User enters natural language query
4. Pinecone performs embedding + cosine similarity search
5. Top matching records are returned

---

## 🔍 Example Queries

- "solar exporters in Gujarat with high revenue"
- "high intent medical device buyers in Asia"
- "tariff impact on textiles in Europe"

---

## 📊 Example Output

### Exporter Search

```
ID: EXP_10978
Similarity Score: 0.8799
Industry: Solar
State: Gujarat
Revenue: 1641312 USD
Intent Score: 0.27
```

### Importer Search

```
Buyer ID: BUY_74601
Country: Singapore
Industry: Medical Devices
Revenue: 39,521,655 USD
Intent Score: 0.43
```

### News Search

```
Region: Europe
Event Type: Tariff Update
Impact Level: High
Affected Industry: Textiles
```

---
## 📸 Output Screenshots
![Output](https://img.sanishtech.com/u/9c58f9e409a180ab0245cbae6221139e.png)
## 🎯 Key Features

- Semantic trade discovery
- Multi-namespace vector search
- Risk-aware trade analysis
- Intent-based importer ranking
- Real-time similarity scoring

---

## 🚀 Future Enhancements

- Trade Opportunity Scoring
- Risk-adjusted matchmaking
- Web dashboard using FastAPI
- AI-based trade recommendation ranking
- RAG integration for trade insights

---

## 👤 Authors

Darshan
Chandan
Harsh
Atharv

---

## 📌 License

This project is for academic and research purposes.