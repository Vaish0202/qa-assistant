"""
Password hashing, login tokens (JWT) and a simple rate limiter.

    hash_password / verify_password   bcrypt (salted, slow on purpose)
    create_access_token               signed JWT with user id + expiry
    get_current_user_id               FastAPI dependency: reads the
                                      "Authorization: Bearer <token>" header,
                                      rejects missing/invalid/expired tokens
    analyze_limiter                   max N analyses per user per minute

Settings (.env):
    JWT_SECRET           long random string - REQUIRED in production
    JWT_EXPIRE_HOURS     default 24
    ANALYZE_RATE_LIMIT   analyses per user per minute, default 10
"""
import hashlib
import hmac
import os
import secrets
import threading
import time
from collections import defaultdict, deque

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    # Local development only: a new secret each start, so old logins stop working.
    JWT_SECRET = secrets.token_urlsafe(48)
    print("WARNING: JWT_SECRET not set - using a temporary secret (set it in production)")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))


# ------------------------------------------------------------------ passwords
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, stored: str) -> tuple[bool, bool]:
    """Returns (is_correct, needs_rehash).

    Accounts created before this change have an unsalted SHA-256 hash. They
    can still log in once; the caller then re-saves the password with bcrypt.
    """
    if stored.startswith("$2"):                       # bcrypt hash
        return bcrypt.checkpw(password.encode(), stored.encode()), False
    legacy = hashlib.sha256(password.encode()).hexdigest()
    return hmac.compare_digest(legacy, stored), True


# --------------------------------------------------------------------- tokens
def create_access_token(user_id: str, username: str) -> str:
    now = int(time.time())
    payload = {"sub": user_id, "username": username,
               "iat": now, "exp": now + JWT_EXPIRE_HOURS * 3600}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


_bearer = HTTPBearer(auto_error=False)


def get_current_user_id(
        creds: HTTPAuthorizationCredentials = Depends(_bearer)) -> str:
    if creds is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not logged in",
                            headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(creds.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired, please log in again")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
    return payload["sub"]


# ---------------------------------------------------------------- rate limit
class RateLimiter:
    """At most `limit` calls per `window` seconds per key (in memory, one server)."""

    def __init__(self, limit: int, window: int = 60):
        self.limit, self.window = limit, window
        self._calls = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str):
        now = time.time()
        with self._lock:
            calls = self._calls[key]
            while calls and calls[0] <= now - self.window:
                calls.popleft()
            if len(calls) >= self.limit:
                wait = int(self.window - (now - calls[0])) + 1
                raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS,
                                    f"Too many analyses - try again in {wait}s",
                                    headers={"Retry-After": str(wait)})
            calls.append(now)


analyze_limiter = RateLimiter(int(os.getenv("ANALYZE_RATE_LIMIT", "10")), 60)