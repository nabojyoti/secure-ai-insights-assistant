import re

from langchain_core.documents import Document as LangChainDocument
from sqlalchemy.orm import Session

from app.models.db_models import Document, DocumentChunk


class RAGTool:
    def retrieve(self, db: Session, query: str, limit: int = 4) -> list[dict]:
        terms = [term for term in re.findall(r"[a-z0-9]+", query.lower()) if len(term) > 2]
        chunks = db.query(DocumentChunk).join(Document).all()
        scored = []
        for chunk in chunks:
            text_lower = chunk.text.lower()
            score = sum(text_lower.count(term) for term in terms)
            if score:
                scored.append((score, chunk))

        if not scored:
            scored = [(1, chunk) for chunk in chunks[:limit]]

        scored.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "document_id": chunk.document_id,
                "document_name": chunk.document.name,
                "chunk_id": chunk.id,
                "snippet": self._snippet(chunk.text, terms),
                "metadata": self._to_langchain_document(chunk).metadata,
            }
            for _, chunk in scored[:limit]
        ]

    def _to_langchain_document(self, chunk: DocumentChunk) -> LangChainDocument:
        return LangChainDocument(
            page_content=chunk.text,
            metadata={
                "document_id": chunk.document_id,
                "document_name": chunk.document.name,
                "chunk_id": chunk.id,
            },
        )

    def _snippet(self, text: str, terms: list[str], length: int = 240) -> str:
        lowered = text.lower()
        start = 0
        for term in terms:
            index = lowered.find(term)
            if index >= 0:
                start = max(index - 60, 0)
                break
        snippet = text[start : start + length].strip()
        return snippet + ("..." if len(text) > start + length else "")
