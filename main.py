import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from neighbor_finder import NeighborFinder

load_dotenv()

app = FastAPI(
    title="Stargazer Neighbor API",
    description="API to find GitHub repositories with shared stargazers",
    version="0.1.0",
)

neighbor_finder = NeighborFinder()


class NeighborResponse(BaseModel):
    repo: str
    stargazers: list[str]


@app.get("/repos/{github_user}/{github_repo}/starneighbours")
async def get_star_neighbours(
    github_user: str, github_repo: str
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
