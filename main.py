import sys
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

ROOT = Path(__file__).resolve().parent
BACKEND_PATH = ROOT / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from app.api.v1 import analytics, auth, chat, documents, ingestion  # noqa: E402
from app.common_utils.logging_utils import logger  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.core.db import engine, init_db  # noqa: E402
from app.core.exceptions import AppError  # noqa: E402


settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.parsed_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.exception(
            f"Unhandled error path={request.url.path} latency_ms={elapsed_ms} error={exc.__class__.__name__}",
            extra={"request_id": request_id},
        )
        raise
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    logger.info(
        f"request method={request.method} path={request.url.path} status={response.status_code} latency_ms={elapsed_ms}",
        extra={"request_id": request_id},
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.code, "detail": exc.message})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(status_code=422, content={"error": "validation_error", "detail": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    request_id = request.headers.get("X-Request-ID", "-")
    logger.exception(
        f"Unhandled application error path={request.url.path} error={exc.__class__.__name__}",
        extra={"request_id": request_id},
    )
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "detail": "An unexpected error occurred", "request_id": request_id},
    )


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}


@app.get("/ready")
def ready():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ready"}


app.include_router(auth.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(ingestion.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")
