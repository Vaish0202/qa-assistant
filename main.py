from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from agents.graph import run_analysis
from agents.conversation import create_session
from auth.routes import router as auth_router
from api.projects import router as projects_router
from api.chat import router as chat_router
from database.models import init_db, AnalysisHistory, SessionLocal
import uvicorn
import time
import json

app = FastAPI(
    title="QA Assistant API",
    description="Agentic AI for intelligent test failure classification",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(chat_router)

@app.on_event("startup")
def startup():
    init_db()
    print("✓ QA Assistant API v2.0 started")

class AnalyzeRequest(BaseModel):
    user_id: str = "default_user"
    project_id: Optional[str] = None
    testcase_logs: str
    testcase_description: str
    testcase_code: str

@app.get("/api/health")
def health():
    return {"status": "ok", "model": "llama3.2", "version": "2.0.0"}

@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    start_time = time.time()
    try:
        result = run_analysis(
            testcase_logs=request.testcase_logs,
            testcase_description=request.testcase_description,
            testcase_code=request.testcase_code,
            user_id=request.user_id,
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
            user_id=request.user_id,
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
            history = AnalysisHistory(
                user_id=request.user_id,
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
            )
            db.add(history)
            db.commit()
        finally:
            db.close()

        return {
            "status": "success",
            "session_id": session_id,        # NEW — for followup chat
            "classification": result.get('classification', 'unknown'),
            "action_type": action_type,
            "framework": result.get('framework', 'unknown'),
            "payload": final,
            "processing_time_seconds": processing_time
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jira/create")
def create_jira_manual(request: dict):
    """Human-approved Jira ticket creation"""
    from integrations.jira import create_jira_ticket
    result = create_jira_ticket(request)
    return result

@app.get("/api/history")
def get_history(user_id: str = "default_user"):
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
                    "project_id": r.project_id,
                    "created_at": str(r.created_at),
                    "alert": r.channel_alert
                }
                for r in records
            ]
        }
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)