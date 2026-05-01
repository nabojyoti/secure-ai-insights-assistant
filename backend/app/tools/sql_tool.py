import re

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.common_utils.logging_utils import logger
from app.core.exceptions import UnsafeQueryError


class SQLTool:
    forbidden = re.compile(r"\b(drop|delete|update|insert|alter|create|truncate|grant|revoke)\b|--|/\*", re.I)

    def run_read_only(self, db: Session, query: str, limit: int = 100) -> list[dict]:
        logger.debug(f"🔍 SQL Query: {query[:100]}..." if len(query) > 100 else f"🔍 SQL Query: {query}")
        normalized = query.strip().rstrip(";")
        if not re.match(r"^select\b", normalized, flags=re.I):
            logger.error(f"❌ SQL Security: Non-SELECT query attempted")
            raise UnsafeQueryError("Only SELECT queries are allowed")
        if self.forbidden.search(normalized):
            logger.error(f"❌ SQL Security: Forbidden keywords detected")
            raise UnsafeQueryError("Unsafe SQL detected")
        if re.search(r"\blimit\b", normalized, flags=re.I):
            safe_query = normalized
        else:
            safe_query = f"{normalized} LIMIT :limit"

        logger.debug(f"✓ SQL validated and executed (limit: {min(limit, 500)})")
        result = db.execute(text(safe_query), {"limit": min(limit, 500)})
        rows = [dict(row._mapping) for row in result]
        logger.debug(f"✓ SQL returned {len(rows)} rows")
        return rows
