#!/usr/bin/python3

'''
This script pulls GitHub Pull Request metrics from STFC Cloud repositories.
#NOTE# At the moment it's a placeholder script with some basic code
to test ansible playbooks.
'''

from github import Github
from github import Auth
import os

def retrieve_repo_names(token:str) -> list[str]:
    ''' 
    A simple function that retrieves all GitHub repositiores assocaited with the user, 
    using a personal GH token.
    :param token: a string containing a github token
    :return: A list of STFC Cloud repositories associated with the User token
    :rtype: List
    '''
    auth = Auth.Token(token)
    
    g = Github(auth=auth)
    repo_list = []

    for repo in g.get_user().get_repos():
        repo_list.append(repo.name)
        #print(f"The repo name is: {repo.name}\n")

    g.close()
    return repo_list

if __name__ == "__main__":
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("No token found in the environment")

    retrieve_repo_names(token=token)
    
