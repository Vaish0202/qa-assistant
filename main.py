from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from agents.graph import run_analysis
from auth.routes import router as auth_router
from database.models import init_db, AnalysisHistory, SessionLocal
import uvicorn
import time

app = FastAPI(
    title="QA Assistant API",
    description="Agentic AI system for intelligent test failure classification",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(auth_router)

@app.on_event("startup")
def startup():
    init_db()
    print("✓ QA Assistant API started")

class AnalyzeRequest(BaseModel):
    user_id: str = "default_user"
    testcase_logs: str
    testcase_description: str
    testcase_code: str
    project_key: Optional[str] = "QA"

@app.get("/api/health")
def health():
    return {"status": "ok", "model": "llama3.2", "version": "1.0.0"}

@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    start_time = time.time()
    try:
        result = run_analysis(
            testcase_logs=request.testcase_logs,
            testcase_description=request.testcase_description,
            testcase_code=request.testcase_code,
            user_id=request.user_id
        )
        processing_time = round(time.time() - start_time, 2)
        final = result.get('final_output', {})

        if 'jira_ticket' in final:
            action_type = 'jira'
        elif 'improved_code' in final:
            action_type = 'suggestion'
        else:
            action_type = 'alert'

        db = SessionLocal()
        try:
            from database.models import AnalysisHistory
            history = AnalysisHistory(
                user_id=request.user_id,
                testcase_logs=request.testcase_logs,
                testcase_description=request.testcase_description,
                testcase_code=request.testcase_code,
                classification=result.get('classification'),
                classification_confidence=result.get('classification_confidence'),
                analysis_type=result.get('analysis_type'),
                final_output=final,
                channel_alert=result.get('channel_alert')
            )
            db.add(history)
            db.commit()
        finally:
            db.close()

        return {
            "status": "success",
            "classification": result.get('classification', 'unknown'),
            "action_type": action_type,
            "payload": final,
            "processing_time_seconds": processing_time
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
                    "classification": r.classification,
                    "analysis_type": r.analysis_type,
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