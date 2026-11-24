"""Passwords, login tokens and the rate limiter (no database, no LLM)."""
import hashlib
import os
import time

os.environ.setdefault("JWT_SECRET", "test-secret-" + "x" * 32)

import jwt
import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from auth import security
from auth.security import (RateLimiter, create_access_token, get_current_user_id,
                           hash_password, verify_password)

app = FastAPI()


@app.get("/me")
def me(user_id: str = Depends(get_current_user_id)):
    return {"user_id": user_id}


client = TestClient(app)


def test_bcrypt_hash_and_verify():
    stored = hash_password("correct-horse")
    assert stored.startswith("$2") and "correct-horse" not in stored
    assert verify_password("correct-horse", stored) == (True, False)
    assert verify_password("wrong-horse", stored) == (False, False)


def test_old_sha256_accounts_still_log_in_and_need_rehash():
    old = hashlib.sha256(b"oldpass123").hexdigest()
    assert verify_password("oldpass123", old) == (True, True)
    assert verify_password("other", old)[0] is False


def test_valid_token_returns_user():
    token = create_access_token("user-1", "alice")
    r = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200 and r.json() == {"user_id": "user-1"}


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer not-a-jwt"}])
def test_missing_or_bad_token_is_rejected(headers):
    assert client.get("/me", headers=headers).status_code == 401


def test_expired_token_is_rejected():
    expired = jwt.encode({"sub": "user-1", "exp": int(time.time()) - 10},
                         security.JWT_SECRET, algorithm="HS256")
    assert client.get("/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_token_signed_with_another_secret_is_rejected():
    forged = jwt.encode({"sub": "admin", "exp": int(time.time()) + 60}, "guess", algorithm="HS256")
    assert client.get("/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_rate_limiter_blocks_after_limit():
    limiter = RateLimiter(limit=2, window=60)
    limiter.check("u1")
    limiter.check("u1")
    with pytest.raises(HTTPException) as e:
        limiter.check("u1")
    assert e.value.status_code == 429
    limiter.check("u2")                       # other users are not affected