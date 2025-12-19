from pydantic import BaseModel


class NeighborResponse(BaseModel):
    repo: str
    stargazers: list[str]
