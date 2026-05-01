import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agents.orchestrator import Orchestrator
from app.auth.dependencies import get_current_user
from app.common_utils.logging_utils import logger
from app.core.db import get_db
from app.models.schemas import ChatRequest, ChatResponse


router = APIRouter(tags=["chat"])
agent = Orchestrator()


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    start_time = time.time()
    logger.info(f"📨 Chat request received from user={user['sub']}")
    logger.info(f"❓ Query: {req.query}")
    
    try:
        result = agent.run(db, req.query, user)
        elapsed = time.time() - start_time
        logger.info(f"✅ Chat completed in {elapsed:.2f}s | Sources: {len(result.get('sources', []))} | Answer length: {len(result.get('answer', ''))} chars")
        return result
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ Chat failed in {elapsed:.2f}s | Error: {str(e)}")
        raise
