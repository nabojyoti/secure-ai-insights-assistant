from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.db import get_db
from app.models.schemas import CsvIngestionResponse, DatasetName, PdfIngestionResponse, SeedResponse
from app.services.ingestion_service import IngestionService


router = APIRouter(prefix="/ingestion", tags=["ingestion"])
ingestion = IngestionService()


@router.post("/csv", response_model=CsvIngestionResponse)
def ingest_csv(
    dataset: DatasetName = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    rows = ingestion.ingest_csv(db, dataset, file)
    return CsvIngestionResponse(dataset=dataset, rows_loaded=rows)


@router.post("/csv/path", response_model=CsvIngestionResponse)
def ingest_csv_path(
    dataset: DatasetName,
    path: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    rows = ingestion.load_csv_path(db, dataset, Path(path))
    return CsvIngestionResponse(dataset=dataset, rows_loaded=rows)


@router.post("/pdf", response_model=PdfIngestionResponse)
def ingest_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    document_id, chunks = ingestion.ingest_pdf(db, file)
    return PdfIngestionResponse(document_id=document_id, chunks_loaded=chunks)


@router.post("/seed", response_model=SeedResponse)
def seed_demo_data(db: Session = Depends(get_db), user=Depends(get_current_user)):
    counts = ingestion.seed_demo_data(db)
    return SeedResponse(status="seeded", rows=counts, documents=counts.get("documents", 0))
