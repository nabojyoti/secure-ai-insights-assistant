# Setup Instructions 🚀

Complete guide to setting up and running the Secure AI Insights Assistant locally and in production.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development](#local-development)
3. [Configuration](#configuration)
4. [Database Setup](#database-setup)
5. [Running the Application](#running-the-application)
6. [Demo & Testing](#demo--testing)
7. [Production Deployment](#production-deployment)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required

- **Python 3.11+** - [Download](https://www.python.org/downloads/)
  ```bash
  python --version
  # Expected: Python 3.11.x or higher
  ```

- **Docker & Docker Compose** - [Download](https://www.docker.com/products/docker-desktop)
  ```bash
  docker --version
  docker compose version
  # Expected: Docker version 20.10+ and Docker Compose 2.0+
  ```

- **Git** - [Download](https://git-scm.com/downloads)
  ```bash
  git --version
  ```

### Optional

- **Visual Studio Code** - For development
- **Postman** or **curl** - For API testing
- **OpenAI API Key** - Only if enabling LLM synthesis

---

## Local Development

### Step 1: Clone the Repository

```bash
# Option A: Using Git
git clone https://github.com/yourusername/secure-ai-insights-assistant.git
cd secure-ai-insights-assistant

# Option B: Using direct download (if not using git)
# Download the ZIP and extract, then:
cd secure-ai-insights-assistant
```

### Step 2: Create Environment File

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your settings (see Configuration section below)
# On Windows with VS Code:
code .env

# On macOS/Linux:
nano .env
```

### Step 3: Create Python Virtual Environment

**Option A: Using `venv` (built-in)**

```bash
# Create virtual environment
python -m venv .venv

# Activate it
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# You should see (.venv) in your prompt
```

**Option B: Using `uv` (faster alternative)**

```bash
# Install uv if you haven't
pip install uv

# Create and activate
uv venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

### Step 4: Install Dependencies

```bash
# Using uv (recommended, faster)
uv pip install -e .

# OR using pip
pip install -e .

# Verify installation
python -c "import fastapi; print('FastAPI installed:', fastapi.__version__)"
```

Expected output:
```
FastAPI installed: 0.109.0
```

---

## Configuration

### `.env` File Setup

Create or edit `.env` with the following variables:

#### Database Configuration

```dotenv
# PostgreSQL connection string
# Format: postgresql+psycopg2://username:password@host:port/database
DATABASE_URL=postgresql+psycopg2://secure_ai:secure_ai_password@localhost:5432/secure_ai
```

#### Security

```dotenv
# JWT Secret (generate with: python -c "import secrets; print(secrets.token_urlsafe(32))")
JWT_SECRET=your-super-secret-key-at-least-32-characters-long

# JWT Algorithm (keep as is)
JWT_ALGORITHM=HS256

# Token expiration in minutes
JWT_EXPIRE_MINUTES=60
```

**Generate a secure secret:**
```bash
python -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(32))"
```

Copy output to `.env`.

#### CORS Configuration

```dotenv
# Allowed frontend origins (comma-separated)
# Local development:
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8000

# Production:
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

#### File & Data Configuration

```dotenv
# Directory for uploaded files and data
DATA_DIR=data

# Maximum upload size in MB
MAX_UPLOAD_MB=50

# Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO
```

#### AI/LLM Configuration (Optional)

```dotenv
# AI Provider: openai, anthropic, or local
AI_PROVIDER=openai

# Model name
AI_MODEL=gpt-4o-mini

# OpenAI API Key (leave empty to disable)
# Get from: https://platform.openai.com/api-keys
OPENAI_API_KEY=

# Enable LLM synthesis (uses OpenAI if key and provider are set)
# Set to false to use deterministic template mode (recommended for testing)
ENABLE_LLM_SYNTHESIS=false
```

#### Deployment Environment

```dotenv
# Application environment
ENVIRONMENT=local

# Application name
APP_NAME=Secure AI Insights Assistant
```

### Example `.env` for Local Development

```dotenv
# Database
DATABASE_URL=postgresql+psycopg2://<USER>:<PASSWORD>@<HOST>:<PORT>/<DB_NAME>

# Security
JWT_SECRET=generated-secret-from-command-above
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8000

# Files & Data
DATA_DIR=data
MAX_UPLOAD_MB=50
LOG_LEVEL=DEBUG

# AI
AI_PROVIDER=openai
AI_MODEL=gpt-4o-mini
OPENAI_API_KEY=
ENABLE_LLM_SYNTHESIS=true

# Environment
ENVIRONMENT=local
APP_NAME=Secure AI Insights Assistant
```

---

## Database Setup

### Using Docker Compose (Recommended)

The `docker-compose.yml` automatically sets up PostgreSQL:

```bash
# Start PostgreSQL in background
docker compose -f docker/docker-compose.yml up -d postgres

# Wait 3-5 seconds for it to be ready
sleep 5

# Check if it's running
docker compose -f docker/docker-compose.yml ps
```

Expected output:
```
NAME           COMMAND                  SERVICE      STATUS
postgres       "docker-entrypoint..."   postgres     Up 10 seconds
```

### Using Docker Directly (Manual)

```bash
# Start PostgreSQL container
docker run --name secure-ai-postgres \
  -e POSTGRES_USER=secure_ai \
  -e POSTGRES_PASSWORD=secure_ai_password \
  -e POSTGRES_DB=secure_ai \
  -p 5432:5432 \
  -d postgres:15

# Verify connection
docker exec secure-ai-postgres psql -U secure_ai -d secure_ai -c "SELECT 1"
```

### Create Tables (Automatic)

When the app starts, SQLAlchemy automatically creates all tables using models in `app/models/db_models.py`.

**Manual table creation (if needed):**

```bash
# Access PostgreSQL
docker compose -f docker/docker-compose.yml exec postgres psql -U secure_ai -d secure_ai

# Or directly from your machine
psql -h localhost -U secure_ai -d secure_ai

# Inside psql:
\dt                    # List existing tables
\q                     # Quit
```

---

## Running the Application

### Option 1: Docker Compose (Simplest)

Starts everything: PostgreSQL, backend, migrations

```bash
# Start all services
docker compose -f docker/docker-compose.yml up --build

# In background:
docker compose -f docker/docker-compose.yml up -d --build

# View logs
docker compose -f docker/docker-compose.yml logs -f backend

# Stop services
docker compose -f docker/docker-compose.yml down
```

### Option 2: Docker with Manual Backend (Development)

```bash
# Terminal 1: Start just PostgreSQL
docker compose -f docker/docker-compose.yml up postgres

# Terminal 2: Run backend locally
# (Make sure .venv is activated)
python main.py

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Option 3: Everything Locally (Without Docker)

**Requires local PostgreSQL installation:**

```bash
# Terminal 1: Start PostgreSQL (platform-specific)
# macOS (if using Homebrew):
brew services start postgresql

# Ubuntu/Debian:
sudo systemctl start postgresql

# Windows: Use PostgreSQL installer's service

# Terminal 2: Run the app
# (Make sure .venv is activated)
python main.py

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## Demo & Testing

### Step 1: Generate Demo Data

```bash
# Activate virtual environment (if not already)
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Generate CSV data and seed database
python scripts/generate_demo_data.py

# Expected output:
# ✓ Generated CSV files
# ✓ Seeded database with 100 movies
# ✓ Created 500 watch activity records
# ✓ Populated all reference tables
```

### Step 2: Access the Application

Once running, open browser tabs:

| Feature | URL | Notes |
|---------|-----|-------|
| **API Docs** | http://localhost:8000/docs | Swagger UI - try endpoints here |
| **Health Check** | http://localhost:8000/health | Should return `{"status": "healthy"}` |
| **OpenAPI Schema** | http://localhost:8000/openapi.json | Machine-readable API spec |

### Step 3: Create an Auth Token

```bash
# Method 1: Using curl
curl -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "demo-user",
    "role": "analyst"
  }'

# Method 2: Using Swagger UI
# 1. Open http://localhost:8000/docs
# 2. Find POST /api/v1/auth/token
# 3. Click "Try it out"
# 4. Enter user_id and role
# 5. Click "Execute"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user_id": "demo-user"
}
```

### Step 4: Try a Chat Query

```bash
# Copy the access_token from previous step
TOKEN="your-access-token-here"

# Ask a question
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Which titles performed best in 2025?"
  }'
```

Response:
```json
{
  "answer": "Stellar Run leads the selected period with $8,200,000.00 revenue across 8200000 views and a 71.0% completion rate.",
  "sources": [
    {
      "source_type": "sql",
      "name": "movies + watch_activity"
    }
  ],
  "metrics": {
    "top_titles": [
      {
        "title": "Stellar Run",
        "revenue": 8200000.0,
        "views": 8200000,
        "completion_rate": 0.71
      }
    ]
  },
  "recommendations": [
    "Prioritize retention and cross-promotion around Stellar Run."
  ],
  "trace": {
    "tools_used": ["top_titles"],
    "synthesis_engine": "deterministic",
    "confidence": "medium"
  }
}
```

### Step 5: Run Tests

```bash
# Activate virtual environment
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_chat.py -v

# Run with coverage report
pytest --cov=app --cov-report=html
```

---

## Production Deployment

### Pre-Deployment Checklist

- [ ] Generate strong `JWT_SECRET` (32+ random characters)
- [ ] Set `ENVIRONMENT=production`
- [ ] Update `CORS_ORIGINS` to your actual domains
- [ ] Set `LOG_LEVEL=WARNING` (reduces verbosity)
- [ ] Configure PostgreSQL backups
- [ ] Set up SSL/TLS certificates
- [ ] Configure reverse proxy (nginx/Traefik)
- [ ] Enable rate limiting
- [ ] Set up monitoring/alerting

### Deployment Options

#### Option A: Docker on Linux Server

```bash
# SSH into your server
ssh user@your-server.com

# Clone repository
git clone <repo-url>
cd secure-ai-insights-assistant

# Copy and configure .env for production
cp .env.example .env
# Edit .env with production values

# Start with Docker Compose
docker compose -f docker/docker-compose.yml up -d

# Check logs
docker compose -f docker/docker-compose.yml logs -f
```

#### Option B: Kubernetes (Helm)

```bash
# Create namespace
kubectl create namespace secure-ai

# Deploy using helm (create helm chart first)
helm install secure-ai ./helm/chart \
  -n secure-ai \
  -f production-values.yaml

# Check status
kubectl get pods -n secure-ai
```

#### Option C: Cloud Platforms

**AWS (EC2 + RDS):**
```bash
# 1. Create EC2 instance
# 2. Create RDS PostgreSQL instance
# 3. Update DATABASE_URL to RDS endpoint
# 4. Deploy via docker or ECS
```

**Google Cloud (Cloud Run + CloudSQL):**
```bash
# 1. Create Cloud SQL PostgreSQL instance
# 2. Build Docker image
gcloud builds submit --tag gcr.io/PROJECT/secure-ai

# 3. Deploy to Cloud Run
gcloud run deploy secure-ai \
  --image gcr.io/PROJECT/secure-ai \
  --add-cloudsql-instances PROJECT:REGION:INSTANCE
```

**Heroku:**
```bash
# 1. Create Heroku app
heroku create your-app-name

# 2. Add PostgreSQL add-on
heroku addons:create heroku-postgresql:standard-0

# 3. Deploy
git push heroku main
```

### Environment Variables in Production

Set these via your platform's configuration system:

```
DATABASE_URL=postgresql+psycopg2://<USER>:<PASSWORD>@<HOST>:<PORT>/<DB_NAME>
JWT_SECRET=<strong-random-32-char-secret>
ENVIRONMENT=production
LOG_LEVEL=WARNING
CORS_ORIGINS=https://yourdomain.com
OPENAI_API_KEY=sk-... (if using LLM synthesis)
```

### Monitoring & Logging

**Application Logs:**
```bash
# Docker Compose
docker compose -f docker/docker-compose.yml logs -f --tail=100

# Set up centralized logging (ELK, Splunk, etc.)
# Configure logging in app/core/logger.py
```

**Health Checks:**
```bash
# Liveness endpoint (app is running)
curl https://yourdomain.com/health

# Readiness endpoint (ready to serve)
curl https://yourdomain.com/ready
```

**Metrics:**
- Response times
- Error rates
- Database connection pool usage
- Request volume

---

## Troubleshooting

### Issue: PostgreSQL Connection Refused

**Error:**
```
psycopg2.OperationalError: could not connect to server
```

**Solutions:**
```bash
# 1. Verify PostgreSQL is running
docker ps | grep postgres

# 2. Check DATABASE_URL in .env
cat .env | grep DATABASE_URL

# 3. Test connection manually
psql -h localhost -U secure_ai -d secure_ai

# 4. Restart PostgreSQL
docker compose -f docker/docker-compose.yml restart postgres
```

### Issue: Port Already in Use

**Error:**
```
ERROR: bind: address already in use
```

**Solutions:**
```bash
# Find what's using port 8000
# Windows:
netstat -ano | findstr :8000

# macOS/Linux:
lsof -i :8000

# Kill the process
# Adjust PID as needed
kill -9 <PID>

# OR use a different port by adding to .env
API_PORT=8001
```

### Issue: JWT Token errors

**Error:**
```
Invalid token or Signature verification failed
```

**Solutions:**
```bash
# 1. Regenerate JWT_SECRET
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 2. Update .env with new secret
# 3. Restart the app
# 4. Generate new token
```

### Issue: OpenAI Rate Limit (429 Error)

**Error:**
```
OpenAI call failed (Client error '429 Too Many Requests')
```

**Solutions:**
```bash
# Option 1: Disable LLM synthesis (recommended for free tier)
# Edit .env:
ENABLE_LLM_SYNTHESIS=false

# Option 2: Upgrade OpenAI account to paid plan

# Option 3: Add retry logic (implemented in synthesizer)
# The system automatically falls back to deterministic mode
```

### Issue: Database Migrations/Schema

**Error:**
```
ProgrammingError: relation "chat_messages" does not exist
```

**Solutions:**
```bash
# 1. Ensure app starts (migrations run automatically)
python main.py

# 2. Manually create tables
# Access PostgreSQL:
docker compose -f docker/docker-compose.yml exec postgres \
  psql -U secure_ai -d secure_ai

# 3. Drop and recreate if corrupted
# Inside psql:
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;

# 4. Restart app to recreate schema
```

### Issue: Dependency Conflict

**Error:**
```
ERROR: pip's dependency resolver does not currently take into account all the packages
```

**Solutions:**
```bash
# 1. Update pip
pip install --upgrade pip

# 2. Use specific Python version
python3.11 -m venv .venv

# 3. Clear pip cache and reinstall
pip cache purge
pip install -e .

# 4. Check pyproject.toml for version constraints
cat pyproject.toml | grep -A 20 dependencies
```

### Issue: Docker Build Fails

**Error:**
```
ERROR [backend 4/10] RUN pip install: ERROR: Could not find a version that satisfies the requirement...
```

**Solutions:**
```bash
# 1. Rebuild without cache
docker compose -f docker/docker-compose.yml build --no-cache

# 2. Update dependencies
pip install --upgrade pip setuptools wheel
uv pip install -e .

# 3. Check Dockerfile
cat docker/Dockerfile
```

### Issue: Demo Data Not Loading

**Error:**
```
No such file or directory: 'data/csv/movies.csv'
```

**Solutions:**
```bash
# 1. Run generator script
python scripts/generate_demo_data.py

# 2. Check if data directory exists
ls -la data/

# 3. Verify permissions
chmod -R 755 data/

# 4. Re-create data:
mkdir -p data/csv data/pdf
python scripts/generate_demo_data.py
```

---

## Advanced Configuration

### Enable LLM Synthesis (Optional)

If you have an OpenAI account:

```bash
# 1. Get API key from: https://platform.openai.com/api-keys

# 2. Update .env:
OPENAI_API_KEY=sk-your-key-here
ENABLE_LLM_SYNTHESIS=true
AI_PROVIDER=openai
AI_MODEL=gpt-4o-mini

# 3. Restart app
# Logs will now show LLM synthesis in use
```

### Custom Analytics Queries

Edit `app/services/analytics_service.py` to add new query methods.

### Adding Custom Tools

Create new tools in `app/tools/`:
```python
# app/tools/my_tool.py
class MyTool:
    def execute(self, db: Session, query: str) -> dict:
        # Your logic here
        pass
```

Register in `app/agents/planner.py`.

### Database Backups

```bash
# Backup
docker compose -f docker/docker-compose.yml exec postgres \
  pg_dump -U secure_ai secure_ai > backup.sql

# Restore
psql -h localhost -U secure_ai -d secure_ai < backup.sql
```

---

## Performance Tuning

### Database Connection Pool

```python
# app/core/db.py
engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_size=20,           # Increase for high concurrency
    max_overflow=40,        # Allow temporary overflow
    pool_recycle=3600,      # Recycle connections hourly
)
```

### Caching Layer (Optional)

Add Redis for caching:
```bash
docker run -d -p 6379:6379 redis:7
```

Configure in `.env`:
```
CACHE_ENABLED=true
REDIS_URL=redis://localhost:6379/0
```

### Logging Level for Production

```
LOG_LEVEL=WARNING
```

Reduces disk I/O while still capturing errors.

---

## Next Steps

1. **Read** [README.md](README.md) for architecture overview
2. **Explore** http://localhost:8000/docs for API documentation
3. **Review** source code in `app/` directory
4. **Customize** services for your business logic
5. **Deploy** to your chosen platform

---

**Successfully set up? 🎉 Start building!**
