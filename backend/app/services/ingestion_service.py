import csv
import random
import re
from datetime import datetime, timedelta, timezone
from io import BytesIO, StringIO
from pathlib import Path
from typing import BinaryIO

from fastapi import UploadFile
from sqlalchemy import delete, func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import IngestionError
from app.models.db_models import (
    Document,
    DocumentChunk,
    MarketingSpend,
    Movie,
    RegionalPerformance,
    Review,
    Viewer,
    WatchActivity,
)
from app.models.schemas import DatasetName


settings = get_settings()


DATASET_MODELS = {
    "movies": Movie,
    "viewers": Viewer,
    "watch_activity": WatchActivity,
    "reviews": Review,
    "marketing_spend": MarketingSpend,
    "regional_performance": RegionalPerformance,
}

REQUIRED_COLUMNS = {
    "movies": {"id", "title", "genre", "release_year", "production_budget"},
    "viewers": {"id", "segment", "city", "age_band"},
    "watch_activity": {"movie_id", "viewer_id", "watched_at", "watch_minutes", "completed", "revenue"},
    "reviews": {"movie_id", "rating", "sentiment", "comment"},
    "marketing_spend": {"movie_id", "channel", "spend", "campaign_month"},
    "regional_performance": {"movie_id", "city", "engagement_score", "month"},
}


