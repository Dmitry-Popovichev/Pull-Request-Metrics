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
from src.main import average_time_to_first_review
from src.main import main


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
    mock_pr1.created_at = datetime.strptime(
        "2026-03-24 15:02:03+00:00", "%Y-%m-%d %H:%M:%S%z"
    )
    mock_pr1.merged_at = datetime.strptime(
        "2026-03-24 15:08:30+00:00", "%Y-%m-%d %H:%M:%S%z"
    )

    list_of_prs = [mock_pr1]

    result = average_time_to_merge(list_of_prs, mock_repo_name)

    assert isinstance(result, float) and result > 0, "Should return a postive float"


def test_pr_datetime_has_None_value_and_skips_and_logs_warning(caplog):

    mock_repo_name = "The best repo ever"

    mock_pr1 = MagicMock()
    mock_pr1.number = 1
    mock_pr1.created_at = datetime.strptime(
        "2026-03-24 15:02:03+00:00", "%Y-%m-%d %H:%M:%S%z"
    )
    mock_pr1.merged_at = None

    list_of_prs = [mock_pr1]

    with caplog.at_level(logging.WARNING):
        result = average_time_to_merge(list_of_prs, mock_repo_name)

    assert len(caplog.records) == 1, "There should be 1 record of a warning"
    assert (
        "Skipping pr #1 in The best repo ever due to missing datestamps (created_at=2026-03-24 15:02:03+00:00, merged_at=None)"
        in caplog.text
    )
    assert result == 0


def test_if_difference_is_negative_then_function_should_log_an_error(caplog):

    mock_repo_name = "The best repo ever"

    mock_pr1 = MagicMock()
    mock_pr1.number = 1
    mock_pr1.created_at = datetime.strptime(
        "2026-03-24 15:08:30+00:00", "%Y-%m-%d %H:%M:%S%z"
    )
    mock_pr1.merged_at = datetime.strptime(
        "2026-03-24 15:02:03+00:00", "%Y-%m-%d %H:%M:%S%z"
    )

    list_of_prs = [mock_pr1]

    with caplog.at_level(logging.ERROR):
        result = average_time_to_merge(list_of_prs, mock_repo_name)

    assert len(caplog.records) == 1, "There should be 1 record of an error"
    assert (
        "Skipping pr #1 as it has produced a negative difference, -387.0 seconds"
        in caplog.text
    )
    assert result == 0


def test_when_datetime_has_missing_timezone_and_exception_is_thrown_with_error_logging(
    caplog,
):

    mock_repo_name = "The best repo ever"

    mock_pr1 = MagicMock()
    mock_pr1.number = 1
    mock_pr1.created_at = datetime.strptime(
        "2026-03-24 15:02:03+00:00", "%Y-%m-%d %H:%M:%S%z"
    )
    mock_pr1.merged_at = datetime.strptime("2026-03-24 15:08:30", "%Y-%m-%d %H:%M:%S")

    list_of_prs = [mock_pr1]

    with caplog.at_level(logging.ERROR):
        result = average_time_to_merge(list_of_prs, mock_repo_name)

    assert len(caplog.records) == 1
    assert "Something went wront when calculating difference" in caplog.text
    assert result == 0


def test_that_average_time_to_first_review_returns_a_positive_float():
    """
    Test the the function works as intended, returning a postive float.
    """

    mock_repo_name = "The best repo ever"

    mock_pr1 = MagicMock()
    mock_pr1.created_at = datetime.strptime(
        "2026-03-24 15:02:03+00:00", "%Y-%m-%d %H:%M:%S%z"
    )
    mock_pr1.number = 1

    mock_review = MagicMock()
    mock_review.submitted_at = datetime.strptime(
        "2026-03-30 10:11:14+00:00", "%Y-%m-%d %H:%M:%S%z"
    )
    mock_pr1.get_reviews.return_value = [mock_review]

    list_of_prs = [mock_pr1]

    result = average_time_to_first_review(list_of_prs, mock_repo_name)

    assert isinstance(result, float) and result > 0, "Should return a postive float"


def test_no_reviews_were_found_and_logging_info_messages_are_captured(caplog):
    """
    Test that no reviews were found in a PR and that the logging info message is
    captured.
    """

    mock_repo_name = "The best repo ever"

    mock_pr1 = MagicMock()
    mock_pr1.created_at = datetime.strptime(
        "2026-03-24 15:02:03+00:00", "%Y-%m-%d %H:%M:%S%z"
    )
    mock_pr1.number = 1
    mock_pr1.get_reviews.return_value = []

    list_of_prs = [mock_pr1]
    with caplog.at_level(logging.INFO):
        result = average_time_to_first_review(list_of_prs, mock_repo_name)

    assert len(caplog.records) == 3
    assert "No reviews were found in PR #1" in caplog.text
    assert "The best repo ever has 0 PRs or 0 reviews in any of the PRs" in caplog.text
    assert "Skipped PRs: 1" in caplog.text
    assert result == 0


