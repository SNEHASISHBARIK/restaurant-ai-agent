from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.agent.agent import Agent
from app.agent.schemas import ChatRequest, ChatResponse
from app.rag.retriever import LocalVectorStore
from app.security.guardrails import check_message, safe_error_message
from app.utils.config import get_settings
from app.utils.errors import UnsafeRequestError
from pathlib import Path

router=APIRouter(prefix="/api/agent", tags=["agent"])
ROOT=Path(__file__).resolve().parents[2]

def get_rag():
    store=LocalVectorStore(ROOT/"app"/"rag"/"knowledge_base", ROOT/"rag_store")
    store.load()
    return store

@router.post("/chat", response_model=ChatResponse, summary="Chat with the restaurant support agent")
def chat(payload: ChatRequest, request: Request, db: Session=Depends(get_db)):
    request_id=request.headers.get("X-Request-ID", f"REQ-{uuid4().hex[:12].upper()}")
    try:
        check_message(payload.message, get_settings().max_message_length)
        return Agent(db, get_rag()).chat(payload, request_id)
    except UnsafeRequestError as exc:
        raise HTTPException(400, safe_error_message(exc))
    except Exception:
        raise HTTPException(500, "The support agent could not complete the request.")
