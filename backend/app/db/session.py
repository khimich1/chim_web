"""Async SQLAlchemy session and FastAPI dependency.

Source: https://fastapi.tiangolo.com/advanced/async-sql-databases/
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

_engine: AsyncEngine | None = None
_async_session_maker: async_sessionmaker[AsyncSession] | None = None


def init_engine(database_url: str) -> None:
    """Create async engine and session factory (called on app startup)."""
    global _engine, _async_session_maker
    _engine = create_async_engine(database_url, echo=False)
    _async_session_maker = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def dispose_engine() -> None:
    """Dispose engine on app shutdown."""
    global _engine, _async_session_maker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _async_session_maker = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield a request-scoped async session; closes after the request."""
    if _async_session_maker is None:
        raise RuntimeError("Database engine is not initialized")
    async with _async_session_maker() as session:
        yield session
