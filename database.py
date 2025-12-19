import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession


def get_database_url() -> str:
    """
    Construct the database URL from environment variables.
    """
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "stargazer")
    user = os.getenv("POSTGRES_USER", "stargazer_user")
    password = os.getenv("POSTGRES_PASSWORD", "changeme123")

    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


# Global engine instance
engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """
    Get or create the database engine.
    """
    global engine
    if engine is None:
        database_url = get_database_url()
        engine = create_async_engine(
            database_url,
            echo=True,  # Set to False in production
            future=True,
        )
    return engine


async def init_db() -> None:
    """
    Initialize the database by creating all tables.
    """
    async with get_engine().begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def close_db() -> None:
    """
    Close the database connection.
    """
    global engine
    if engine is not None:
        await engine.dispose()
        engine = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get a database session.
    """
    async with AsyncSession(get_engine(), expire_on_commit=False) as session:
        yield session
