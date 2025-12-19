from contextlib import asynccontextmanager

import httpx
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from auth import verify_api_key
from database import close_db, init_db
from models import User
from neighbor_finder import NeighborFinder

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

# API Key security scheme
neighbor_finder = NeighborFinder()


class NeighborResponse(BaseModel):
    repo: str
    stargazers: list[str]


@app.get(
    "/repos/{github_user}/{github_repo}/starneighbours",
    summary="Get Star Neighbours",
    description="Find repositories that share stargazers with the specified repository",
)
async def get_star_neighbours(
    github_user: str,
    github_repo: str,
    current_user: User = Depends(verify_api_key),
) -> list[NeighborResponse]:
    """
    Get neighbor repositories that share stargazers with the given repository.

    Args:
        github_user: GitHub repository owner username
        github_repo: GitHub repository name

    Returns:
        List of neighbor repositories with their common stargazers
    """
    try:
        neighbors = await neighbor_finder.find_star_neighbours(github_user, github_repo)
        return neighbors
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Repository not found")
        elif e.response.status_code == 403:
            raise HTTPException(
                status_code=403, detail="API rate limit exceeded or access forbidden"
            )
        else:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
