import sys
from unittest.mock import patch, MagicMock

from src import vars as src_vars

sys.modules.setdefault("vars", src_vars)

from src.main import retrieve_list_of_prs
from src.main import retrieve_all_merged_prs


@patch("src.main.Auth")
@patch("src.main.Github")
def test_retrieve_list_of_prs_function_returns_list(mock_github, _mock_auth):
    """
    Test that retrieve_list_of_prs returns a list of PR objects.
    """

    mock_github_instance = mock_github.return_value

    mock_repo = MagicMock()
    mock_pr = MagicMock()
    mock_pr.merged = True
    mock_repo.get_pulls.return_value = [mock_pr]

    mock_github_instance.get_repo.return_value = mock_repo

    result = retrieve_list_of_prs("mock_token", "mock_repo")

    assert isinstance(result, list), "Should return a list"
    assert len(result) == 1, "Should have exactly one PR"
    assert result[0] == mock_pr, "The PR should match the mock"


@patch("src.main.Auth")
@patch("src.main.Github")
def test_retrieve_list_of_prs_function_has_invalid_token_or_repo(
    mock_github, _mock_auth
):
    """
    Test that retrieve_list_of_prs raises an error if the token is invalid or the repo is incorrect.
    """
    mock_github_instance = mock_github.return_value
    mock_repo = MagicMock()
    mock_repo.get_pulls.side_effect = Exception("Bad credentials")
    mock_github_instance.get_repo.return_value = mock_repo

    try:
        retrieve_list_of_prs("invalid_token", "mock_repo")
    except RuntimeError as e:
        assert (
            str(e)
            == "Error retrieving pull requests, either the repo name or the token is incorrect: Bad credentials"
        ), "Should raise a RuntimeError with the correct message"
    else:
        assert False, "Should have raised a RuntimeError"


def test_retrieve_all_merged_function_returns_only_merged_prs():
    """
    Test that retrieve_all_merged returns only merged PRs.
    """

    mock_pr1 = MagicMock()
    mock_pr1.merged = True

    mock_pr2 = MagicMock()
    mock_pr2.merged = False

    mock_pr3 = MagicMock()
    mock_pr3.merged = None

    list_of_prs = [mock_pr1, mock_pr2, mock_pr3]

    result = retrieve_all_merged_prs(list_of_prs)

    assert isinstance(result, list), "Should return a list"
    assert len(result) == 1, "Should have exactly one merged PR"
    assert result[0] == mock_pr1, "The merged PR should match the mock"
