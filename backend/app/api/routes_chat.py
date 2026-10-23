import json
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import CreateSessionRequest, MessageIn, ChatMessageOut, ChatSessionOut
from app.agents.chat_agent import AskRaahAgent
from app.utils.time_utils import utcnow, ensure_naive

router = APIRouter(prefix="/chat", tags=["Ask Raah (Contextual Chat)"])

@router.post("/sessions", response_model=ChatSessionOut)
def create_session(payload: CreateSessionRequest, db: Session = Depends(get_db)):
    """Creates a new conversation or retrieves an existing active thread for a transaction."""
    if payload.transaction_id:
        existing = db.query(ChatSession).filter(
            ChatSession.transaction_id == payload.transaction_id,
            ChatSession.user_id == (payload.user_id or "user_default_01")
        ).first()
        if existing:
            count = db.query(ChatMessage).filter(ChatMessage.session_id == existing.id).count()
            latest = db.query(ChatMessage).filter(ChatMessage.session_id == existing.id).order_by(ChatMessage.created_at.desc()).first()
            return ChatSessionOut(
                id=existing.id,
                user_id=existing.user_id,
                transaction_id=existing.transaction_id,
                case_id=existing.case_id,
                title=existing.title,
                created_at=existing.created_at,
                updated_at=existing.updated_at,
                latest_message=latest.content if latest else None,
                message_count=count
            )

    title = "Payment Assistance"
    if payload.transaction_id:
        title = f"Inquiry: {payload.transaction_id}"

    sess = ChatSession(
        user_id=payload.user_id or "user_default_01",
        transaction_id=payload.transaction_id,
        case_id=payload.case_id,
        title=title,
        created_at=utcnow()
    )
    db.add(sess)
    db.flush()

    # If initial message provided, save greeting
    greeting = ChatMessage(
        session_id=sess.id,
        sender="ASSISTANT",
        content=(
            "Hello! I am Raah, your autonomous payment recovery teammate. "
            "I'm tracking your payment in real-time across the payer bank, switch, and merchant. "
            "How can I help you regarding this transaction?"
        ),
        created_at=utcnow()
    )
    db.add(greeting)
    db.commit()

    return ChatSessionOut(
        id=sess.id,
        user_id=sess.user_id,
        transaction_id=sess.transaction_id,
        case_id=sess.case_id,
        title=sess.title,
        created_at=sess.created_at,
        updated_at=sess.updated_at,
        latest_message=greeting.content,
        message_count=1
    )


@router.get("/sessions", response_model=List[ChatSessionOut])
def list_sessions(user_id: str = "user_default_01", db: Session = Depends(get_db)):
    """Retrieves saved conversation history."""
    sessions = db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.updated_at.desc()).all()
    results = []
    for s in sessions:
        count = db.query(ChatMessage).filter(ChatMessage.session_id == s.id).count()
        latest = db.query(ChatMessage).filter(ChatMessage.session_id == s.id).order_by(ChatMessage.created_at.desc()).first()
        results.append(ChatSessionOut(
            id=s.id,
            user_id=s.user_id,
            transaction_id=s.transaction_id,
            case_id=s.case_id,
            title=s.title,
            created_at=s.created_at,
            updated_at=s.updated_at,
            latest_message=latest.content if latest else None,
            message_count=count
        ))
    return results


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageOut])
def get_session_messages(session_id: str, db: Session = Depends(get_db)):
    sess = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    msgs = db.query(ChatMessage).filter(ChatMessage.session_id == sess.id).order_by(ChatMessage.created_at.asc()).all()
    results = []
    for m in msgs:
        tc = []
        tr = []
        try:
            tc = json.loads(m.tool_calls) if m.tool_calls else []
            tr = json.loads(m.tool_results) if m.tool_results else []
        except Exception:
            pass

        results.append(ChatMessageOut(
            id=m.id,
            session_id=m.session_id,
            sender=m.sender,
            content=m.content,
            tool_calls=tc,
            tool_results=tr,
            created_at=m.created_at
        ))
    return results


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageOut)
async def send_message(session_id: str, payload: MessageIn):
    """Sends a customer question to Ask Raah and runs autonomous resolution tools."""
    res = await AskRaahAgent.process_user_message(
        session_id=session_id,
        user_message=payload.content,
        transaction_id=payload.transaction_id
    )
    if "error" in res:
        raise HTTPException(status_code=400, detail=res["error"])

    return ChatMessageOut(
        id=res["message_id"],
        session_id=session_id,
        sender="ASSISTANT",
        content=res["content"],
        tool_calls=res.get("tool_calls", []),
        tool_results=res.get("tool_results", []),
        created_at=datetime.fromisoformat(res["created_at"])
    )
