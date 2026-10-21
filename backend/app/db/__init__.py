from pathlib import Path

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ..core.config import BACKEND_DIR, settings

database_url = make_url(settings.database_url)
if database_url.get_backend_name() == "sqlite":
    if database_url.drivername == "sqlite":
        database_url = database_url.set(drivername="sqlite+aiosqlite")
    if database_url.database and database_url.database != ":memory:":
        database_path = Path(database_url.database)
        if not database_path.is_absolute():
            database_path = BACKEND_DIR / database_path
        database_path.parent.mkdir(parents=True, exist_ok=True)
        database_url = database_url.set(database=str(database_path))
elif database_url.get_backend_name() in {"postgres", "postgresql"}:
    if database_url.drivername != "postgresql+asyncpg":
        database_url = database_url.set(drivername="postgresql+asyncpg")

engine = create_async_engine(database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
