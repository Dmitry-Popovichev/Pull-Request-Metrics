import pytest
import sys
from unittest.mock import patch, MagicMock

from datetime import datetime
import logging
from src import vars as src_vars

sys.modules.setdefault("vars", src_vars)

from src.main import retrieve_list_of_prs
from src.main import retrieve_all_merged_prs
from src.main import average_time_to_merge


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

    with pytest.raises(RuntimeError) as e:
        retrieve_list_of_prs("invalid_token", "mock_repo")
        print(e.value)
        assert (
            str(e.value)
            == "Error retrieving pull requests, either the repo name or the token is incorrect."
        )


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


def test_average_time_to_merge_returns_a_positive_float():

    mock_repo_name = "The best repo ever"

    mock_pr1 = MagicMock()
    mock_pr1.created_at = datetime.strptime("2026-03-24 15:02:03+00:00", '%Y-%m-%d %H:%M:%S%z')
    mock_pr1.merged_at = datetime.strptime("2026-03-24 15:08:30+00:00", '%Y-%m-%d %H:%M:%S%z')

    list_of_prs = [mock_pr1]

    result = average_time_to_merge(list_of_prs, mock_repo_name)

    assert isinstance(result, float) and result > 0, "Should return a postive float"


def test_pr_datetime_has_None_value_and_skips_and_logs_warning(caplog):
    
    mock_repo_name = "The best repo ever"

    mock_pr1 = MagicMock()
    mock_pr1.number = 1
    mock_pr1.created_at = datetime.strptime("2026-03-24 15:02:03+00:00", '%Y-%m-%d %H:%M:%S%z')
    mock_pr1.merged_at = None

    list_of_prs = [mock_pr1]

    with caplog.at_level(logging.WARNING):
        result = average_time_to_merge(list_of_prs, mock_repo_name)

    assert len(caplog.records) == 1, "There should be 1 record of a warning"
    assert "Skipping pr #1 in The best repo ever due to missing datestamps (created_at=2026-03-24 15:02:03+00:00, merged_at=None)" in caplog.text
    assert result == 0

def test_if_difference_is_negative_then_function_should_log_an_error(caplog):

    mock_repo_name = "The best repo ever"

    mock_pr1 = MagicMock()
    mock_pr1.number = 1
    mock_pr1.created_at = datetime.strptime("2026-03-24 15:08:30+00:00", '%Y-%m-%d %H:%M:%S%z')
    mock_pr1.merged_at = datetime.strptime("2026-03-24 15:02:03+00:00", '%Y-%m-%d %H:%M:%S%z')

    list_of_prs = [mock_pr1]

    with caplog.at_level(logging.ERROR):
        result = average_time_to_merge(list_of_prs, mock_repo_name)

    assert len(caplog.records) == 1, "There should be 1 record of an error"
    assert "Skipping pr #1 as it has produced a negative difference, -387.0 seconds" in caplog.text
    assert result == 0


def test_when_datetime_has_missing_timezone_and_exception_is_thrown_with_error_logging(caplog):

    mock_repo_name = "The best repo ever"

    mock_pr1 = MagicMock()
    mock_pr1.number = 1
    mock_pr1.created_at = datetime.strptime("2026-03-24 15:02:03+00:00", '%Y-%m-%d %H:%M:%S%z')
    mock_pr1.merged_at = datetime.strptime("2026-03-24 15:08:30", '%Y-%m-%d %H:%M:%S')

    list_of_prs = [mock_pr1]

    with caplog.at_level(logging.ERROR):
        result = average_time_to_merge(list_of_prs, mock_repo_name)

    assert len(caplog.records) == 1
    assert "Something went wront when calculating difference" in caplog.text
    assert result == 0