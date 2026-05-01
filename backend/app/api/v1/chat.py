from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.orchestrator import Orchestrator
from app.auth.dependencies import get_current_user
from app.core.db import get_db
from app.models.schemas import ChatRequest, ChatResponse


router = APIRouter(tags=["chat"])
agent = Orchestrator()


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return agent.run(db, req.query, user)
