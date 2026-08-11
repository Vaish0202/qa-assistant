from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from agents.conversation import (
    handle_followup,
    get_session_history,
    get_user_sessions
)

router = APIRouter(prefix="/api/chat", tags=["chat"])

class FollowupRequest(BaseModel):
    session_id: str
    message: str

@router.post("/followup")
def followup(request: FollowupRequest):
    """Send a followup message in an existing conversation"""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    result = handle_followup(request.session_id, request.message)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result

@router.get("/session/{session_id}")
def get_session(session_id: str):
    """Get full conversation history"""
    result = get_session_history(session_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@router.get("/sessions")
def list_sessions(user_id: str = "default_user"):
    """List all conversations for a user"""
    return {"sessions": get_user_sessions(user_id)}

@router.post("/resolve/{session_id}")
def mark_resolved(session_id: str):
    """Mark a conversation as resolved"""
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