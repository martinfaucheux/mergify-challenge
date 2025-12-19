import httpx
from fastapi import APIRouter, Depends, HTTPException

from api.models import User
from api.schemas import NeighborResponse
from config.auth import verify_api_key
from services.neighbor_finder import NeighborFinder

router = APIRouter()


@router.get(
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
    neighbor_finder = NeighborFinder()

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
