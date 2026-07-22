from config import Config
from app.utils.github_client import get_client

gh = get_client()
user = gh.get_user(Config.NAME_GITHUB)

a = list(user.get_repos())

for repo in a:
    if repo.name == "CONFESSION":
        pulls = repo.get_pulls(state="all")

        for pr in pulls:
            print(f"Đang kiểm tra PR #{pr.number}: {pr.title}")
            reviews = pr.get_reviews()

            print(len(list(reviews)))
