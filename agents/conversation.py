
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from database.models import ConversationSession, SessionLocal
from datetime import datetime
import json
import re
from agents.llm import get_llm
llm = get_llm()

def build_conversation_messages(session: ConversationSession) -> list:
    """Build LangChain message history from session"""
    messages = []

    # System prompt with full context
    system_content = f"""You are a QA expert assistant helping debug a test failure.

ORIGINAL TEST FAILURE CONTEXT:
- Framework: {session.framework}
- Classification: {session.classification}
- Logs: {session.initial_logs}
- Description: {session.initial_description}
- Code: {session.initial_code}

You are continuing a conversation about this specific test failure.
Remember all previous messages and provide contextual help.
If the user says they applied a fix and got a new error,
analyze the NEW error in context of the ORIGINAL problem.
Give specific, actionable answers — not generic advice."""

    messages.append(SystemMessage(content=system_content))

    # Add conversation history
    for msg in (session.messages or []):
        if msg['role'] == 'user':
            messages.append(HumanMessage(content=msg['content']))
        elif msg['role'] == 'assistant':
            messages.append(AIMessage(content=msg['content']))

    return messages

def handle_followup(session_id: str, user_message: str) -> dict:
    """Handle a followup message in an existing conversation"""
    db = SessionLocal()
    try:
        session = db.query(ConversationSession)\
                    .filter(ConversationSession.id == session_id)\
                    .first()

        if not session:
            return {"error": "Session not found", "session_id": session_id}

        print(f"--- CONVERSATION AGENT: session {session_id[:8]}... ---")
        print(f"User: {user_message[:100]}...")

        # Add user message to history
        messages = session.messages or []
        messages.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Build full conversation for LLM
        llm_messages = build_conversation_messages(session)
        llm_messages.append(HumanMessage(content=user_message))

        # Get AI response
        response = llm.invoke(llm_messages)
        ai_response = response.content.strip()

        print(f"AI response: {ai_response[:100]}...")

        # Add AI response to history
        messages.append({
            "role": "assistant",
            "content": ai_response,
            "timestamp": datetime.utcnow().isoformat()
        })

        # Check if resolved
        is_resolved = any(word in user_message.lower() for word in
                         ['solved', 'fixed', 'working', 'resolved', 'thanks', 'thank you'])

        # Update session
        session.messages = messages
        session.is_resolved = is_resolved
        session.updated_at = datetime.utcnow()
        db.commit()

        return {
            "session_id": session_id,
            "response": ai_response,
            "is_resolved": is_resolved,
            "message_count": len(messages),
            "framework": session.framework,
            "classification": session.classification
        }

    finally:
        db.close()

def create_session(
    user_id: str,
    logs: str,
    description: str,
    code: str,
    classification: str,
    framework: str,
    initial_response: str,
    project_id: str = None
) -> str:
    """Create new conversation session after initial analysis"""
    db = SessionLocal()
    try:
        session = ConversationSession(
            user_id=user_id,
            project_id=project_id,
            initial_logs=logs,
            initial_description=description,
            initial_code=code,
            classification=classification,
            framework=framework,
            messages=[{
                "role": "assistant",
                "content": initial_response,
                "timestamp": datetime.utcnow().isoformat()
            }]
        )
        db.add(session)
        db.commit()
        return session.id
    finally:
        db.close()

def get_session_history(session_id: str) -> dict:
    """Get full conversation history for a session"""
    db = SessionLocal()
    try:
        session = db.query(ConversationSession)\
                    .filter(ConversationSession.id == session_id)\
                    .first()
        if not session:
            return {"error": "Session not found"}

        return {
            "session_id": session_id,
            "framework": session.framework,
            "classification": session.classification,
            "is_resolved": session.is_resolved,
            "message_count": len(session.messages or []),
            "messages": session.messages or [],
            "created_at": str(session.created_at),
            "updated_at": str(session.updated_at)
        }
    finally:
        db.close()

def get_user_sessions(user_id: str) -> list:
    """Get all sessions for a user"""
    db = SessionLocal()
    try:
        sessions = db.query(ConversationSession)\
                    .filter(ConversationSession.user_id == user_id)\
                    .order_by(ConversationSession.created_at.desc())\
                    .limit(20).all()
        return [
            {
                "session_id": s.id,
                "framework": s.framework,
                "classification": s.classification,
                "is_resolved": s.is_resolved,
                "message_count": len(s.messages or []),
                "created_at": str(s.created_at)
            }
            for s in sessions
        ]
    finally:
        db.close()