import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.config import settings
from ...db.session import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "environment": settings.app_env}


@router.get("/health/ready", tags=["Health"])
async def readiness_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.exception("Database readiness check failed")
        raise HTTPException(status_code=503, detail="Database is not reachable") from exc
    return {"status": "ready"}
