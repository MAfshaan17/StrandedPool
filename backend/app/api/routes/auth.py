import asyncio
import time
from collections import defaultdict, deque

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.auth import create_access_token, get_current_user, hash_password, verify_password
from ...db.session import get_db
from ...models.user import User
from ...schemas import AuthLogin, AuthRegister, AuthToken, AuthUser

router = APIRouter()
_attempts: dict[str, deque[float]] = defaultdict(deque)
_attempts_lock = asyncio.Lock()


@router.post("/auth/register", response_model=AuthToken, status_code=status.HTTP_201_CREATED)
async def register(
    payload: AuthRegister,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await _rate_limit(request, "register", max_attempts=5, window_seconds=3600)
    normalized_email = payload.email.strip().casefold()
    existing = await db.scalar(select(User.id).where(User.email == normalized_email))
    if existing is not None:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user = User(email=normalized_email, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        ) from exc
    await db.refresh(user)
    token, expires_in = create_access_token(user.id)
    return AuthToken(access_token=token, expires_in=expires_in, user=AuthUser.model_validate(user))


@router.post("/auth/login", response_model=AuthToken)
async def login(
    payload: AuthLogin,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    await _rate_limit(request, "login", max_attempts=10, window_seconds=900)
    normalized_email = payload.email.strip().casefold()
    user = await db.scalar(select(User).where(User.email == normalized_email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    token, expires_in = create_access_token(user.id)
    return AuthToken(access_token=token, expires_in=expires_in, user=AuthUser.model_validate(user))


@router.get("/auth/me", response_model=AuthUser)
async def current_user(user: User = Depends(get_current_user)):
    return user


async def _rate_limit(
    request: Request,
    action: str,
    max_attempts: int,
    window_seconds: int,
) -> None:
    client_host = request.client.host if request.client else "unknown"
    key = f"{action}:{client_host}"
    now = time.monotonic()
    async with _attempts_lock:
        attempts = _attempts[key]
        while attempts and now - attempts[0] >= window_seconds:
            attempts.popleft()
        if len(attempts) >= max_attempts:
            raise HTTPException(
                status_code=429,
                detail="Too many authentication attempts. Please try again later.",
                headers={"Retry-After": str(window_seconds)},
            )
        attempts.append(now)
