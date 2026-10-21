import base64
import hashlib
import hmac
import json
import secrets
import time

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_db
from ..models.user import User
from .config import settings

_DEVELOPMENT_SECRET = secrets.token_bytes(32)
_PASSWORD_ITERATIONS = 310_000
_TOKEN_LIFETIME_SECONDS = 60 * 60
_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        _PASSWORD_ITERATIONS,
    )
    return "pbkdf2_sha256${}${}${}".format(
        _PASSWORD_ITERATIONS,
        _encode(salt),
        _encode(digest),
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations_text, salt_text, digest_text = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(iterations_text)
        if iterations < 100_000 or iterations > 2_000_000:
            return False
        expected = _decode(digest_text)
        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            _decode(salt_text),
            iterations,
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def create_access_token(user_id: int) -> tuple[str, int]:
    expires_at = int(time.time()) + _TOKEN_LIFETIME_SECONDS
    payload = _encode(
        json.dumps(
            {"sub": user_id, "exp": expires_at, "iss": "strandedpool"},
            separators=(",", ":"),
        ).encode("utf-8")
    )
    signature = _encode(hmac.new(_secret(), payload.encode("ascii"), hashlib.sha256).digest())
    return f"{payload}.{signature}", _TOKEN_LIFETIME_SECONDS


def decode_access_token(token: str) -> int:
    try:
        payload_text, signature_text = token.split(".", 1)
        expected_signature = hmac.new(
            _secret(),
            payload_text.encode("ascii"),
            hashlib.sha256,
        ).digest()
        if not hmac.compare_digest(_decode(signature_text), expected_signature):
            raise ValueError("Invalid token signature")
        payload = json.loads(_decode(payload_text))
        user_id = payload["sub"]
        expires_at = payload["exp"]
        if (
            payload.get("iss") != "strandedpool"
            or not isinstance(user_id, int)
            or user_id <= 0
            or not isinstance(expires_at, int)
            or expires_at <= int(time.time())
        ):
            raise ValueError("Invalid or expired token")
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return user_id


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None or credentials.scheme.casefold() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = decode_access_token(credentials.credentials)
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def _secret() -> bytes:
    if settings.auth_secret_key:
        return settings.auth_secret_key.encode("utf-8")
    return _DEVELOPMENT_SECRET


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
