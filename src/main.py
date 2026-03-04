#!/usr/bin/python3

"""
This script pulls GitHub Pull Request metrics from STFC Cloud repositories.
It uses the PyGithub library to interact with the GitHub API, 
retrieving a list of pull requests from specified repositories and filters
them accordingly.
"""

import os
from typing import List
from github import Github, Auth, PullRequest, PaginatedList
from github.PullRequest import PullRequest
from github.PaginatedList import PaginatedList
from vars import stfc_repositiories


def retrieve_list_of_prs(token: str, repo: str) -> PaginatedList[PullRequest]:
    """
    A function that retrieves a list of pull requests from the given repository
    using the provided GitHub token.

    :param token: A string containing a github token
    :param repo: A string containing the name of the repository
    :return: A list of pull requests from the given repository (github.PullRequest.PullRequest objects)
    """

    auth = Auth.Token(token)
    g = Github(auth=auth)
    list_of_prs = []

    try:
        list_of_prs = g.get_repo(repo).get_pulls(state="closed")
    except Exception as e:
        raise RuntimeError(
            f"Error retrieving pull requests, either the repo name or the token is incorrect: {e}"
        )
    return list_of_prs


def retrieve_all_merged_prs(
    list_of_prs: PaginatedList[PullRequest],
) -> List[PullRequest]:
    """
    A simple function that retrieves all pull requests from the given repository and creates a new
    list, appending only the merged PRs. This turns the paginated list of PRs that is slow to iterate through
    into a single list of merged PRs.

    :param list_of_prs: a paginated list of PRs (PaginatedList[PullRequest] objects)
    :return: A list of merged PRs
    """

    merged_prs = []

    for pr in list_of_prs:
        if pr.merged:
            merged_prs.append(pr)
            print(pr.number)  # Only here for testing purposes
        else:
            print(
                "PR has none value for merged field"
            )  # Only here for testing purposes

    print(f"Total merged PRs: {len(merged_prs)}")  # Only here for testing purposes
    return merged_prs


if __name__ == "__main__":
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        raise RuntimeError("GITHUB_TOKEN environment variable not found.")

    for repo in stfc_repositiories:
        list_of_prs = retrieve_list_of_prs(token=token, repo=repo)
        retrieve_all_merged_prs(list_of_prs)
