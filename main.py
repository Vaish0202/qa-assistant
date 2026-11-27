import json
import os
import time
import uuid
from typing import Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.conversation import create_session
from agents.graph import run_analysis
from agents.llm import get_model_info
from api.chat import router as chat_router
from api.projects import router as projects_router
from auth.routes import router as auth_router
from auth.security import analyze_limiter, get_current_user_id
from database.models import AnalysisHistory, JiraTicket, SessionLocal, init_db

# ------------------------------------------------------------------ settings
# DEMO_MODE=true: Jira tickets are drafted and approved in the UI but NOT
# created in Jira (safe for a public demo).
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "20000"))   # per field
# Only these websites may call the API from a browser.
# Production: ALLOWED_ORIGINS=https://your-app.vercel.app
ALLOWED_ORIGINS = [o.strip() for o in os.getenv(
    "ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()]

app = FastAPI(
    title="QA Assistant API",
    description="Agentic AI for intelligent test failure classification",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Authorization", "Content-Type"]
)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(chat_router)


def utc_iso(dt):
    """Database times are UTC; the trailing Z lets the browser convert to local time."""
    return dt.isoformat() + "Z" if dt else None


@app.on_event("startup")
def startup():
    init_db()
    # Load the XGBoost model at startup so the first request isn't slow.
    try:
        from ml_classifier.predict import get_model
        get_model()
    except FileNotFoundError:
        pass
    print("✓ QA Assistant API v2.0 started")


# -------------------------------------------------------------------- health
@app.get("/")
def root():
    return {"status": "ok", "message": "QA Assistant backend is running"}


@app.get("/api/health")
@app.get("/health")
def health():
    return {"status": "ok", "model": get_model_info()["model"], "version": "2.0.0",
            "demo_mode": DEMO_MODE}


# ------------------------------------------------------------------- analyze
class AnalyzeRequest(BaseModel):
    project_id: Optional[str] = None
    testcase_logs: str
    testcase_description: str
    testcase_code: str


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest, user_id: str = Depends(get_current_user_id)):
    for name in ("testcase_logs", "testcase_description", "testcase_code"):
        if len(getattr(request, name)) > MAX_INPUT_CHARS:
            raise HTTPException(status_code=413,
                                detail=f"{name} is longer than {MAX_INPUT_CHARS} characters")
    analyze_limiter.check(user_id)            # 429 if this user sends too many
    start_time = time.time()
    try:
        result = run_analysis(
            testcase_logs=request.testcase_logs,
            testcase_description=request.testcase_description,
            testcase_code=request.testcase_code,
            user_id=user_id,
            project_id=request.project_id
        )
        processing_time = round(time.time() - start_time, 2)
        final = result.get('final_output', {})

        if 'jira_ticket' in final:
            action_type = 'jira'
        elif 'improved_code' in final:
            action_type = 'suggestion'
        else:
            action_type = 'alert'

        # Build initial response summary for session
        initial_response = json.dumps({
            "classification": result.get('classification'),
            "analysis_type": result.get('analysis_type'),
            "framework": result.get('framework'),
            "summary": final.get('root_cause') or final.get('summary', ''),
            "action": action_type
        })

        # Create conversation session
        session_id = create_session(
            user_id=user_id,
            logs=request.testcase_logs,
            description=request.testcase_description,
            code=request.testcase_code,
            classification=result.get('classification', 'unknown'),
            framework=result.get('framework', 'unknown'),
            initial_response=initial_response,
            project_id=request.project_id
        )

        # Save to analysis history
        db = SessionLocal()
        try:
            db.add(AnalysisHistory(
                user_id=user_id,
                project_id=request.project_id,
                session_id=session_id,
                testcase_logs=request.testcase_logs,
                testcase_description=request.testcase_description,
                testcase_code=request.testcase_code,
                classification=result.get('classification'),
                classification_confidence=result.get('classification_confidence'),
                analysis_type=result.get('analysis_type'),
                framework=result.get('framework'),
                final_output=final,
                channel_alert=result.get('channel_alert')
            ))
            db.commit()
        finally:
            db.close()

        return {
            "status": "success",
            "session_id": session_id,
            "classification": result.get('classification', 'unknown'),
            "classification_confidence": result.get('classification_confidence'),
            "action_type": action_type,
            "framework": result.get('framework', 'unknown'),
            "payload": final,
            "processing_time_seconds": processing_time,
            "trace_run_id": result.get('trace_run_id')
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ------------------------------------------------------------ history / view
@app.get("/api/history")
def get_history(user_id: str = Depends(get_current_user_id)):
    db = SessionLocal()
    try:
        records = db.query(AnalysisHistory)\
                    .filter(AnalysisHistory.user_id == user_id)\
                    .order_by(AnalysisHistory.created_at.desc())\
                    .limit(20).all()
        return {
            "user_id": user_id,
            "total": len(records),
            "analyses": [
                {
                    "id": r.id,
                    "session_id": r.session_id,
                    "classification": r.classification,
                    "analysis_type": r.analysis_type,
                    "framework": r.framework,
                    "severity": (r.final_output or {}).get("severity"),
                    "project_id": r.project_id,
                    "created_at": utc_iso(r.created_at),
                    "alert": r.channel_alert
                }
                for r in records
            ]
        }
    finally:
        db.close()


@app.get("/api/analysis/{session_id}")
def get_analysis(session_id: str, user_id: str = Depends(get_current_user_id)):
    """One saved analysis, in the same shape as /api/analyze returns."""
    db = SessionLocal()
    try:
        r = db.query(AnalysisHistory).filter(AnalysisHistory.session_id == session_id,
                                             AnalysisHistory.user_id == user_id).first()
        if not r:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return {
            "status": "success",
            "session_id": r.session_id,
            "classification": r.classification,
            "classification_confidence": r.classification_confidence,
            "analysis_type": r.analysis_type,
            "framework": r.framework,
            "payload": r.final_output or {},
            "testcase_logs": r.testcase_logs,
            "created_at": utc_iso(r.created_at),
            "processing_time_seconds": None,
        }
    finally:
        db.close()


# ---------------------------------------------------------------------- jira
class JiraCreateRequest(BaseModel):
    summary: str
    description: Optional[str] = ""
    bug_type: Optional[str] = "backend"
    severity: Optional[str] = "medium"
    priority: Optional[str] = "Medium"
    steps_to_reproduce: Optional[list] = []
    expected_result: Optional[str] = ""
    actual_result: Optional[str] = ""
    suggested_fix: Optional[str] = ""
    project_key: Optional[str] = "QA"
    assignee: Optional[str] = None
    due_date: Optional[str] = None


@app.post("/api/jira/create")
def create_jira_manual(request: JiraCreateRequest,
                       user_id: str = Depends(get_current_user_id)):
    """Human-approved Jira ticket creation with custom parameters"""
    if DEMO_MODE:
        result = {"success": True, "demo": True,
                  "ticket_key": f"DEMO-{uuid.uuid4().hex[:5].upper()}", "ticket_url": "",
                  "message": "Demo mode: the ticket was approved but not sent to Jira."}
    else:
        from integrations.jira import create_jira_ticket
        result = create_jira_ticket(request.dict())

    if result.get("success"):                 # remember it for the My Tickets page
        db = SessionLocal()
        try:
            db.add(JiraTicket(user_id=user_id, ticket_key=result.get("ticket_key"),
                              ticket_url=result.get("ticket_url") or "",
                              summary=(request.summary or "")[:200],
                              priority=request.priority, is_demo=DEMO_MODE))
            db.commit()
        finally:
            db.close()
    return result


@app.get("/api/tickets")
def list_tickets(user_id: str = Depends(get_current_user_id)):
    """Tickets this user approved in the app, newest first."""
    db = SessionLocal()
    try:
        rows = db.query(JiraTicket).filter(JiraTicket.user_id == user_id)\
                 .order_by(JiraTicket.created_at.desc()).limit(50).all()
        return {"tickets": [
            {"key": t.ticket_key, "url": t.ticket_url, "summary": t.summary,
             "priority": t.priority,
             "status": "Demo (not sent)" if t.is_demo else "Created in Jira",
             "created": t.created_at.strftime("%d %b %Y")}
            for t in rows]}
    finally:
        db.close()


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)