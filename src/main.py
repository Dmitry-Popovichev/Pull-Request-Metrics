#!/usr/bin/python3

"""
This script pulls GitHub Pull Request metrics from STFC Cloud repositories.
It uses the PyGithub library to interact with the GitHub API,
retrieving a list of pull requests from specified repositories and filters
them accordingly.
"""

import os
import logging
import argparse
import time
from typing import List
from github import Github, Auth, PullRequest, PaginatedList
from github.PullRequest import PullRequest
from github.PaginatedList import PaginatedList
from prometheus_client import start_http_server, Gauge
from vars import stfc_repositiories

# Configure a safe default; CLI overrides are applied in main().
logging.basicConfig(
    format="%(asctime)s %(levelname)-8s %(message)s",
    level=logging.WARNING,
    datefmt="%d-%m-%Y %H:%M:%S",
)

# Defining a Prometheus Gauge to track the total number of merged PRs per repository.
merged_pr_total_gauge = Gauge(
    name="github_merged_prs_total",
    documentation="Total number of merged pull requests",
    labelnames=["repository"],
)
# Defining a Prometheus Gauge to track the average time to merge PRs within a repository.
average_time_to_merge_pr_gauge = Gauge(
    name="average_time_to_merge_pr",
    documentation="The average time to merge a pull request from creation",
    labelnames=["repository"],
)
# Defining a Prometheus Gauge to track the average time to firs review within a repository.
average_time_to_first_review_gauge = Gauge(
    name="average_time_to_first_review",
    documentation="The average time to the first review within a repository",
    labelnames=["repository"],
)


def retrieve_list_of_prs(token: str, repo: str) -> PaginatedList[PullRequest]:
    """
    A function that retrieves a paginated list of pull requests from the given repository
    using the provided GitHub token.

    :param token: A string containing a github token.
    :param repo: A string containing the name of the repository.
    :return: A paginated list of pull requests from the given repository.
    """

    auth = Auth.Token(token)
    g = Github(auth=auth)
    list_of_prs = []

    try:
        list_of_prs = g.get_repo(repo).get_pulls(state="closed")
    except Exception as e:
        raise RuntimeError(
            f"Error retrieving pull requests, either the repo name or the token is incorrect: {e}"
        ) from e

    logging.debug("Retrieved %s pull requests from %s", type(list_of_prs), repo)
    return list_of_prs


def retrieve_all_merged_prs(
    list_of_prs: PaginatedList[PullRequest],
) -> List[PullRequest]:
    """
    A simple function that retrieves all pull requests from the given repository and creates a new
    list, appending only the merged PRs. This turns the paginated list of PRs that is slow to
    iterate through into a simple list of merged PRs.

    :param list_of_prs: a paginated list of PRs.
    :return: A list of merged PRs.
    """

    merged_prs = []
    logging.info("The exporter is collecting pull requests, please wait...")

    for pr in list_of_prs:
        if pr.merged:
            merged_prs.append(pr)
            logging.debug(pr.number)
        else:
            logging.debug("PR has none value for merged field")

    logging.info("Total merged PRs: %s", len(merged_prs))
    return merged_prs


def average_time_to_merge(merged_prs: List[PullRequest], repo: str) -> float:
    """
    This function uses the merged_prs list and calculates the average time from PR creation to
    merge using the simple list generated earlier.

    :param merged_prs: A list of merged PRs.
    :param repo: A string containing the repository name.
    :return: Average time to merge float per repository in seconds
    """

    skipped_prs = 0
    avg_time_to_merge = 0
    time_to_merge_list = []

    for pr in merged_prs:
        pr_number = getattr(pr, "number", "unknown")
        created_at = getattr(pr, "created_at", None)
        merged_at = getattr(pr, "merged_at", None)

        if created_at is None or merged_at is None:
            skipped_prs += 1
            logging.warning(
                "Skipping pr #%s in %s due to missing datestamps (created_at=%s, merged_at=%s)",
                pr_number,
                repo,
                created_at,
                merged_at,
            )
        else:
            try:
                difference = merged_at - created_at
                time_in_seconds = difference.total_seconds()
                if time_in_seconds < 0:
                    skipped_prs += 1
                    logging.error(
                        "Skipping pr #%s as it has produced a negative difference, %s seconds",
                        pr_number,
                        time_in_seconds,
                    )
                    continue
                time_to_merge_list.append(time_in_seconds)

            except Exception as e:
                skipped_prs += 1
                logging.error("Something went wront when calculating difference: %s", e)

    if len(time_to_merge_list) == 0:
        logging.info("%s has 0 PRs", repo)
    else:
        avg_time_to_merge = sum(time_to_merge_list) / len(time_to_merge_list)
        logging.info(
            "The average time to merge a PR in %s is %s seconds",
            repo,
            avg_time_to_merge,
        )
        logging.info("Skipped PRs: %s", skipped_prs)

    return avg_time_to_merge


