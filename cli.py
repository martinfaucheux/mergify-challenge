import asyncio
import secrets
from datetime import datetime, timedelta, timezone

import typer

from api.models import User
from config.database import get_session

app = typer.Typer()


@app.command()
def create_api_key(
    username: str,
    email: str,
    expire_at: str | None = None,
):
    """
    Create a new user with an API key and save it in the DB.
    If expire_at is not provided, the API key will expire in 90 days.

    Example:
        python cli.py create-api-key john john@example.com
        python cli.py create-api-key jane jane@example.com --expire-at "2026-12-31T23:59:59"
    """
    asyncio.run(_create_api_key_async(username, email, expire_at))


async def _create_api_key_async(
    username: str,
    email: str,
    expire_at: str | None,
):
    """
    Async implementation of create_api_key command.
    """
    # Generate a secure API key
    api_key = secrets.token_urlsafe(32)

    # Parse expiration date if provided
    valid_until = None
    if expire_at:
        try:
            valid_until = datetime.fromisoformat(expire_at)
            # Ensure timezone aware
            if valid_until.tzinfo is None:
                valid_until = valid_until.replace(tzinfo=timezone.utc)
        except ValueError:
            typer.echo(
                f"Error: Invalid date format '{expire_at}'. Use ISO format (YYYY-MM-DDTHH:MM:SS)",
                err=True,
            )
            raise typer.Exit(1)
    else:
        # Set far future date if no expiration
        valid_until = datetime.now(timezone.utc) + timedelta(days=90)

    # Create user in database
    async for session in get_session():
        try:
            user = User(
                username=username,
                email=email,
                api_key=api_key,
                api_key_valid_until=valid_until,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)

            typer.echo("✓ User created successfully!")
            typer.echo(f"  Username: {user.username}")
            typer.echo(f"  Email: {user.email}")
            typer.echo(f"  API Key: {api_key}")
            typer.echo(f"  Valid Until: {valid_until.isoformat()}")
            typer.echo(f"  User ID: {user.id}")

        except Exception as e:
            typer.echo(f"Error creating user: {e}", err=True)
            raise typer.Exit(1)

        break  # Exit after first (and only) iteration


if __name__ == "__main__":
    app()
