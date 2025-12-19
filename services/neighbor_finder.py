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
        # Step 1: Get all stargazers of the target repository
        stargazers = await self.github_service.get_stargazers(owner, repo)

        # Step 2: For each stargazer, fetch their starred repositories
        # Using a dict to track: repo_full_name -> set of common stargazers
        neighbor_repos = defaultdict(set)

        for stargazer in stargazers:
            try:
                starred_repos = await self.github_service.get_starred_repos(stargazer)

                for starred_repo in starred_repos:
                    repo_full_name = starred_repo["full_name"]
                    # Skip the original repository
                    if repo_full_name.lower() != f"{owner}/{repo}".lower():
                        neighbor_repos[repo_full_name].add(stargazer)
            except Exception as e:
                # Continue with other stargazers if one fails
                print(f"Error fetching starred repos for {stargazer}: {e}")
                continue

        # Step 3: Format the results
        results = []
        for repo_name, stargazer_set in neighbor_repos.items():
            results.append(
                {"repo": repo_name, "stargazers": sorted(list(stargazer_set))}
            )

        # Sort by number of common stargazers (descending)
        results.sort(key=lambda x: len(x["stargazers"]), reverse=True)

        return results
