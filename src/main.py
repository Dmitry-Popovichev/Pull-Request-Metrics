from github import Github
from github import Auth
import os

token = os.getenv("GITHUB_TOKEN")

if not token:
    print("No token found")

auth = Auth.Token(token)

g = Github(auth=auth)

g = Github(base_url="https://github.com/stfc/cloud-image-builders/api/v3", auth=auth)

for repo in g.get_user().get_repos():
    print(repo.name)

g.close()
