from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from api.models import User

NEIGHBOR_FINDER_PATH = "services.neighbor_finder.NeighborFinder.find_star_neighbours"


class TestStarNeighboursRoute:
    """Test suite for the star neighbours endpoint."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Set up mocks for GitHub services that will be used across all tests."""
        # Create a mock for the NeighborFinder instance
        self.mock_neighbor_finder = MagicMock()
        self.mock_neighbor_finder.find_star_neighbours = AsyncMock()

    def test_get_star_neighbours_success(
        self, client: TestClient, test_user: User, setup_mocks
    ):
        """
        GIVEN a valid API key and a repository with star neighbours
        WHEN requesting the star neighbours endpoint
        THEN the neighbours should be returned with correct structure
        """
        # Arrange
        expected_neighbors = [
            {"repo": "user1/repo1", "stargazers": ["alice", "bob"]},
            {"repo": "user2/repo2", "stargazers": ["alice"]},
        ]

        with patch(NEIGHBOR_FINDER_PATH, return_value=expected_neighbors):
            # Act
            response = client.get(
                "/repos/testowner/testrepo/starneighbours",
                headers={"X-API-Key": test_user.api_key},
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["repo"] == "user1/repo1"
            assert data[0]["stargazers"] == ["alice", "bob"]
            assert data[1]["repo"] == "user2/repo2"
            assert data[1]["stargazers"] == ["alice"]

    def test_get_star_neighbours_empty_result(
        self, client: TestClient, test_user: User, setup_mocks
    ):
        """
        GIVEN a valid API key and a repository with no star neighbours
        WHEN requesting the star neighbours endpoint
        THEN an empty list should be returned with 200 status
        """
        # Arrange
        with patch(NEIGHBOR_FINDER_PATH, return_value=[]):
            # Act
            response = client.get(
                "/repos/testowner/testrepo/starneighbours",
                headers={"X-API-Key": test_user.api_key},
            )

            # Assert
            assert response.status_code == 200
            assert response.json() == []

    def test_get_star_neighbours_no_api_key(self, client: TestClient):
        """
        GIVEN a request without an API key
        WHEN requesting the star neighbours endpoint
        THEN a 401 Unauthorized error should be returned
        """
        # Act
        response = client.get("/repos/testowner/testrepo/starneighbours")

        # Assert
        assert response.status_code == 401
        assert "API key is missing" in response.json()["detail"]

    def test_get_star_neighbours_invalid_api_key(self, client: TestClient):
        """
        GIVEN a request with an invalid API key
        WHEN requesting the star neighbours endpoint
        THEN a 401 Unauthorized error should be returned
        """
        # Act
        response = client.get(
            "/repos/testowner/testrepo/starneighbours",
            headers={"X-API-Key": "invalid-key"},
        )

        # Assert
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]

    def test_get_star_neighbours_expired_api_key(
        self, client: TestClient, expired_user: User
    ):
        """
        GIVEN a request with an expired API key
        WHEN requesting the star neighbours endpoint
        THEN a 401 Unauthorized error should be returned
        """
        # Act
        response = client.get(
            "/repos/testowner/testrepo/starneighbours",
            headers={"X-API-Key": expired_user.api_key},
        )

        # Assert
        assert response.status_code == 401
        assert "API key has expired" in response.json()["detail"]

    def test_get_star_neighbours_repository_not_found(
        self, client: TestClient, test_user: User, setup_mocks
    ):
        """
        GIVEN a valid API key and a nonexistent repository
        WHEN requesting the star neighbours endpoint
        THEN a 404 Not Found error should be returned
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 404
        http_error = httpx.HTTPStatusError(
            "Not Found", request=MagicMock(), response=mock_response
        )

        with patch(NEIGHBOR_FINDER_PATH, side_effect=http_error):
            # Act
            response = client.get(
                "/repos/nonexistent/repo/starneighbours",
                headers={"X-API-Key": test_user.api_key},
            )

            # Assert
            assert response.status_code == 404
            assert "Repository not found" in response.json()["detail"]

    def test_get_star_neighbours_rate_limit_exceeded(
        self, client: TestClient, test_user: User, setup_mocks
    ):
        """
        GIVEN a valid API key and GitHub API rate limit is exceeded
        WHEN requesting the star neighbours endpoint
        THEN a 403 Forbidden error should be returned
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 403
        http_error = httpx.HTTPStatusError(
            "Forbidden", request=MagicMock(), response=mock_response
        )

        with patch(NEIGHBOR_FINDER_PATH, side_effect=http_error):
            # Act
            response = client.get(
                "/repos/testowner/testrepo/starneighbours",
                headers={"X-API-Key": test_user.api_key},
            )

            # Assert
            assert response.status_code == 403
            assert "rate limit" in response.json()["detail"].lower()

    def test_get_star_neighbours_github_server_error(
        self, client: TestClient, test_user: User, setup_mocks
    ):
        """
        GIVEN a valid API key and GitHub API returns a server error
        WHEN requesting the star neighbours endpoint
        THEN a 503 Service Unavailable error should be returned
        """
        # Arrange
        mock_response = MagicMock()
        mock_response.status_code = 503
        http_error = httpx.HTTPStatusError(
            "Service Unavailable", request=MagicMock(), response=mock_response
        )

        with patch(NEIGHBOR_FINDER_PATH, side_effect=http_error):
            # Act
            response = client.get(
                "/repos/testowner/testrepo/starneighbours",
                headers={"X-API-Key": test_user.api_key},
            )

            # Assert
            assert response.status_code == 503

    def test_get_star_neighbours_internal_error(
        self, client: TestClient, test_user: User, setup_mocks
    ):
        """
        GIVEN a valid API key and an unexpected error occurs
        WHEN requesting the star neighbours endpoint
        THEN a 500 Internal Server Error should be returned
        """
        # Arrange
        with patch(NEIGHBOR_FINDER_PATH, side_effect=Exception("Unexpected error")):
            # Act
            response = client.get(
                "/repos/testowner/testrepo/starneighbours",
                headers={"X-API-Key": test_user.api_key},
            )

            # Assert
            assert response.status_code == 500
            assert "Internal server error" in response.json()["detail"]

    def test_get_star_neighbours_with_special_characters(
        self, client: TestClient, test_user: User, setup_mocks
    ):
        """
        GIVEN a valid API key and repository names with special characters
        WHEN requesting the star neighbours endpoint
        THEN the neighbours should be returned successfully
        """
        # Arrange
        expected_neighbors = [
            {"repo": "user/repo-with-dashes", "stargazers": ["user1"]},
            {"repo": "user/repo.with.dots", "stargazers": ["user2"]},
        ]

        with patch(NEIGHBOR_FINDER_PATH, return_value=expected_neighbors):
            # Act
            response = client.get(
                "/repos/test-owner/test.repo/starneighbours",
                headers={"X-API-Key": test_user.api_key},
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2

    def test_get_star_neighbours_large_result_set(
        self, client: TestClient, test_user: User, setup_mocks
    ):
        """
        GIVEN a valid API key and a repository with 100 star neighbours
        WHEN requesting the star neighbours endpoint
        THEN all 100 neighbours should be returned successfully
        """
        # Arrange
        expected_neighbors = [
            {"repo": f"user{i}/repo{i}", "stargazers": [f"stargazer{i}"]}
            for i in range(100)
        ]

        with patch(NEIGHBOR_FINDER_PATH, return_value=expected_neighbors):
            # Act
            response = client.get(
                "/repos/testowner/testrepo/starneighbours",
                headers={"X-API-Key": test_user.api_key},
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 100

    def test_get_star_neighbours_response_schema(
        self, client: TestClient, test_user: User, setup_mocks
    ):
        """
        GIVEN a valid API key and a repository with star neighbours
        WHEN requesting the star neighbours endpoint
        THEN the response should match the expected schema structure
        """
        # Arrange
        expected_neighbors = [
            {"repo": "user1/repo1", "stargazers": ["alice", "bob", "charlie"]},
        ]

        with patch(NEIGHBOR_FINDER_PATH, return_value=expected_neighbors):
            # Act
            response = client.get(
                "/repos/testowner/testrepo/starneighbours",
                headers={"X-API-Key": test_user.api_key},
            )

            # Assert
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            for item in data:
                assert "repo" in item
                assert "stargazers" in item
                assert isinstance(item["repo"], str)
                assert isinstance(item["stargazers"], list)
                assert all(isinstance(s, str) for s in item["stargazers"])
