from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.pool import StaticPool

from database import get_session
from main import app
from models import User


@pytest_asyncio.fixture(name="session")
async def session_fixture():
    """Create a fresh in-memory database for each test."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session

    await engine.dispose()


@pytest.fixture(name="client")
def client_fixture(session: AsyncSession):
    """Create a test client with the test database session."""

    async def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(name="test_user")
async def test_user_fixture(session: AsyncSession):
    """Create a test user with a valid API key."""
    # Use timezone-naive datetime for SQLite compatibility
    user = User(
        username="testuser",
        email="test@example.com",
        api_key="test-api-key-12345",
        api_key_valid_until=datetime.now(timezone.utc).replace(tzinfo=None)
        + timedelta(days=30),
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest_asyncio.fixture(name="expired_user")
async def expired_user_fixture(session: AsyncSession):
    """Create a test user with an expired API key."""
    # Use timezone-naive datetime for SQLite compatibility
    user = User(
        username="expireduser",
        email="expired@example.com",
        api_key="expired-api-key-12345",
        api_key_valid_until=datetime.now(timezone.utc).replace(tzinfo=None)
        - timedelta(days=1),
        created_at=datetime.now(timezone.utc).replace(tzinfo=None),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
