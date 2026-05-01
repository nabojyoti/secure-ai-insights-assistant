# Secure AI Insights Assistant

Backend-first implementation of the Futures First assignment: a secure internal analytics assistant that answers business questions using approved tools over SQL data, CSV ingestion, and PDF report retrieval.

## Architecture

```text
Client UI
  -> FastAPI /api/v1
    -> Auth + validation + request logging
    -> LangGraph orchestrator
      -> input guardrail
      -> planner
      -> approved tools
      -> output guardrail
      -> AnalyticsService over Postgres
      -> RAGTool over stored PDF chunks using LangChain Document metadata
      -> guarded SQLTool for internal read-only diagnostics
    -> SQLAlchemy models
      -> Postgres in Docker
```

The assistant never receives unrestricted file or database access. Routes call backend services/tools with explicit validation and source tracking.
LangGraph is used for orchestration only. The backend intentionally does not use a LangChain SQL agent because autonomous SQL generation is a poor fit for the assignment's privacy and access-boundary requirements.

## Run Locally

```bash
cp .env.example .env
python scripts/generate_demo_data.py
docker compose -f docker/docker-compose.yml up --build
```

Then open:

- API docs: `http://localhost:8000/docs`
- Liveness: `http://localhost:8000/health`
- Readiness: `http://localhost:8000/ready`

Create a demo token:

```bash
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"demo-user\",\"role\":\"analyst\"}"
```

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

## Assignment Coverage

- SQL source: Postgres tables for movies, viewers, watch activity, reviews, marketing spend, and regional performance.
- CSV source: controlled ingestion with dataset allowlist, schema checks, extension checks, size limit, and no arbitrary table names.
- PDF source: PDF upload, text chunk storage, keyword retrieval, source snippets.
- Explainability: chat responses include `sources` and `trace.tools_used`.
- Security: JWT auth, env-based secrets, upload limits, path restrictions, CORS config, sanitized app errors.
- Guardrails: explicit input guardrail blocks prompt injection, secret/file probing, and unsafe SQL intent; output guardrail enforces response shape, source/tool trace, and secret-like redaction.
- Agent stack: LangGraph workflow plus LangChain document utilities; no unrestricted SQL agent.
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