def average_time_to_first_review(merged_prs: List[PullRequest], repo: str):
    """
    This function gets the average time from PR creation to the first review using the
    "get_reviews" method. This produces another paginated list which we have to iterate
    through. The funtion is slow especially when it goes through repos with a large amount
    of PRs.

    :param merged_prs: A list of merged PRs.
    :param repo: A string containing the repository name.
    :return: Average time to first review float per repository in seconds.
    """

    avg_time_to_first_review = 0.0
    first_review_date = None
    skipped_prs = 0
    reviews = []
    time_to_first_review_list = []

    for pr in merged_prs:
        created_at = getattr(pr, "created_at", None)
        pr_number = getattr(pr, "number", "unknown")

        reviews = list(pr.get_reviews())
        if not reviews or not reviews[0].submitted_at:
            logging.info("No reviews were found in PR #%s", pr_number)
            skipped_prs += 1
            continue
        first_review_date = reviews[0].submitted_at

        try:
            difference = first_review_date - created_at
            time_in_seconds = difference.total_seconds()
            if time_in_seconds < 0:
                skipped_prs += 1
                logging.info(
                    "Skipping pr #%s as it has produced a negative difference, %s seconds",
                    pr_number,
                    time_in_seconds,
                )
                continue

            time_to_first_review_list.append(time_in_seconds)

        except Exception as e:
            skipped_prs += 1
            logging.error("Something went wront when calculating difference: %s", e)

    if len(time_to_first_review_list) == 0:
        logging.info("%s has 0 PRs or 0 reviews in any of the PRs", repo)
    else:
        avg_time_to_first_review = sum(time_to_first_review_list) / len(
            time_to_first_review_list
        )
        logging.info(
            "The average time to first review in %s is %s seconds",
            repo,
            avg_time_to_first_review,
        )
    logging.info("Skipped PRs: %s", skipped_prs)

    return avg_time_to_first_review


def main() -> None:
    """
    Arguments parser sits here as it was interfering with command flags in the terminal
    when it was in the main body of the script. Allows for log-level command flags.

    The main function of the script that retrieves the GitHub token from the environment,
    starts the Prometheus HTTP server, and continuously retrieves pull request data from the
    specified repositories. Lastly, it sleeps for an hour before repeating the process.
    """

    parser = argparse.ArgumentParser(
        description="Set the logging level via command line"
    )
    parser.add_argument(
        "--log",
        "--log-level",
        dest="log_level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="WARNING",
        help="Set the logging level",
    )
    args, _unknown = parser.parse_known_args()
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN environment variable not found.")

    start_http_server(8081)

    while True:

        for repo in stfc_repositiories:
            # Initial API call to retrieve and simplify list of Pull Requests in the repo.
            # Also total merged prs metric is here.
            list_of_prs = retrieve_list_of_prs(token=token, repo=repo)
            merged_prs_list = retrieve_all_merged_prs(list_of_prs)

            # Metric calculations (there will be more)
            avereage_time_to_first_review_per_repo = average_time_to_first_review(
                merged_prs_list, repo=repo
            )
            average_time_to_merge_pr_per_repo = average_time_to_merge(
                merged_prs_list, repo=repo
            )

            # Prometheus gauge post to http server
            merged_pr_total_gauge.labels(repository=repo).set(len(merged_prs_list))
            average_time_to_merge_pr_gauge.labels(repository=repo).set(
                average_time_to_merge_pr_per_repo
            )
            average_time_to_first_review_gauge.labels(repository=repo).set(
                avereage_time_to_first_review_per_repo
            )

        # Sleep for 1 hour
        time.sleep(3600)


if __name__ == "__main__":
    main()