def test_one_review_object_has_a_valid_date_and_one_has_None_value_and_logging_info_messages_are_captured(
    caplog,
):
    """
    Test that one review is good but one review has a None value a PR and that the logging info message is
    captured.
    """

    mock_repo_name = "The best repo ever"

    mock_pr1 = MagicMock()
    mock_pr1.created_at = datetime.strptime(
        "2026-03-24 15:02:03+00:00", "%Y-%m-%d %H:%M:%S%z"
    )
    mock_pr1.number = 1

    mock_review_1 = MagicMock()
    mock_review_1.submitted_at = datetime.strptime(
        "2026-03-30 10:11:14+00:00", "%Y-%m-%d %H:%M:%S%z"
    )
    mock_review_2 = None
    mock_pr1.get_reviews.return_value = [mock_review_1, mock_review_2]

    list_of_prs = [mock_pr1]
    with caplog.at_level(logging.INFO):
        result = average_time_to_first_review(list_of_prs, mock_repo_name)

    assert len(caplog.records) == 2
    assert (
        "The average time to first review in The best repo ever is 500951.0 seconds"
        in caplog.text
    )
    assert "Skipped PRs: 0" in caplog.text
    assert result == 500951.0


def test_submitted_at_date_is_None_and_logging_messages_are_captured(caplog):
    """
    Test that one review has a submitted date but has returned as none, increasing the skipping
    value and logging the error
    """

    mock_repo_name = "The best repo ever"

    mock_pr1 = MagicMock()
    mock_pr1.created_at = datetime.strptime(
        "2026-03-24 15:02:03+00:00", "%Y-%m-%d %H:%M:%S%z"
    )
    mock_pr1.number = 1

    mock_review_1 = MagicMock()
    mock_review_1.submitted_at = ""

    mock_pr1.get_reviews.return_value = [mock_review_1]

    list_of_prs = [mock_pr1]
    with caplog.at_level(logging.INFO):
        result = average_time_to_first_review(list_of_prs, mock_repo_name)

    assert len(caplog.records) == 3
    assert "The best repo ever has 0 PRs or 0 reviews in any of the PRs" in caplog.text
    assert "Skipped PRs: 1" in caplog.text
    assert result == 0


def test_that_time_to_review_is_negative_and_logging_messages_are_captured(caplog):
    """
    Test that time to review is negative and logging messages are captured.
    """

    mock_repo_name = "The best repo ever"

    mock_pr1 = MagicMock()
    mock_pr1.created_at = datetime.strptime(
        "2026-03-24 15:02:03+00:00", "%Y-%m-%d %H:%M:%S%z"
    )
    mock_pr1.number = 1

    mock_review_1 = MagicMock()
    mock_review_1.submitted_at = datetime.strptime(
        "2026-02-20 10:11:14+00:00", "%Y-%m-%d %H:%M:%S%z"
    )

    mock_pr1.get_reviews.return_value = [mock_review_1]

    list_of_prs = [mock_pr1]

    list_of_prs = [mock_pr1]
    with caplog.at_level(logging.INFO):
        result = average_time_to_first_review(list_of_prs, mock_repo_name)

    assert len(caplog.records) == 3
    assert (
        "Skipping pr #1 as it has produced a negative difference, -2782249.0 seconds"
        in caplog.text
    )


def test_Exception_is_raised_after_difference_calculation_fails(caplog):
    """
    Test that the exception is raised when the calculation fails due to miss matching datetime
    formats.
    """

    mock_repo_name = "The best repo ever"

    mock_pr1 = MagicMock()
    mock_pr1.created_at = datetime.strptime(
        "2026-03-24 15:02:03+00:00", "%Y-%m-%d %H:%M:%S%z"
    )
    mock_pr1.number = 1

    mock_review_1 = MagicMock()
    mock_review_1.submitted_at = datetime.strptime(
        "2026-02-20 10:11:14", "%Y-%m-%d %H:%M:%S"
    )

    mock_pr1.get_reviews.return_value = [mock_review_1]

    list_of_prs = [mock_pr1]

    list_of_prs = [mock_pr1]
    with caplog.at_level(logging.INFO):
        result = average_time_to_first_review(list_of_prs, mock_repo_name)

    assert len(caplog.records) == 3
    assert "Something went wront when calculating difference:" in caplog.text
    assert "The best repo ever has 0 PRs or 0 reviews in any of the PRs"
    assert "Skipped PRs: 1" in caplog.text
    assert result == 0


@patch("src.main.logging.getLogger")
@patch("src.main.os.getenv", return_value=None)
def test_main_accepts_log_level_choices_and_config_exists(
    _mock_getenv, mock_get_logger
):
    """
    Test that valid --log values are accepted by the parser configuration.
    """

    for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        with patch("sys.argv", ["prog", "--log", level]):
            with pytest.raises(RuntimeError):
                main()

    assert mock_get_logger.return_value.setLevel.call_count == 5


@patch("src.main.logging.getLogger")
@patch("src.main.os.getenv", return_value=None)
def test_main_maps_parsed_log_level_to_set_level(_mock_getenv, mock_get_logger):
    """
    Test that --log value maps to logging.<LEVEL> in setLevel.
    """

    with patch("sys.argv", ["prog", "--log", "INFO"]):
        with pytest.raises(RuntimeError) as exc:
            main()

    assert str(exc.value) == "GITHUB_TOKEN environment variable not found."
    mock_get_logger.return_value.setLevel.assert_called_once_with(logging.INFO)
