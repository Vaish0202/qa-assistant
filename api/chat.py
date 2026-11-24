from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from agents.conversation import (
    handle_followup,
    get_session_history,
    get_user_sessions
)

from auth.security import get_current_user_id
from database.models import ConversationSession, SessionLocal

router = APIRouter(prefix="/api/chat", tags=["chat"])


def require_own_session(session_id: str, user_id: str):
    """404 unless the conversation exists AND belongs to this user."""
    db = SessionLocal()
    try:
        found = db.query(ConversationSession.id).filter(
            ConversationSession.id == session_id,
            ConversationSession.user_id == user_id).first()
    finally:
        db.close()
    if not found:
        raise HTTPException(status_code=404, detail="Session not found")

class FollowupRequest(BaseModel):
    session_id: str
    message: str

@router.post("/followup")
def followup(request: FollowupRequest, user_id: str = Depends(get_current_user_id)):
    """Send a followup message in an existing conversation"""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if len(request.message) > 4000:
        raise HTTPException(status_code=413, detail="Message is too long")
    require_own_session(request.session_id, user_id)

    result = handle_followup(request.session_id, request.message)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result

@router.get("/session/{session_id}")
def get_session(session_id: str, user_id: str = Depends(get_current_user_id)):
    """Get full conversation history"""
    require_own_session(session_id, user_id)
    result = get_session_history(session_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.get("/sessions")
def list_sessions(user_id: str = Depends(get_current_user_id)):
    """List all conversations for a user"""
    return {"sessions": get_user_sessions(user_id)}

@router.post("/resolve/{session_id}")
def mark_resolved(session_id: str, user_id: str = Depends(get_current_user_id)):
    """Mark a conversation as resolved"""
    require_own_session(session_id, user_id)
    from database.models import ConversationSession, SessionLocal
    from datetime import datetime
    db = SessionLocal()
    try:
        session = db.query(ConversationSession)\
                    .filter(ConversationSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        session.is_resolved = True
        session.updated_at = datetime.utcnow()
        db.commit()
        return {"message": "Session marked as resolved", "session_id": session_id}
    finally:
        db.close()