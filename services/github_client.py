import os

import httpx


class GitHubRestService:
    """Service to interact with GitHub GraphQL API."""

    GRAPHQL_URL = "https://api.github.com/graphql"

    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError(
                "GITHUB_TOKEN environment variable is required for GraphQL API"
            )
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def _execute_query(self, query: str, variables: dict) -> dict:
        """Execute a GraphQL query."""
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.GRAPHQL_URL,
                json={"query": query, "variables": variables},
                headers=self.headers,
            )
            response.raise_for_status()
            result = response.json()

            if "errors" in result:
                raise Exception(f"GraphQL errors: {result['errors']}")

            return result["data"]

    async def get_stargazers_with_starred_repos(
        self, owner: str, repo: str
    ) -> dict[str, list[str]]:
        """
        Fetch all stargazers for a given repository.
        """
        query = """
		query($owner: String!, $repo: String!, $cursor: String) {
			repository(owner: $owner, name: $repo) {
				stargazers(first: 100, after: $cursor) {
					pageInfo {
						hasNextPage
						endCursor
					}
					edges {
						node {
							login
							starredRepositories(first: 100) {
								pageInfo {
									hasNextPage
									endCursor
								}
								nodes {
									nameWithOwner
								}
							}
						}
					}
				}
			}
		}
		"""

        stargazer_repos = {}
        cursor = None
        has_next_page = True

        while has_next_page:
            variables = {"owner": owner, "repo": repo, "cursor": cursor}
            data = await self._execute_query(query, variables)

            if not data or "repository" not in data or not data["repository"]:
                break

            stargazers_data = data["repository"]["stargazers"]

            for edge in stargazers_data["edges"]:
                stargazer = edge["node"]["login"]
                starred_repos = [
                    node["nameWithOwner"]
                    for node in edge["node"]["starredRepositories"]["nodes"]
                ]

                # If user has more than 100 starred repos, fetch the rest
                starred_page_info = edge["node"]["starredRepositories"]["pageInfo"]
                if starred_page_info["hasNextPage"]:
                    additional_repos = await self._get_remaining_starred_repos(
                        stargazer, starred_page_info["endCursor"]
                    )
                    starred_repos.extend(additional_repos)

                stargazer_repos[stargazer] = starred_repos

            page_info = stargazers_data["pageInfo"]
            has_next_page = page_info["hasNextPage"]
            cursor = page_info["endCursor"]

        return stargazer_repos

    async def _get_remaining_starred_repos(
        self, username: str, cursor: str
    ) -> list[str]:
        """Fetch remaining starred repositories for a user when they have more than 100."""
        query = """
		query($username: String!, $cursor: String!) {
			user(login: $username) {
				starredRepositories(first: 100, after: $cursor) {
					pageInfo {
						hasNextPage
						endCursor
					}
					nodes {
						nameWithOwner
					}
				}
			}
		}
		"""

        repos = []
        has_next_page = True

        while has_next_page:
            variables = {"username": username, "cursor": cursor}
            data = await self._execute_query(query, variables)

            if not data or "user" not in data or not data["user"]:
                break

            starred_data = data["user"]["starredRepositories"]
            repos.extend([node["nameWithOwner"] for node in starred_data["nodes"]])

            page_info = starred_data["pageInfo"]
            has_next_page = page_info["hasNextPage"]
            cursor = page_info["endCursor"]

        return repos
