from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from . import AsyncSessionLocal


async def get_db() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionLocal() as session:
        yield session
