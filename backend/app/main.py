import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import health
from .api.routes import bookings, disruptions, journeys, recovery
from .core.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="StrandedPool API",
    description="Travel disruption reporting and recovery planning. Transport information is not live inventory.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

app.include_router(health.router, prefix="/api")
app.include_router(journeys.router, prefix="/api")
app.include_router(disruptions.router, prefix="/api")
app.include_router(recovery.router, prefix="/api")
app.include_router(bookings.router, prefix="/api")


@app.get("/health", tags=["Health"], include_in_schema=False)
async def root_health_check():
    return {"status": "ok", "environment": settings.app_env}
