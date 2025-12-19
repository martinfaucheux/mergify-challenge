import pytest
from httpx import Request

from services.github_client import GitHubRestService
from services.neighbor_finder import NeighborFinder


class MockResponse:
    """Mock httpx Response object."""

    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json_data = json_data
        self._request = Request("GET", "https://api.github.com")

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


class TestGitHubRestService:
    """Tests for GitHubRestService."""

    @pytest.mark.asyncio
    async def test_get_stargazers_single_page(self, monkeypatch):
        """
        GIVEN a repository with 3 stargazers
        WHEN fetching stargazers from the GitHub API
        THEN all stargazers should be returned in a single page
        """
        service = GitHubRestService()

        # Mock response data
        mock_stargazers = [
            {"login": "user1"},
            {"login": "user2"},
            {"login": "user3"},
        ]

        async def mock_get(url, headers=None, params=None):
            if params["page"] == 1:
                return MockResponse(200, mock_stargazers)
            return MockResponse(200, [])

        class MockAsyncClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def get(self, url, headers=None, params=None):
                return await mock_get(url, headers, params)

        monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)

        stargazers = await service.get_stargazers("owner", "repo")

        assert len(stargazers) == 3
        assert stargazers == ["user1", "user2", "user3"]

    @pytest.mark.asyncio
    async def test_get_stargazers_multiple_pages(self, monkeypatch):
        """
        GIVEN a repository with 150 stargazers across multiple pages
        WHEN fetching stargazers from the GitHub API
        THEN all stargazers should be fetched across pages and returned
        """
        service = GitHubRestService()

        # Mock response data for multiple pages
        page1_data = [{"login": f"user{i}"} for i in range(1, 101)]
        page2_data = [{"login": f"user{i}"} for i in range(101, 151)]

        call_count = {"count": 0}

        async def mock_get(url, headers=None, params=None):
            call_count["count"] += 1
            if params["page"] == 1:
                return MockResponse(200, page1_data)
            elif params["page"] == 2:
                return MockResponse(200, page2_data)
            return MockResponse(200, [])

        class MockAsyncClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def get(self, url, headers=None, params=None):
                return await mock_get(url, headers, params)

        monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)

        stargazers = await service.get_stargazers("owner", "repo")

        assert len(stargazers) == 150
        assert stargazers[0] == "user1"
        assert stargazers[99] == "user100"
        assert stargazers[149] == "user150"
        assert call_count["count"] == 3  # 2 pages with data + 1 empty page

    @pytest.mark.asyncio
    async def test_get_stargazers_empty_repo(self, monkeypatch):
        """
        GIVEN a repository with no stargazers
        WHEN fetching stargazers from the GitHub API
        THEN an empty list should be returned
        """
        service = GitHubRestService()

        async def mock_get(url, headers=None, params=None):
            return MockResponse(200, [])

        class MockAsyncClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def get(self, url, headers=None, params=None):
                return await mock_get(url, headers, params)

        monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)

        stargazers = await service.get_stargazers("owner", "repo")

        assert len(stargazers) == 0
        assert stargazers == []

    @pytest.mark.asyncio
    async def test_get_starred_repos_single_page(self, monkeypatch):
        """
        GIVEN a user who has starred 2 repositories
        WHEN fetching their starred repositories from the GitHub API
        THEN all repositories should be returned with correct structure
        """
        service = GitHubRestService()

        mock_repos = [
            {
                "name": "repo1",
                "owner": {"login": "owner1"},
                "full_name": "owner1/repo1",
            },
            {
                "name": "repo2",
                "owner": {"login": "owner2"},
                "full_name": "owner2/repo2",
            },
        ]

        async def mock_get(url, headers=None, params=None):
            if params["page"] == 1:
                return MockResponse(200, mock_repos)
            return MockResponse(200, [])

        class MockAsyncClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def get(self, url, headers=None, params=None):
                return await mock_get(url, headers, params)

        monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)

        repos = await service.get_starred_repos("testuser")

        assert len(repos) == 2
        assert repos[0] == {
            "owner": "owner1",
            "name": "repo1",
            "full_name": "owner1/repo1",
        }
        assert repos[1] == {
            "owner": "owner2",
            "name": "repo2",
            "full_name": "owner2/repo2",
        }

    @pytest.mark.asyncio
    async def test_get_starred_repos_multiple_pages(self, monkeypatch):
        """
        GIVEN a user who has starred 125 repositories across multiple pages
        WHEN fetching their starred repositories from the GitHub API
        THEN all repositories should be fetched across pages and returned
        """
        service = GitHubRestService()

        page1_repos = [
            {
                "name": f"repo{i}",
                "owner": {"login": f"owner{i}"},
                "full_name": f"owner{i}/repo{i}",
            }
            for i in range(1, 101)
        ]
        page2_repos = [
            {
                "name": f"repo{i}",
                "owner": {"login": f"owner{i}"},
                "full_name": f"owner{i}/repo{i}",
            }
            for i in range(101, 126)
        ]

        async def mock_get(url, headers=None, params=None):
            if params["page"] == 1:
                return MockResponse(200, page1_repos)
            elif params["page"] == 2:
                return MockResponse(200, page2_repos)
            return MockResponse(200, [])

        class MockAsyncClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def get(self, url, headers=None, params=None):
                return await mock_get(url, headers, params)

        monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)

        repos = await service.get_starred_repos("testuser")

        assert len(repos) == 125
        assert repos[0]["full_name"] == "owner1/repo1"
        assert repos[124]["full_name"] == "owner125/repo125"


