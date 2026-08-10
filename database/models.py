from sqlalchemy import create_engine, Column, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import uuid

Base = declarative_base()

class AnalysisHistory(Base):
    __tablename__ = "analysis_history"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    testcase_logs = Column(String)
    testcase_description = Column(String)
    testcase_code = Column(String)
    classification = Column(String)
    classification_confidence = Column(Float)
    analysis_type = Column(String)
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