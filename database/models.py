from sqlalchemy import create_engine, Column, String, Float, DateTime, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    description = Column(String)
    tech_stack = Column(JSON)
    test_framework = Column(String)
    language = Column(String)
    common_patterns = Column(JSON)
    jira_project_key = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String, nullable=False)

class ConversationSession(Base):
    __tablename__ = "conversation_sessions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    project_id = Column(String, nullable=True)
    initial_logs = Column(String)
    initial_description = Column(String)
    initial_code = Column(String)
    messages = Column(JSON, default=list)   # list of {role, content, timestamp}
    classification = Column(String)
    framework = Column(String)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)

class AnalysisHistory(Base):
    __tablename__ = "analysis_history"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    project_id = Column(String, nullable=True)
    session_id = Column(String, nullable=True)   # NEW
    testcase_logs = Column(String)
    testcase_description = Column(String)
    testcase_code = Column(String)
    classification = Column(String)
    classification_confidence = Column(Float)
    analysis_type = Column(String)
    framework = Column(String)
    final_output = Column(JSON)
    channel_alert = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

engine = create_engine("sqlite:///qa_assistant.db", echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
    print("✓ Database initialized")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()