class TestNeighborFinder:
    """Tests for NeighborFinder service."""

    @pytest.mark.asyncio
    async def test_find_star_neighbours_basic(self, monkeypatch):
        """
        GIVEN a repository with 3 stargazers who have starred various other repos
        WHEN finding star neighbors
        THEN neighbor repos should be returned sorted by common stargazer count
        """
        finder = NeighborFinder()

        # Mock data
        target_stargazers = ["alice", "bob", "charlie"]
        alice_repos = [
            {
                "name": "cool-project",
                "owner": {"login": "owner1"},
                "full_name": "owner1/cool-project",
            },
            {
                "name": "awesome-lib",
                "owner": {"login": "owner2"},
                "full_name": "owner2/awesome-lib",
            },
        ]
        bob_repos = [
            {
                "name": "cool-project",
                "owner": {"login": "owner1"},
                "full_name": "owner1/cool-project",
            },
        ]
        charlie_repos = [
            {
                "name": "different-repo",
                "owner": {"login": "owner3"},
                "full_name": "owner3/different-repo",
            },
        ]

        async def mock_get(url, headers=None, params=None):
            if "/stargazers" in url:
                if params["page"] == 1:
                    return MockResponse(200, [{"login": u} for u in target_stargazers])
                return MockResponse(200, [])
            elif "/starred" in url:
                if "alice" in url:
                    if params["page"] == 1:
                        return MockResponse(200, alice_repos)
                    return MockResponse(200, [])
                elif "bob" in url:
                    if params["page"] == 1:
                        return MockResponse(200, bob_repos)
                    return MockResponse(200, [])
                elif "charlie" in url:
                    if params["page"] == 1:
                        return MockResponse(200, charlie_repos)
                    return MockResponse(200, [])
            return MockResponse(200, [])

        class MockAsyncClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def get(self, url, headers=None, params=None):
                return await mock_get(url, headers, params)

        monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)

        results = await finder.find_star_neighbours("testowner", "testrepo")

        # Should have 3 neighbor repos
        assert len(results) == 3

        # cool-project should be first (2 common stargazers)
        assert results[0]["repo"] == "owner1/cool-project"
        assert set(results[0]["stargazers"]) == {"alice", "bob"}

        # awesome-lib and different-repo should have 1 stargazer each
        repo_names = {r["repo"] for r in results[1:]}
        assert "owner2/awesome-lib" in repo_names
        assert "owner3/different-repo" in repo_names

    @pytest.mark.asyncio
    async def test_find_star_neighbours_excludes_original_repo(self, monkeypatch):
        """
        GIVEN a stargazer who has starred both the target repo and other repos
        WHEN finding star neighbors
        THEN the target repository should be excluded from the results
        """
        finder = NeighborFinder()

        alice_repos = [
            {
                "name": "testrepo",
                "owner": {"login": "testowner"},
                "full_name": "testowner/testrepo",
            },
            {
                "name": "other-repo",
                "owner": {"login": "owner1"},
                "full_name": "owner1/other-repo",
            },
        ]

        async def mock_get(url, headers=None, params=None):
            if "/stargazers" in url:
                if params["page"] == 1:
                    return MockResponse(200, [{"login": "alice"}])
                return MockResponse(200, [])
            elif "/starred" in url and "alice" in url:
                if params["page"] == 1:
                    return MockResponse(200, alice_repos)
                return MockResponse(200, [])
            return MockResponse(200, [])

        class MockAsyncClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def get(self, url, headers=None, params=None):
                return await mock_get(url, headers, params)

        monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)

        results = await finder.find_star_neighbours("testowner", "testrepo")

        # Should only have other-repo, not the original testrepo
        assert len(results) == 1
        assert results[0]["repo"] == "owner1/other-repo"
        assert results[0]["stargazers"] == ["alice"]

    @pytest.mark.asyncio
    async def test_find_star_neighbours_no_stargazers(self, monkeypatch):
        """
        GIVEN a repository with no stargazers
        WHEN finding star neighbors
        THEN an empty list should be returned
        """
        finder = NeighborFinder()

        async def mock_get(url, headers=None, params=None):
            return MockResponse(200, [])

        class MockAsyncClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def get(self, url, headers=None, params=None):
                return await mock_get(url, headers, params)

        monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)

        results = await finder.find_star_neighbours("testowner", "testrepo")

        assert len(results) == 0
        assert results == []

    @pytest.mark.asyncio
    async def test_find_star_neighbours_handles_errors(self, monkeypatch, capsys):
        """
        GIVEN one stargazer's repos are accessible and another stargazer returns an error
        WHEN finding star neighbors
        THEN the process should continue and return results from successful requests
        """
        finder = NeighborFinder()

        target_stargazers = ["alice", "bob"]
        alice_repos = [
            {
                "name": "repo1",
                "owner": {"login": "owner1"},
                "full_name": "owner1/repo1",
            },
        ]

        call_count = {"alice": 0, "bob": 0}

        async def mock_get(url, headers=None, params=None):
            if "/stargazers" in url:
                if params["page"] == 1:
                    return MockResponse(200, [{"login": u} for u in target_stargazers])
                return MockResponse(200, [])
            elif "/starred" in url:
                if "alice" in url:
                    call_count["alice"] += 1
                    if params["page"] == 1:
                        return MockResponse(200, alice_repos)
                    return MockResponse(200, [])
                elif "bob" in url:
                    call_count["bob"] += 1
                    # Simulate an error for bob
                    response = MockResponse(404, {"message": "Not Found"})
                    response.raise_for_status()
                    return response
            return MockResponse(200, [])

        class MockAsyncClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                pass

            async def get(self, url, headers=None, params=None):
                return await mock_get(url, headers, params)

        monkeypatch.setattr("httpx.AsyncClient", MockAsyncClient)

        results = await finder.find_star_neighbours("testowner", "testrepo")

        # Should still have alice's repos even though bob failed
        assert len(results) == 1
        assert results[0]["repo"] == "owner1/repo1"
        assert results[0]["stargazers"] == ["alice"]

        # Verify error was logged
        captured = capsys.readouterr()
        assert "Error fetching starred repos for bob" in captured.out
