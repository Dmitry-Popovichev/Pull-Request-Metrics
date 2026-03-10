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

# Set up logging to allow for command based log level configuration
parser = argparse.ArgumentParser(description="Set the logging level via command line")
parser.add_argument(
    "--log-level",
    choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    default="WARNING",
    help="Set the logging level",
)
args = parser.parse_args()
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',
    level=getattr(logging, args.log_level),
    datefmt='%d-%m-%Y %H:%M:%S'
    )

# Defining a Prometheus Gauge to track the total number of merged PRs per repository
merged_pr_total = Gauge(
    name="github_merged_prs_total",
    documentation="Total number of merged pull requests",
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


def main() -> None:
    """
    The main function of the script that retrieves the GitHub token from the environment,
    starts the Prometheus HTTP server, and continuously retrieves pull request data from the
    specified repositories. Lastly, it sleeps for an hour before repeating the process.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN environment variable not found.")

    start_http_server(8081)

    while True:

        for repo in stfc_repositiories:
            list_of_prs = retrieve_list_of_prs(token=token, repo=repo)
            merged_prs_list = retrieve_all_merged_prs(list_of_prs)
            merged_pr_total.labels(repository=repo).set(len(merged_prs_list))

        time.sleep(3600)


if __name__ == "__main__":
    main()
