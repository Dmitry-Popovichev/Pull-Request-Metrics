#!/usr/bin/python3

"""
This script pulls GitHub Pull Request metrics from STFC Cloud repositories.
It uses the PyGithub library to interact with the GitHub API, 
retrieving a list of pull requests from specified repositories and filters
them accordingly.
"""

from github import Github
from github import Auth
from vars import stfc_repositiories
import os

def retrieve_list_of_prs(token: str, repo: str) -> list[object]:
    """
    A function that retrieves a list of pull requests from the given repository 
    using the provided GitHub token.

    :param token: A string containing a github token
    :param repo: A string containing the name of the repository
    :return: A list of pull requests from the given repository (github.PullRequest.PullRequest objects)
    :rtype: list
    """

    auth = Auth.Token(token)
    g = Github(auth=auth)
    
    list_of_prs = []
    list_of_prs = g.get_repo(repo).get_pulls(state="closed")
    return list_of_prs
    
def retrieve_all_merged(list_of_prs: list[object]) -> list[object]:
    """
    A simple function that retrieves all pull requests from the given repository and creates a new
    list, appending only the merged PRs. This turns the paginated list of PRs that is slow to iterate through 
    into a single list of merged PRs.

    :param list_of_prs: a list of PRs
    :return: A list of merged PRs
    :rtype: list
    """

    merged_prs = []

    for pr in list_of_prs:
        if pr.merged:
            merged_prs.append(pr)
            print(pr.number)
        elif pr.merged == None:
            print("PR has none value for merged field")

    print(f"Total merged PRs: {len(merged_prs)}")
    return merged_prs

if __name__ == "__main__":
    token = os.getenv("GITHUB_TOKEN")
    repos = stfc_repositiories

    if not token:
        raise RuntimeError("GITHUB_TOKEN environment variable not found.")
    
    for r in repos:
        list_of_prs = retrieve_list_of_prs(token=token, repo=r)
        retrieve_all_merged(list_of_prs)

