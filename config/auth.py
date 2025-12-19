from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from api.models import User
from config.database import get_session

# API Key security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(
    api_key: str = Security(api_key_header),
    session: AsyncSession = Depends(get_session),
) -> User:
    """
    Verify the API key and return the associated user.

    Args:
        api_key: The API key from the X-API-Key header
        session: Database session

    Returns:
        User object if authentication succeeds

    Raises:
        HTTPException: 401 if API key is missing, invalid, or expired
    """
    if not api_key:
        raise HTTPException(status_code=401, detail="API key is missing")

    # Query for user with matching API key
    statement = select(User).where(User.api_key == api_key)
    result = await session.exec(statement)
    user = result.one_or_none()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Do the expiration check after confirming user exists
    # Handle both timezone-aware (PostgreSQL) and timezone-naive (SQLite) datetimes
    now = datetime.now(timezone.utc)
    valid_until = user.api_key_valid_until

    # Make comparison work for both timezone-aware and timezone-naive datetimes
    if valid_until.tzinfo is None:
        # If stored datetime is naive (e.g., SQLite), compare with naive datetime
        now = now.replace(tzinfo=None)

    if valid_until < now:
        raise HTTPException(status_code=401, detail="API key has expired")

    return user
