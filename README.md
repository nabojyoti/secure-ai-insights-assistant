# Secure AI Insights Assistant 🔐

> A secure, production-ready AI-powered analytics assistant that safely answers business questions using multiple private data sources while maintaining strong access boundaries and security guarantees.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-red.svg)](LICENSE)

---

## 📋 Overview

The Secure AI Insights Assistant is an internal analytics platform that intelligently combines data from multiple sources to answer business questions while maintaining strict security and privacy boundaries.

**Key Features:**
- 🔐 **Secure Multi-Source Integration**: SQL databases, CSV files, and PDF documents
- 🛡️ **Guardrail Architecture**: Input & output validation with safety constraints
- 📊 **Multi-Tool Orchestration**: LangGraph-based tool planning and execution
- 📈 **Rich Analytics**: Pre-built tools for performance, engagement, and ROI analysis
- 🔍 **Source Attribution**: Transparent tracking of data sources used in answers
- 🛠️ **Tool-Based Access**: No unrestricted database/file access to LLMs
- 🚀 **Production Ready**: Logging, error handling, Docker containerization

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client (React/Next.js)                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    FastAPI Backend (8000)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  /api/v1 Routes                                      │  │
│  │  • Auth (JWT with role-based access)                 │  │
│  │  • Chat (orchestrator entry point)                   │  │
│  │  • Analytics (direct data access)                    │  │
│  │  • Ingestion (CSV/PDF upload & processing)          │  │
│  └──────────────┬───────────────────────────────────────┘  │
│                 │                                            │
│  ┌──────────────▼───────────────────────────────────────┐  │
│  │  LangGraph Orchestrator (Stateful Workflow)          │  │
│  │                                                       │  │
│  │  1️⃣  Input Guardrail ────────────────────────┐      │  │
│  │  2️⃣  Planner (tool selection) ──────────────┤      │  │
│  │  3️⃣  Execute Approved Tools ────────────────┤      │  │
│  │      ├─ SQLTool (read-only queries)          │      │  │
│  │      ├─ RAGTool (PDF semantic search)        │      │  │
│  │      └─ Analytics Service (typed queries)    │      │  │
│  │  4️⃣  Build Evidence Layer ──────────────────┤      │  │
│  │  5️⃣  Compose Candidate Answer ──────────────┤      │  │
│  │  6️⃣  Optional: LLM Synthesis (OpenAI) ──────┤      │  │
│  │  7️⃣  Output Guardrail ──────────────────────┤      │  │
│  │  8️⃣  Persist Chat History ──────────────────┘      │  │
│  └──────────────┬───────────────────────────────────────┘  │
│                 │                                            │
└─────────────────┼────────────────────────────────────────────┘
                  │
        ┌─────────┴─────────┬──────────┬──────────┐
        │                   │          │          │
┌───────▼──────┐  ┌────────▼───┐  ┌──▼──────┐  ┌▼────────┐
│  PostgreSQL  │  │ SQLAlchemy │  │ LangChain  │  │ Vector  │
│  (5432)      │  │ ORM        │  │ Documents  │  │ Store   │
│              │  │ Models     │  │ (RAG)      │  │ (PDF)   │
└──────────────┘  └────────────┘  └────────────┘  └─────────┘
```

**Design Philosophy:**
- No autonomous SQL generation (LLMs never generate raw queries)
- Tool-based access (all data access through pre-built services)
- Guardrails first (safety validation before & after reasoning)
- Source tracking (audit trail for every answer)
- Graceful degradation (deterministic fallback when AI fails)

See [SETUP.md](SETUP.md) for detailed setup instructions.

---

## 🚀 Quick Start (5 minutes)

```bash
# 1. Clone
git clone <repo-url>
cd secure-ai-insights-assistant

# 2. Setup environment
cp .env.example .env

# 3. Install dependencies
pip install -e .
# or: uv pip install -e .

# 4. Start services
docker compose -f docker/docker-compose.yml up --build

# 5. Seed demo data (in another terminal)
python scripts/generate_demo_data.py
```

**Access the app:**
- 📖 **API Docs**: http://localhost:8000/docs
- 🌐 **Frontend**: http://localhost:5173

**Create a token:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"user_id":"demo-user","role":"analyst"}'
```

---

## 📚 Features

### ✅ What This System Does

| Feature | Example |
|---------|---------|
| **Multi-Source Analysis** | "Which titles performed best?" → Queries SQL + PDF reports |
| **Guardrailed Reasoning** | Input validated → Tools executed → Output validated |
| **Source Attribution** | Every answer shows which data sources were used |
| **Rich Analytics** | Top performers, weak genres, regional engagement, ROI analysis |
| **Optional LLM Synthesis** | Can use OpenAI to refine answers (gracefully degrades if unavailable) |
| **Transparent Logging** | Detailed execution trace for debugging & auditing |

