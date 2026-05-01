from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.db import get_db
from app.models.db_models import Document


router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
def list_documents(db: Session = Depends(get_db), user=Depends(get_current_user)):
    documents = db.query(Document).order_by(Document.created_at.desc()).all()
    return [
        {
            "id": doc.id,
            "name": doc.name,
            "document_type": doc.document_type,
            "chunks": len(doc.chunks),
            "created_at": doc.created_at,
        }
        for doc in documents
    ]
