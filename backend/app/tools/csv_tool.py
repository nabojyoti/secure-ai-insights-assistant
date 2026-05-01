import csv
from pathlib import Path

from app.core.config import get_settings
from app.core.exceptions import IngestionError


class CSVTool:
    def read_preview(self, path: Path, limit: int = 10) -> list[dict[str, str]]:
        settings = get_settings()
        root = settings.data_dir.resolve()
        resolved = path.resolve()
        if root not in resolved.parents and resolved != root:
            raise IngestionError("CSV path must be inside configured data directory")
        if resolved.suffix.lower() != ".csv":
            raise IngestionError("Only CSV files are supported")
        with resolved.open("r", encoding="utf-8-sig", newline="") as handle:
            return list(csv.DictReader(handle))[:limit]
