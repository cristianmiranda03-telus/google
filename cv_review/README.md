# CV Review v2 — Google Team

A fully redesigned, Next.js-powered CV evaluation platform with real-time analysis progress,
rich metrics, and a manager-ready dashboard.

## What's new vs v1

| Feature | v1 (Streamlit) | v2 (Next.js + FastAPI) |
|---|---|---|
| Frontend | Streamlit (Python) | Next.js 14 + Tailwind CSS |
| UX | Basic upload → results | Drag & drop, real-time progress, animated results |
| Dashboard | ❌ | ✅ Analysis history, best candidates per area |
| Metrics | ❌ | ✅ AI time, API calls, tokens, human time saved |
| History | ❌ | ✅ Persistent JSON storage |
| Charts | ❌ | ✅ Area distribution, AI time trend |
| API | No REST API | Full REST API (FastAPI) |

## Architecture

```
cv_review_v2/
├── backend/          Python FastAPI server
│   ├── main.py       REST API endpoints
│   ├── src/
│   │   ├── evaluator.py     CV evaluation with progress callbacks + metrics
│   │   ├── storage.py       Persistent JSON history & metrics aggregation
│   │   ├── cv_parser.py     PDF/TXT/DOCX text extraction
│   │   ├── fuelix_client.py Fuelix AI API client
│   │   └── prompts.py       Evaluation prompt templates
│   ├── config/
│   │   ├── config.yaml      App & API config
│   │   └── skill_matrix.yaml 13 specializations across 5 areas
│   └── data/
│       └── analyses.json    Persistent analysis history
└── frontend/         Next.js 14 app
    ├── app/
    │   ├── page.tsx          CV upload + real-time analysis
    │   ├── dashboard/        Analytics dashboard
    │   └── analysis/[id]/    Individual analysis detail
    └── components/           UI components
```

## Quick Start

### 1. Backend (Python/FastAPI)

```powershell
cd cv_review_v2\backend

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API key
copy .env.example .env
# Edit .env and set FUELIX_API_KEY=your_key_here

# Start server (port 8000)
uvicorn main:app --reload --port 8000
```

### 2. Frontend (Next.js)

```powershell
cd cv_review_v2\frontend

# Install dependencies
npm install

# Start dev server (port 3000)
npm run dev
```

Open http://localhost:3000

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/evaluate | Upload CV, start analysis |
| GET | /api/jobs/{id} | Poll analysis progress |
| GET | /api/analyses | List all past analyses |
| GET | /api/analyses/{id} | Get specific analysis |
| DELETE | /api/analyses/{id} | Delete analysis |
| GET | /api/metrics | Usage & time metrics |
| GET | /api/best-candidates | Top candidate per area |
| GET | /api/health | Health check |

## Key Metrics Tracked

- **AI analysis time** — actual seconds for full evaluation
- **API calls per analysis** — number of AI model calls (~16–17)
- **Token usage** — total tokens consumed (if available from API)
- **Human time saved** — estimated 45 min/CV × number of CVs analyzed
- **Best-fit area distribution** — where most candidates fit

## Environment Variables

```env
FUELIX_API_KEY=your_secret_token   # Required
FUELIX_MODEL=gemini-3-pro          # Optional (default)
FUELIX_BASE_URL=https://api.fuelix.ai/v1  # Optional
```

```env
NEXT_PUBLIC_API_URL=http://localhost:8000  # Frontend (optional)
```