class IngestionService:
    def ingest_csv(self, db: Session, dataset: DatasetName, upload: UploadFile) -> int:
        if upload.content_type not in {"text/csv", "application/vnd.ms-excel", "application/octet-stream"}:
            raise IngestionError("Only CSV uploads are supported")
        if not upload.filename or not upload.filename.lower().endswith(".csv"):
            raise IngestionError("Uploaded file must have a .csv extension")

        payload = upload.file.read(settings.upload_limit_bytes + 1)
        if len(payload) > settings.upload_limit_bytes:
            raise IngestionError(f"Upload exceeds {settings.max_upload_mb} MB limit")

        rows = list(csv.DictReader(StringIO(payload.decode("utf-8-sig"))))
        return self._replace_dataset_rows(db, dataset, rows)

    def load_csv_path(self, db: Session, dataset: DatasetName, file_path: Path) -> int:
        safe_root = settings.data_dir.resolve()
        resolved = file_path.resolve()
        if safe_root not in resolved.parents and resolved != safe_root:
            raise IngestionError("CSV path must be inside the configured data directory")
        if resolved.suffix.lower() != ".csv":
            raise IngestionError("Only .csv files are supported")
        with resolved.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        return self._replace_dataset_rows(db, dataset, rows)

    def ingest_pdf(self, db: Session, upload: UploadFile) -> tuple[int, int]:
        if not upload.filename or not upload.filename.lower().endswith(".pdf"):
            raise IngestionError("Uploaded document must have a .pdf extension")

        payload = upload.file.read(settings.upload_limit_bytes + 1)
        if len(payload) > settings.upload_limit_bytes:
            raise IngestionError(f"Upload exceeds {settings.max_upload_mb} MB limit")

        text = self._extract_pdf_text(BytesIO(payload))
        if not text.strip():
            text = self._demo_text_from_filename(upload.filename)

        document = Document(name=self._safe_document_name(upload.filename), document_type="report")
        existing = db.query(Document).filter(Document.name == document.name).one_or_none()
        if existing:
            db.delete(existing)
            db.flush()

        chunks = [DocumentChunk(chunk_index=index, text=chunk) for index, chunk in enumerate(self._chunk_text(text))]
        document.chunks = chunks
        db.add(document)
        db.commit()
        db.refresh(document)
        return document.id, len(chunks)

    def seed_demo_data(self, db: Session) -> dict[str, int]:
        if db.query(func.count(Movie.id)).scalar() or 0:
            return self._counts(db)

        movies = [
            Movie(id=1, title="Stellar Run", genre="Sci-Fi", release_year=2025, production_budget=48_000_000),
            Movie(id=2, title="Dark Orbit", genre="Sci-Fi", release_year=2025, production_budget=41_000_000),
            Movie(id=3, title="Last Kingdom", genre="Drama", release_year=2025, production_budget=35_000_000),
            Movie(id=4, title="Laugh Track", genre="Comedy", release_year=2025, production_budget=22_000_000),
            Movie(id=5, title="City Lights", genre="Romance", release_year=2024, production_budget=18_000_000),
            Movie(id=6, title="Final Whistle", genre="Sports", release_year=2025, production_budget=27_000_000),
        ]
        viewers = [
            Viewer(id=1, segment="Gen Z streamers", city="Mumbai", age_band="18-24"),
            Viewer(id=2, segment="Family co-viewers", city="Bengaluru", age_band="25-34"),
            Viewer(id=3, segment="Premium subscribers", city="Delhi", age_band="35-44"),
            Viewer(id=4, segment="Weekend binge watchers", city="Hyderabad", age_band="25-34"),
            Viewer(id=5, segment="Regional explorers", city="Pune", age_band="18-24"),
            Viewer(id=6, segment="Critic-led viewers", city="Chennai", age_band="35-44"),
        ]
        db.add_all(movies + viewers)
        db.flush()

        rng = random.Random(42)
        base = datetime(2026, 4, 1, tzinfo=timezone.utc)
        activities = []
        weights = {1: 1.65, 2: 1.2, 3: 1.05, 4: 0.45, 5: 0.65, 6: 0.9}
        for day in range(30):
            for movie in movies:
                for viewer in viewers:
                    multiplier = weights[movie.id]
                    views = max(1, int(rng.randint(1, 5) * multiplier))
                    for _ in range(views):
                        activities.append(
                            WatchActivity(
                                movie_id=movie.id,
                                viewer_id=viewer.id,
                                watched_at=base + timedelta(days=day, hours=rng.randint(0, 23)),
                                watch_minutes=rng.randint(35, 130),
                                completed=rng.random() < (0.82 if movie.id != 4 else 0.48),
                                revenue=round(rng.uniform(2.5, 9.0) * multiplier, 2),
                            )
                        )
        db.add_all(activities)

        db.add_all(
            [
                Review(movie_id=1, rating=4.7, sentiment="positive", comment="Strong rewatch intent and social buzz."),
                Review(movie_id=2, rating=4.2, sentiment="positive", comment="Dark Orbit performs well with sci-fi fans."),
                Review(movie_id=3, rating=4.0, sentiment="positive", comment="Last Kingdom has loyal drama audience."),
                Review(movie_id=4, rating=2.8, sentiment="negative", comment="Comedy timing feels stale to younger segments."),
                Review(movie_id=5, rating=3.5, sentiment="neutral", comment="Stable catalog performance."),
                Review(movie_id=6, rating=3.8, sentiment="positive", comment="Sports fans engage around weekends."),
            ]
        )
        db.add_all(
            [
                MarketingSpend(movie_id=1, channel="Social", spend=900_000, campaign_month="2026-04"),
                MarketingSpend(movie_id=2, channel="Influencer", spend=650_000, campaign_month="2026-04"),
                MarketingSpend(movie_id=3, channel="Search", spend=420_000, campaign_month="2026-04"),
                MarketingSpend(movie_id=4, channel="Display", spend=500_000, campaign_month="2026-04"),
                MarketingSpend(movie_id=6, channel="Sports partnerships", spend=380_000, campaign_month="2026-04"),
            ]
        )
        db.add_all(
            [
                RegionalPerformance(movie_id=1, city="Mumbai", engagement_score=91.5, month="2026-04"),
                RegionalPerformance(movie_id=1, city="Bengaluru", engagement_score=88.2, month="2026-04"),
                RegionalPerformance(movie_id=2, city="Delhi", engagement_score=79.3, month="2026-04"),
                RegionalPerformance(movie_id=3, city="Hyderabad", engagement_score=73.4, month="2026-04"),
                RegionalPerformance(movie_id=4, city="Pune", engagement_score=41.8, month="2026-04"),
                RegionalPerformance(movie_id=6, city="Chennai", engagement_score=68.1, month="2026-04"),
            ]
        )
        for name, text in self._demo_documents().items():
            document = Document(name=name, document_type="demo_report")
            document.chunks = [
                DocumentChunk(chunk_index=index, text=chunk)
                for index, chunk in enumerate(self._chunk_text(text))
            ]
            db.add(document)

        db.commit()
        return self._counts(db)

    def _replace_dataset_rows(self, db: Session, dataset: DatasetName, rows: list[dict[str, str]]) -> int:
        if not rows:
            raise IngestionError("CSV contains no data rows")
        missing = REQUIRED_COLUMNS[dataset] - set(rows[0].keys())
        if missing:
            raise IngestionError(f"CSV is missing required columns: {', '.join(sorted(missing))}")

        self._clear_dataset(db, dataset)
        db.add_all([self._row_to_model(dataset, row) for row in rows])
        db.commit()
        return len(rows)

    def _clear_dataset(self, db: Session, dataset: DatasetName) -> None:
        if dataset == "movies":
            for model in (WatchActivity, Review, MarketingSpend, RegionalPerformance, Movie):
                db.execute(delete(model))
            return
        if dataset == "viewers":
            db.execute(delete(WatchActivity))
            db.execute(delete(Viewer))
            return
        db.execute(delete(DATASET_MODELS[dataset]))

    def _row_to_model(self, dataset: DatasetName, row: dict[str, str]):
        if dataset == "movies":
            return Movie(
                id=int(row["id"]),
                title=row["title"],
                genre=row["genre"],
                release_year=int(row["release_year"]),
                production_budget=float(row["production_budget"]),
            )
        if dataset == "viewers":
            return Viewer(id=int(row["id"]), segment=row["segment"], city=row["city"], age_band=row["age_band"])
        if dataset == "watch_activity":
            return WatchActivity(
                movie_id=int(row["movie_id"]),
                viewer_id=int(row["viewer_id"]),
                watched_at=datetime.fromisoformat(row["watched_at"].replace("Z", "+00:00")),
                watch_minutes=int(row["watch_minutes"]),
                completed=row["completed"].strip().lower() in {"true", "1", "yes", "y"},
                revenue=float(row["revenue"]),
            )
        if dataset == "reviews":
            return Review(
                movie_id=int(row["movie_id"]),
                rating=float(row["rating"]),
                sentiment=row["sentiment"],
                comment=row["comment"],
            )
        if dataset == "marketing_spend":
            return MarketingSpend(
                movie_id=int(row["movie_id"]),
                channel=row["channel"],
                spend=float(row["spend"]),
                campaign_month=row["campaign_month"],
            )
        return RegionalPerformance(
            movie_id=int(row["movie_id"]),
            city=row["city"],
            engagement_score=float(row["engagement_score"]),
            month=row["month"],
        )

    def _extract_pdf_text(self, stream: BinaryIO) -> str:
        try:
            from pypdf import PdfReader

            reader = PdfReader(stream)
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception:
            return ""

    def _chunk_text(self, text: str, size: int = 900) -> list[str]:
        cleaned = re.sub(r"\s+", " ", text).strip()
        if not cleaned:
            return []
        return [cleaned[index : index + size] for index in range(0, len(cleaned), size)]

    def _safe_document_name(self, filename: str) -> str:
        name = Path(filename).name
        return re.sub(r"[^A-Za-z0-9_. -]", "_", name)[:240]

    def _demo_text_from_filename(self, filename: str) -> str:
        return f"{filename} discusses internal entertainment performance, audience behavior, campaign impact, and leadership recommendations."

    def _demo_documents(self) -> dict[str, str]:
        return {
            "quarterly-executive-report.pdf": (
                "Stellar Run is trending because social conversation, completion rate, and repeat viewing increased together. "
                "Leadership should extend the campaign, create behind the scenes clips, and cross-promote to sci-fi audiences."
            ),
            "campaign-performance-summary.pdf": (
                "Comedy campaigns underperformed because display spend reached broad audiences but produced weak completion. "
                "Shift budget toward creator-led clips and test sharper positioning before scaling."
            ),
            "audience-behavior-report.pdf": (
                "Mumbai and Bengaluru show the strongest engagement. Gen Z streamers and weekend binge watchers are the most responsive segments."
            ),
        }

    def _counts(self, db: Session) -> dict[str, int]:
        counts = {
            name: int(db.query(func.count(model.id)).scalar() or 0)
            for name, model in DATASET_MODELS.items()
        }
        counts["documents"] = int(db.query(func.count(Document.id)).scalar() or 0)
        counts["document_chunks"] = int(db.query(func.count(DocumentChunk.id)).scalar() or 0)
        return counts
