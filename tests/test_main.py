import pytest
import sys
from unittest.mock import patch, MagicMock

from src import vars as src_vars
sys.modules.setdefault("vars", src_vars)

from src.main import retrieve_list_of_prs
from src.main import retrieve_all_merged

@patch("src.main.Auth")
@patch("src.main.Github")
def test_retrieve_list_of_prs_function_returns_list(mock_github, mock_auth):
    """
    Test that retrieve_list_of_prs returns a list of PR objects.
    """

    mock_auth_instance = mock_auth.return_value
    mock_github_instance = mock_github.return_value

    mock_repo = MagicMock()
    mock_pr = MagicMock()
    mock_pr.merged = True
    mock_repo.get_pulls.return_value = [mock_pr]

    mock_github_instance.get_repo.return_value = mock_repo

    result = retrieve_list_of_prs("mock_token", "mock_repo")

    assert isinstance(result, list), "Should return a list"
    assert len(result) == 1, "Should have exactly one PR"
    assert result[0] == mock_pr, "The PR should match our mock"


@patch("src.main.Auth")
@patch("src.main.Github")
def test_retrieve_all_merged_function_returns_only_merged_prs(mock_github, mock_auth):
    """
    Test that retrieve_all_merged returns only merged PRs.
    """

    mock_auth_instance = mock_auth.return_value
    mock_github_instance = mock_github.return_value

    mock_pr1 = MagicMock()
    mock_pr1.merged = True

    mock_pr2 = MagicMock()
    mock_pr2.merged = False

    mock_pr3 = MagicMock()
    mock_pr3.merged = None

    list_of_prs = [mock_pr1, mock_pr2, mock_pr3]

    result = retrieve_all_merged(list_of_prs)

    assert isinstance(result, list), "Should return a list"
    assert len(result) == 1, "Should have exactly one merged PR"
    assert result[0] == mock_pr1, "The merged PR should match our mock"