from contextlib import asynccontextmanager, contextmanager
from typing import AsyncGenerator, Generator

from pgvector.asyncpg import register_vector
from sqlalchemy import create_engine, event, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from .config.settings import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    echo=False,
    future=True,
    pool_size=10,
    max_overflow=20,
)


# Event listener to automatically register pgvector custom types on every raw asyncpg connection
@event.listens_for(engine.sync_engine, "connect")
def connect(dbapi_connection, connection_record):
    """Registers vector codec bindings directly onto the underlying asyncpg driver connection."""
    dbapi_connection.run_async(register_vector)


AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

sync_engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
)

SyncSessionLocal = sessionmaker(
    sync_engine,
    autocommit=False,
    autoflush=False,
)


# 3. SCHEMA & EXTENSION INITIALIZATION
async def init_db() -> None:
    """Verify pgvector is available and provision ORM tables."""
    import core.models  # noqa: F401

    async with engine.begin() as conn:
        result = await conn.execute(
            text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
        )
        if result.scalar() is None:
            raise RuntimeError(
                "The pgvector extension is not enabled on this database. "
                "Run scripts/setup-postgres.sql once as a PostgreSQL superuser, "
                "then retry."
            )
        await conn.run_sync(Base.metadata.create_all)


# Dependency for FastAPI
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Async context manager (for RabbitMQ consumers, background tasks, etc.)
@asynccontextmanager
async def get_async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async context manager for database sessions outside FastAPI dependencies.

    Usage:
        async with get_async_db_session() as db:
            # Your database operations
            pass
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Sync context manager (for Celery, APScheduler, etc.)
@contextmanager
def get_sync_db_session() -> Generator[Session, None, None]:
    """
    Sync context manager for database sessions in sync contexts.

    Usage:
        with get_sync_db_session() as db:
            # Your database operations
            pass
    """
    session = SyncSessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
