from fastapi import APIRouter, HTTPException
from auth.models import LoginRequest, LoginResponse
from auth.security import create_access_token, hash_password, verify_password
from database.models import User, SessionLocal
import uuid

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register")
def register(request: LoginRequest):
    username = request.username.strip()
    if not 3 <= len(username) <= 50:
        raise HTTPException(status_code=400, detail="Username must be 3-50 characters")
    # bcrypt only uses the first 72 bytes of a password
    if not 8 <= len(request.password.encode()) <= 72:
        raise HTTPException(status_code=400, detail="Password must be 8-72 characters")
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
        user = User(id=str(uuid.uuid4()), username=username,
                    password=hash_password(request.password))
        db.add(user)
        db.commit()
        return {"message": f"User {username} registered successfully"}
    finally:
        db.close()


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == request.username.strip()).first()
        ok, needs_rehash = verify_password(request.password, user.password) if user else (False, False)
        if not ok:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if needs_rehash:                      # old SHA-256 account -> upgrade to bcrypt
            user.password = hash_password(request.password)
            db.commit()
        return LoginResponse(
            user_id=user.id,
            username=user.username,
            token=create_access_token(user.id, user.username),
            message="Login successful"
        )
    finally:
        db.close()