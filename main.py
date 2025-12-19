from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI

from api.routes import router
from config.database import close_db, init_db

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager to handle startup and shutdown events.
    """
    # Startup: Initialize database
    await init_db()
    yield
    # Shutdown: Close database connection
    await close_db()


app = FastAPI(
    title="Stargazer Neighbor API",
    description="API to find GitHub repositories with shared stargazers",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)