### ❌ What This System Does NOT Do

| Feature | Why |
|---------|-----|
| **Autonomous SQL Generation** | Security risk; no LLM-generated queries ever executed |
| **Unrestricted Data Access** | All access controlled via typed service methods |
| **Hallucination Without Evidence** | Answers grounded in actual data only |
| **Untracked Operations** | Every tool call logged with user & query context |

---

## 📦 Project Structure

```
secure-ai-insights-assistant/
├── app/                              # Main application
│   ├── api/v1/
│   │   ├── auth.py                  # JWT token generation
│   │   ├── chat.py                  # Chat endpoint
│   │   ├── analytics.py             # Direct analytics
│   │   └── ingestion.py             # File uploads
│   ├── agents/
│   │   ├── orchestrator.py          # LangGraph workflow
│   │   └── planner.py               # Tool selection
│   ├── tools/
│   │   ├── sql_tool.py              # Read-only SQL (guarded)
│   │   ├── rag_tool.py              # PDF retrieval
│   │   └── csv_tool.py              # CSV access
│   ├── services/
│   │   ├── analytics_service.py     # Typed analytics
│   │   ├── answer_synthesizer.py    # Optional LLM layer
│   │   ├── evidence_service.py      # Citation building
│   │   └── ingestion_service.py     # Document processing
│   ├── core/
│   │   ├── config.py                # Environment config
│   │   ├── db.py                    # Database session
│   │   ├── logger.py                # Logging setup
│   │   └── exceptions.py            # Custom exceptions
│   ├── auth/
│   │   ├── security.py              # JWT utils
│   │   └── dependencies.py          # FastAPI Depends
│   ├── models/
│   │   ├── db_models.py             # SQLAlchemy ORM
│   │   └── schemas.py               # Pydantic schemas
│   ├── guardrails/                  # Safety validation
│   └── common_utils/
│       └── logging_utils.py         # Logging setup
│
├── data/
│   ├── csv/                         # Business data files
│   └── pdf/                         # Document corpus
├── scripts/
│   └── generate_demo_data.py       # Demo data generator
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── SETUP.md                         # Detailed setup guide
├── README.md                        # This file
└── pyproject.toml                   # Dependencies
```

