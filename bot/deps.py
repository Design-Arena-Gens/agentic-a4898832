from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from .database import async_session_factory


@asynccontextmanager
async def db_session() -> AsyncSession:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
