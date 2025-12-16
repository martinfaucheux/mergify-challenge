import os

import httpx


class GitHubRestService:
    """Service to interact with GitHub API."""

    BASE_URL = "https://api.github.com"

    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    async def get_stargazers(self, owner: str, repo: str) -> list[str]:
        """
        Fetch all stargazers for a given repository.
        """
        stargazers = []
        page = 1
        per_page = 100

        async with httpx.AsyncClient() as client:
            while True:
                url = f"{self.BASE_URL}/repos/{owner}/{repo}/stargazers"
                params = {"page": page, "per_page": per_page}

                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()
                if not data:
                    break

                stargazers.extend([user["login"] for user in data])
                page += 1

        return stargazers

    async def get_starred_repos(self, username: str) -> list[dict[str, str]]:
        """
        Fetch all repositories starred by a user.
        """
        repos = []
        page = 1
        per_page = 100

        async with httpx.AsyncClient() as client:
            while True:
                url = f"{self.BASE_URL}/users/{username}/starred"
                params = {"page": page, "per_page": per_page}

                response = await client.get(url, headers=self.headers, params=params)
                response.raise_for_status()

                data = response.json()
                if not data:
                    break

                for repo in data:
                    repos.append(
                        {
                            "owner": repo["owner"]["login"],
                            "name": repo["name"],
                            "full_name": repo["full_name"],
                        }
                    )

                page += 1

        return repos
