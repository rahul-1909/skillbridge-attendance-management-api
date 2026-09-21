import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.hash import pbkdf2_sha256

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET", "change-me-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24
MONITORING_TOKEN_EXPIRE_HOURS = 1


def hash_password(password: str) -> str:
    return pbkdf2_sha256.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pbkdf2_sha256.verify(plain_password, hashed_password)


def _build_payload(data: Dict[str, Any], expires_delta: timedelta, token_type: str) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    payload = data.copy()
    payload.update(
        {
            "iat": int(now.timestamp()),
            "exp": int((now + expires_delta).timestamp()),
            "typ": token_type,
        }
    )
    return payload


def create_access_token(user_id: int, role: str) -> str:
    payload = _build_payload(
        {"user_id": user_id, "role": role},
        timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS),
        token_type="access",
    )
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_monitoring_token(user_id: int, role: str) -> str:
    payload = _build_payload(
        {
            "user_id": user_id,
            "role": role,
            "scope": "monitoring_read",
        },
        timedelta(hours=MONITORING_TOKEN_EXPIRE_HOURS),
        token_type="monitoring",
    )
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
