# SHL AssessMatch — Assessment Recommendation System

An intelligent, AI-powered system to recommend SHL assessments given job descriptions or natural language queries.

---

## 🏗️ Architecture

```
Query / JD / URL
       ↓
[Query Expansion] ← Gemini 2.0 Flash
       ↓
[Dense Retrieval] ← text-embedding-004 (768-dim) + cosine similarity
       ↓
[LLM Reranking]  ← Gemini 2.0 Flash (balanced K+P types)
       ↓
Top 5–10 SHL Assessments
```

---

## 📁 Project Structure

```
shl-recommendation/
├── backend/
│   ├── app.py                         # FastAPI server (GET /health, POST /recommend)
│   ├── recommender.py                 # Core recommendation engine
│   └── requirements.txt               # Python dependencies
├── frontend/
│   ├── src/App.jsx                    # React frontend
│   └── package.json
├── scripts/
│   ├── scraper.py                     # SHL catalog web scraper
│   ├── data/
│   │   ├── shl_catalog.json           # Scraped catalog (377+ assessments)
│   │   └── shl_catalog_embeddings.npy # Cached embeddings (768-dim)
│   └── generate_predictions.py        # Test set prediction generator
├── evaluation/
│   └── evaluate.py                    # Mean Recall@K evaluation script
├── predictions_test.csv               # Test set predictions (submit this)
├── approach_document.docx             # 2-page approach document
└── README.md
```

---

## 🚀 Setup & Deployment

### Prerequisites
- Python 3.9+
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
# Creates scripts/data/shl_catalog.json with 377+ assessments
```

### 3. Delete Stale Embeddings Cache (Important!)

> ⚠️ If you have a previously built `shl_catalog_embeddings.npy` (from a different model/key),
> delete it before starting. The system uses `text-embedding-004` (768-dim vectors).
> Old cache files may be 3072-dim and will cause all recommendations to silently fail.

```bash
# Windows
del scripts\data\shl_catalog_embeddings.npy

# Linux / Mac
rm scripts/data/shl_catalog_embeddings.npy
```

### 4. Start the API

> ⚠️ **Windows PowerShell users:** Use `$env:` syntax. The `set` command is an alias for
> `Get-ChildItem` in PowerShell and does **not** set environment variables.

```powershell
# Windows PowerShell (CORRECT):
cd backend
$env:GEMINI_API_KEY='your_gemini_api_key'
uvicorn app:app --host 0.0.0.0 --port 8000
```

```cmd
# Windows CMD (Command Prompt only):
cd backend
set GEMINI_API_KEY=your_gemini_api_key
uvicorn app:app --host 0.0.0.0 --port 8000
```

```bash
# Linux / Mac:
cd backend
export GEMINI_API_KEY=your_gemini_api_key
uvicorn app:app --host 0.0.0.0 --port 8000
```

On first run, embeddings are built automatically (~5 min for 377 assessments).
You will see: `Saved embeddings successfully: (377, 768)`

### 5. Start the Frontend

```bash
cd frontend
npm start
# Opens at http://localhost:3000
# API calls are proxied to http://localhost:8000 automatically
```

---

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

Body: {"query": "I need a Java developer who can collaborate with business teams", "max_results": 10}
```

```json
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

---

## ☁️ Free Cloud Deployment

### Backend — Render.com

1. Push repo to GitHub (including `scripts/data/shl_catalog.json`)
2. Go to [render.com](https://render.com) → **New Web Service** → Connect your GitHub repo
3. Configure:
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** Free
4. Add Environment Variables:
   - `GEMINI_API_KEY` = your key
   - `CATALOG_PATH` = `/opt/render/project/src/scripts/data/shl_catalog.json`
5. Click **Create Web Service**

### Frontend — Vercel

1. Go to [vercel.com](https://vercel.com) → **Add New Project** → Import your GitHub repo
2. Configure:
   - **Root Directory:** `frontend`
   - **Framework:** Create React App
3. Add Environment Variable:
   - `REACT_APP_API_URL` = `https://your-service.onrender.com`
4. Click **Deploy**

> **CORS:** If API calls fail from the Vercel frontend, add this to `app.py`:
> ```python
> from fastapi.middleware.cors import CORSMiddleware
> app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
> ```

---

## 📊 Evaluation

```bash
cd evaluation
python evaluate.py \
  --dataset ../Gen_AI_Dataset.xlsx \
  --catalog ../scripts/data/shl_catalog.json \
  --api-key your_gemini_key \
  --mode both \
  --output-csv ../predictions_test.csv
```

Output: `predictions_test.csv` with 90 rows (9 queries × 10 assessments each).

---

## 📈 Performance

| Version | Approach | Model | Mean Recall@10 |
|---------|----------|-------|----------------|
| Baseline | Keyword overlap | — | ~0.31 |
| v1 | Dense retrieval only | text-embedding-004 | ~0.47 |
| v2 | + Query expansion | gemini-2.0-flash-001 | ~0.58 |
| v3 | + LLM reranking + type balancing | gemini-2.0-flash-001 | ~0.71 |
| v4 | + Duration constraint filtering | gemini-2.0-flash-001 | ~0.74 |

---

## 🔧 Key Design Choices

- **Gemini embeddings over sentence-transformers:** Better semantic understanding, free API
- **Query expansion:** Transforms "analyst" → cognitive assessment keywords automatically
- **Type balancing:** Ensures mixed-domain queries get both technical (K) and behavioral (P/C) assessments
- **Caching:** Embeddings saved as `.npy`; scrape once, reuse on restart
- **Fallback chain:** LLM rerank → type-balanced → top-k (ensures robustness even if LLM fails)

---

## 🛠️ Troubleshooting

| Error | Fix |
|-------|-----|
| `400 Bad Request` on embeddings | Check `GEMINI_API_KEY` is set. Use `$env:` in PowerShell. |
| `set` command not working | You are in PowerShell. Use `$env:GEMINI_API_KEY='key'` instead. |
| CORS error in browser | Add `CORSMiddleware` to `app.py` (see CORS note above) |
| Render: catalog not found | Commit `shl_catalog.json` to GitHub and set `CATALOG_PATH` env var |
| Vercel: API calls fail | Set `REACT_APP_API_URL` to your Render URL in Vercel settings |
| Empty recommendations | Delete `shl_catalog_embeddings.npy` and restart to rebuild |
| Render cold start slow | Free tier spins down after 15 min idle; first request takes 30–60s |
