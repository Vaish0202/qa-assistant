from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from database.models import Project, SessionLocal
import uuid

router = APIRouter(prefix="/api/projects", tags=["projects"])

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    frontend: Optional[str] = ""
    backend: Optional[str] = ""
    database: Optional[str] = ""
    cloud: Optional[str] = ""
    test_framework: Optional[str] = "pytest"
    language: Optional[str] = "python"
    jira_project_key: Optional[str] = "QA"
    user_id: str = "default_user"

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    tech_stack: dict
    test_framework: str
    language: str
    jira_project_key: str
    user_id: str

@router.post("/create")
def create_project(data: ProjectCreate):
    db = SessionLocal()
    try:
        project = Project(
            id=str(uuid.uuid4()),
            name=data.name,
            description=data.description,
            tech_stack={
                "frontend": data.frontend,
                "backend": data.backend,
                "database": data.database,
                "cloud": data.cloud
            },
            test_framework=data.test_framework,
            language=data.language,
            jira_project_key=data.jira_project_key,
            user_id=data.user_id
        )
        db.add(project)
        db.commit()
        return {
            "message": "Project created successfully",
            "project_id": project.id,
            "name": project.name
        }
    finally:
        db.close()

@router.get("/list")
def list_projects(user_id: str = "default_user"):
    db = SessionLocal()
    try:
        projects = db.query(Project)\
                    .filter(Project.user_id == user_id)\
                    .all()
        return {
            "projects": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "tech_stack": p.tech_stack,
                    "test_framework": p.test_framework,
                    "language": p.language,
                    "jira_project_key": p.jira_project_key
                }
                for p in projects
            ]
        }
    finally:
        db.close()

@router.get("/{project_id}")
def get_project(project_id: str):
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "tech_stack": project.tech_stack,
            "test_framework": project.test_framework,
            "language": project.language,
            "jira_project_key": project.jira_project_key
        }
    finally:
        db.close()

@router.delete("/{project_id}")
def delete_project(project_id: str):
    db = SessionLocal()
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        db.delete(project)
        db.commit()
        return {"message": "Project deleted"}
    finally:
        db.close()