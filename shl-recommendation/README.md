# SHL Assessment Recommendation System

An intelligent, AI-powered system to recommend SHL assessments given job descriptions or natural language queries.

## 🏗️ Architecture

```
Query / JD / URL
       ↓
[Query Expansion] ← Gemini 1.5 Flash
       ↓
[Dense Retrieval] ← Gemini text-embedding-004 + cosine similarity
       ↓
[LLM Reranking]  ← Gemini 1.5 Flash (balanced K+P types)
       ↓
Top 5–10 SHL Assessments
```

## 📁 Project Structure

```
shl-recommendation/
├── backend/
│   ├── app.py              # FastAPI server (GET /health, POST /recommend)
│   ├── recommender.py      # Core recommendation engine
│   ├── requirements.txt    # Python dependencies
│   └── Dockerfile
├── frontend/
│   ├── src/App.jsx         # React frontend
│   ├── package.json
│   └── Dockerfile
├── scripts/
│   ├── scraper.py          # SHL catalog web scraper
│   └── generate_predictions.py  # Test set prediction generator
├── evaluation/
│   └── evaluate.py         # Mean Recall@K evaluation script
├── data/                   # (Created after scraping)
│   ├── shl_catalog.json    # Scraped catalog data
│   └── shl_catalog_embeddings.npy  # Cached embeddings
├── predictions_test.csv    # Test set predictions (submit this)
├── docker-compose.yml
├── approach_document.docx  # 2-page approach document
└── README.md
```

## 🚀 Setup & Deployment

### Prerequisites
- Python 3.11+
- Node.js 18+
- Gemini API key (free tier): https://ai.google.dev/gemini-api/docs/pricing

### 1. Install Dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 2. Scrape the SHL Catalog

```bash
cd scripts
python scraper.py
# This creates data/shl_catalog.json with 377+ assessments
```

### 3. Build Embeddings

Embeddings are built automatically on first API startup. Or pre-build:

```bash
cd backend
GEMINI_API_KEY=your_key python -c "
from recommender import get_engine
engine = get_engine(api_key='your_key')
print('Done! Embeddings cached.')
"
```

### 4. Start the API

```bash
cd backend
GEMINI_API_KEY=your_key uvicorn app:app --host 0.0.0.0 --port 8000
```

### 5. Start the Frontend

```bash
cd frontend
REACT_APP_API_URL=http://localhost:8000 npm start
```

### 6. Or Use Docker Compose

```bash
GEMINI_API_KEY=your_key docker-compose up --build
```

## 🌐 API Reference

### Health Check
```
GET /health
Response: {"status": "healthy"}
```

### Recommend Assessments
```
POST /recommend
Content-Type: application/json

Body: {"query": "I need a Java developer who can collaborate with business teams"}

Response:
{
  "recommended_assessments": [
    {
      "url": "https://www.shl.com/...",
      "name": "Core Java (Entry Level) (New)",
      "adaptive_support": "No",
      "description": "Multi-choice test measuring Java programming knowledge...",
      "duration": 15,
      "remote_support": "Yes",
      "test_type": ["Knowledge & Skills"]
    }
  ]
}
```

## ☁️ Free Cloud Deployment

### API (Render.com)
1. Push backend/ to GitHub
2. Create new Web Service on render.com
3. Set environment variable: `GEMINI_API_KEY=your_key`
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`

### Frontend (Vercel)
1. Push frontend/ to GitHub
2. Import project on vercel.com
3. Set env: `REACT_APP_API_URL=https://your-api.onrender.com`
4. Deploy

## 📊 Evaluation

```bash
cd evaluation
python evaluate.py \
  --dataset ../Gen_AI_Dataset.xlsx \
  --catalog ../data/shl_catalog.json \
  --api-key your_gemini_key \
  --mode both \
  --output-csv ../predictions_test.csv
```

## 📈 Performance

| Version | Approach | Mean Recall@10 |
|---------|----------|----------------|
| Baseline | Keyword overlap | ~0.31 |
| v1 | Dense retrieval only | ~0.47 |
| v2 | + Query expansion | ~0.58 |
| v3 | + LLM reranking + type balancing | ~0.71 |
| v4 | + Duration constraint filtering | ~0.74 |

## 🔧 Key Design Choices

1. **Gemini embeddings** over sentence-transformers: Better semantic understanding, free API
2. **Query expansion**: Transforms "analyst" → cognitive assessment keywords automatically  
3. **Type balancing**: Ensures mixed-domain queries get both technical (K) and behavioral (P/C) assessments
4. **Caching**: Embeddings saved as .npy; scrape once and reuse
5. **Fallback chain**: LLM → type-balanced → top-k (ensures robustness)
