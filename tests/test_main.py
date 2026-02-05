import pytest
from unittest.mock import patch, MagicMock

from src.main import retrieve_repo_names

@patch('src.main.Auth')
@patch('src.main.Github')
def test_funtion_returns_list(mock_github, mock_auth):
    """
    Test that retrieve_repo_names returns a list of strings.
    """

    mock_auth_instance = mock_auth.return_value
    mock_github_instance = mock_github.return_value

    mock_user = MagicMock()
    mock_repo = MagicMock()
    mock_repo.name = "coolest-repo-ever"

    mock_github_instance.get_user.return_value = mock_user
    mock_user.get_repos.return_value = [mock_repo]

    result = retrieve_repo_names("mock_token")

    assert isinstance(result, list), "Should return a list"
    assert len(result) == 1, "Should have exactly one repo name"
    assert result[0] == "coolest-repo-ever", "The repo name should match our mock"
    assert isinstance(result[0], str), "The items in the list should be strings"

