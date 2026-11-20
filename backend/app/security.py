import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt
from fastapi import HTTPException

from app.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()


def verify_password(password: str, hashed: str) -> bool:
    encoded = password.encode()
    return len(encoded) <= 72 and bcrypt.checkpw(encoded, hashed.encode())


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue_token(user_id: int, kind: str, expires: timedelta, jti: str | None = None) -> str:
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user_id),
            "type": kind,
            "iat": now,
            "exp": now + expires,
            "jti": jti or str(uuid.uuid4()),
            "iss": "procureai",
            "aud": "procureai",
        },
        settings.jwt_secret.get_secret_value(),
        algorithm="HS256",
    )


def decode_token(token: str, kind: str) -> dict:
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=["HS256"],
            issuer="procureai",
            audience="procureai",
            options={"require": ["sub", "exp", "iat", "jti", "type"]},
        )
        if claims["type"] != kind or not claims["sub"].isdigit():
            raise jwt.InvalidTokenError("Invalid token type or subject")
        return claims
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            401, "Invalid or expired credentials", headers={"WWW-Authenticate": "Bearer"}
        ) from exc
