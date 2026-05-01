import re

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.exceptions import UnsafeQueryError


class SQLTool:
    forbidden = re.compile(r"\b(drop|delete|update|insert|alter|create|truncate|grant|revoke)\b|--|/\*", re.I)

    def run_read_only(self, db: Session, query: str, limit: int = 100) -> list[dict]:
        normalized = query.strip().rstrip(";")
        if not re.match(r"^select\b", normalized, flags=re.I):
            raise UnsafeQueryError("Only SELECT queries are allowed")
        if self.forbidden.search(normalized):
            raise UnsafeQueryError("Unsafe SQL detected")
        if re.search(r"\blimit\b", normalized, flags=re.I):
            safe_query = normalized
        else:
            safe_query = f"{normalized} LIMIT :limit"

        result = db.execute(text(safe_query), {"limit": min(limit, 500)})
        return [dict(row._mapping) for row in result]
