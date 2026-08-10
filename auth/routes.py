from fastapi import APIRouter, HTTPException
from auth.models import LoginRequest, LoginResponse
from database.models import User, SessionLocal
import uuid
import hashlib

router = APIRouter(prefix="/api/auth", tags=["auth"])

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(user_id: str) -> str:
    return hashlib.sha256(f"{user_id}-qa-secret".encode()).hexdigest()

@router.post("/register")
def register(request: LoginRequest):
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == request.username).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
        user = User(
            id=str(uuid.uuid4()),
            username=request.username,
            password=hash_password(request.password)
        )
        db.add(user)
        db.commit()
        return {"message": f"User {request.username} registered successfully"}
    finally:
        db.close()

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == request.username).first()
        if not user or user.password != hash_password(request.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_token(user.id)
        return LoginResponse(
            user_id=user.id,
            username=user.username,
            token=token,
            message="Login successful"
        )
    finally:
        db.close()