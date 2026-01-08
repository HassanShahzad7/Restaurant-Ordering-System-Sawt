"""Database connection pool management using asyncpg."""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import asyncpg
from asyncpg import Pool

from sawt.config import get_settings


class DatabasePool:
    """Manages asyncpg connection pool lifecycle."""

    _pool: Pool | None = None
    _lock: asyncio.Lock = asyncio.Lock()

    @classmethod
    async def get_pool(cls) -> Pool:
        """Get or create the connection pool."""
        if cls._pool is None:
            async with cls._lock:
                if cls._pool is None:
                    settings = get_settings()
                    cls._pool = await asyncpg.create_pool(
                        dsn=settings.database_url,
                        min_size=settings.db_pool_min_size,
                        max_size=settings.db_pool_max_size,
                        command_timeout=60,
                    )
        return cls._pool

    @classmethod
    async def close_pool(cls) -> None:
        """Close the connection pool."""
        if cls._pool is not None:
            await cls._pool.close()
            cls._pool = None

    @classmethod
    @asynccontextmanager
    async def acquire(cls) -> AsyncGenerator[asyncpg.Connection, None]:
        """Acquire a connection from the pool."""
        pool = await cls.get_pool()
        async with pool.acquire() as connection:
            yield connection

    @classmethod
    @asynccontextmanager
    async def transaction(cls) -> AsyncGenerator[asyncpg.Connection, None]:
        """Acquire a connection with transaction."""
        async with cls.acquire() as connection:
            async with connection.transaction():
                yield connection


async def init_db() -> Pool:
    """Initialize database connection pool."""
    return await DatabasePool.get_pool()


async def close_db() -> None:
    """Close database connection pool."""
    await DatabasePool.close_pool()


@asynccontextmanager
async def get_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """Get a database connection from the pool."""
    async with DatabasePool.acquire() as connection:
        yield connection


@asynccontextmanager
async def get_transaction() -> AsyncGenerator[asyncpg.Connection, None]:
    """Get a database connection with transaction."""
    async with DatabasePool.transaction() as connection:
        yield connection
