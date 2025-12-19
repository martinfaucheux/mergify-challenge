from collections import defaultdict

from services.github_client import GitHubRestService


class NeighborFinder:
    """Service to find neighbor repositories based on common stargazers."""

    def __init__(self):
        self.github_service = GitHubRestService()

    async def find_star_neighbours(self, owner: str, repo: str) -> list[dict]:
        """
        Find neighbor repositories that share stargazers with the given repository.

        Args:
            owner: Repository owner username
            repo: Repository name

        Returns:
            List of neighbor repositories with their common stargazers
        """
        # Fetch all stargazers and their starred repos in batched GraphQL queries
        stargazer_repos = await self.github_service.get_stargazers_with_starred_repos(
            owner, repo
        )

        # Track repo_full_name -> set of common stargazers
        neighbor_repos = defaultdict(set)
        target_repo = f"{owner}/{repo}".lower()

        # Process all stargazers and their starred repos
        for stargazer, starred_repos in stargazer_repos.items():
            for repo_full_name in starred_repos:
                # Skip the original repository
                if repo_full_name.lower() != target_repo:
                    neighbor_repos[repo_full_name].add(stargazer)

        # Format the results
        results = [
            {"repo": repo_name, "stargazers": sorted(list(stargazer_set))}
            for repo_name, stargazer_set in neighbor_repos.items()
        ]

        # Sort by number of common stargazers (descending)
        results.sort(key=lambda x: len(x["stargazers"]), reverse=True)

        return results
