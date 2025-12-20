import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

# Import models so SQLModel.metadata knows about them
from api.models import User  # noqa: F401


def get_database_url() -> str:
    """
    Construct the database URL from environment variables.
    Supports both DATABASE_URL (Render) and individual POSTGRES_* variables (local).
    """
    # Check for Render's DATABASE_URL first
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        # Render provides postgresql:// but we need postgresql+asyncpg://
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        elif database_url.startswith("postgres://"):
            database_url = database_url.replace(
                "postgres://", "postgresql+asyncpg://", 1
            )
        return database_url

    # Fallback to individual environment variables for local development
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

        # Configure SSL for production (Render requires SSL)
        connect_args = {}
        if os.getenv("DATABASE_URL"):  # Production environment (Render)
            connect_args = {
                "ssl": "require",  # Require SSL connection
            }

        engine = create_async_engine(
            database_url,
            echo=True,  # Set to False in production
            future=True,
            connect_args=connect_args,
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