**See [README.md#project-structure](README.md#-project-structure) for full details.**

---

## 🔧 Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Backend** | FastAPI 0.109 | Speed, async support, auto docs |
| **Orchestration** | LangGraph | State management, workflow control |
| **Database** | PostgreSQL 15 | Reliability, JSONB support |
| **ORM** | SQLAlchemy 2.0 | Type safety, migration support |
| **Auth** | PyJWT | Lightweight JWT implementation |
| **AI** | LangChain + OpenAI | LLM integration (optional) |
| **Validation** | Pydantic | Schema validation, serialization |
| **Logging** | Python logging | Structured, centralized logging |
| **Container** | Docker | Reproducible deployment |

---

## 🔐 Security Features

### Input Validation
- Query length checks
- SQL injection prevention
- Malicious pattern detection

### Output Validation  
- Response safety checks
- Hallucination detection
- Source verification

### Access Control
- JWT-based authentication
- Role-based authorization
- Request logging & auditing

### Data Protection
- Read-only database access
- No raw file downloads
- Parameterized queries only

---

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| **[README.md](README.md)** | Project overview, architecture, features |
| **[SETUP.md](SETUP.md)** | Installation, configuration, deployment |
| **API Docs** | http://localhost:8000/docs (Swagger UI) |

---

## 🚀 Deployment

### Docker Compose (Development)
```bash
docker compose -f docker/docker-compose.yml up --build
```

### Production
See [SETUP.md#production-deployment](SETUP.md#production-deployment) for:
- Cloud platform setup (AWS, GCP, Heroku)
- Environment configuration
- Database backups
- Monitoring & logging

---

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=app

# Specific test file
pytest tests/test_chat.py -v
```

---

## 📊 Example Queries

The system can answer questions like:

1. **"Which titles performed best in 2025?"**
   - Uses SQL analytics → Returns top performers with metrics

2. **"Why is Stellar Run trending?"**
   - Uses SQL + PDF documents → Data + contextual insights

3. **"Which city had the strongest engagement?"**
   - Uses regional performance data → Geographic analysis

4. **"What explains weak comedy performance?"**
   - Uses genre analysis + policy docs → Root cause analysis

5. **"What should leadership do next quarter?"**
   - Uses all data sources → Strategic recommendations

See [SETUP.md#step-4-try-a-chat-query](SETUP.md#step-4-try-a-chat-query) for API examples.

---

## 🎯 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Tool-Based over LLM SQL** | Security >> flexibility |
| **Deterministic Default** | Reliability >> fancy AI |
| **Guardrails First** | Safety before features |
| **Optional LLM Synthesis** | Cost control + graceful fallback |
| **Source Attribution** | Transparency & auditability |

See [README.md#assumptions--tradeoffs](README.md#-assumptions--tradeoffs) for full details.

---

## 🆘 Troubleshooting

Common issues and solutions in [SETUP.md#troubleshooting](SETUP.md#troubleshooting):

- PostgreSQL connection errors
- Port conflicts
- JWT token issues
- OpenAI rate limits
- Docker build failures

---

## 📞 Support

- 📖 **Docs**: [SETUP.md](SETUP.md) for detailed setup
- 🐛 **Issues**: GitHub Issues
- 💬 **Discussions**: GitHub Discussions  
- 📧 **Contact**: See LICENSE

---

## 📄 License

MIT License - See LICENSE file for details

---

**Built with ❤️ | [Setup Guide](SETUP.md) | [Full Architecture](README.md#-architecture)**

Use the returned bearer token for protected routes. Seed demo data:

```bash
curl -X POST http://localhost:8000/api/v1/ingestion/seed \
  -H "Authorization: Bearer <token>"
```

To load generated CSV files through the ingestion API, use `POST /api/v1/ingestion/csv` for each file in `data/csv`. To load generated PDFs, use `POST /api/v1/ingestion/pdf` for each file in `data/pdf`.

If you edit the report text files in `data/pdf/*.txt`, rebuild the matching PDFs with:

```bash
python scripts/sync_txt_to_pdf.py
```

Ask one of the required questions:

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"Why is Stellar Run trending recently?\"}"
```

## Main APIs

- `GET /health`
- `GET /ready`
- `POST /api/v1/auth/token`
- `POST /api/v1/ingestion/seed`
- `POST /api/v1/ingestion/csv`
- `POST /api/v1/ingestion/pdf`
- `POST /api/v1/chat`
- `GET /api/v1/analytics/top-titles`
- `GET /api/v1/analytics/compare-titles`
- `GET /api/v1/analytics/strongest-city`
- `GET /api/v1/analytics/weak-genres`
- `GET /api/v1/analytics/audience-segments`

## Frontend

The React frontend lives in `frontend/` and provides:

- Chat assistant UI with sample assignment questions.
- Year/month filters and seeded-data reconnect action.
- Insights panel with title revenue chart, strongest city, weak genres, and audience segments.
- Tool trace and source snippets from the backend response.
- Query history for recent prompts.

Run only the frontend locally:

```bash
cd frontend
npm install
npm run dev
```

The frontend expects the backend at `http://localhost:8000`. Override with `frontend/.env`:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

Optional OpenAI answer synthesis is disabled by default. Enable it only when you want LLM-written final wording over already-retrieved evidence:

```bash
ENABLE_LLM_SYNTHESIS=true
OPENAI_API_KEY=<your-key>
```

## Assignment Coverage

- SQL source: Postgres tables for movies, viewers, watch activity, reviews, marketing spend, and regional performance.
- CSV source: controlled ingestion with dataset allowlist, schema checks, extension checks, size limit, and no arbitrary table names.
- PDF source: PDF upload, text chunk storage, keyword retrieval, source snippets.
- Explainability: chat responses include `sources` and `trace.tools_used`.
- Security: JWT auth, env-based secrets, upload limits, path restrictions, CORS config, sanitized app errors.
- Guardrails: explicit input guardrail blocks prompt injection, secret/file probing, and unsafe SQL intent; output guardrail enforces response shape, source/tool trace, and secret-like redaction.
- Agent stack: LangGraph workflow plus LangChain document utilities; no unrestricted SQL agent.
- Optional LLM synthesis: evidence from approved SQL/PDF tools can be summarized by OpenAI when `ENABLE_LLM_SYNTHESIS=true`; deterministic fallback remains the default.
- Multi-source routing: explanatory, weak-performance, and leadership/recommendation questions are planned to combine SQL metrics with PDF evidence.
- Observability: request IDs, request logging, health/readiness endpoints, tool trace persistence.

## Tests

```bash
pip install -r requirements.txt
pytest
```

Tests use SQLite by default and validate auth, SQL safety, analytics, ingestion controls, and chat orchestration.

## Assumptions and Tradeoffs

- Postgres is the production-like default through Docker; SQLite remains useful for local tests.
- The AI layer is provider-configurable, but answers are deterministic from tool outputs so the demo works without spending model calls.
- Demo data and report snippets are generated because the assignment permits random/demo datasets.
- Alembic can be added later; this version uses explicit SQLAlchemy table initialization to keep setup simple for evaluators.
