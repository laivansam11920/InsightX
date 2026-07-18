"""
Project: InsightX
Author: Lại Văn Sâm
Email: samvasang1192011@gmail.com
Date: July 2026
License: MIT
Description: Customizable GitHub repository analytics engine with high-precision data visualization.
"""

from app.utils.github_client import gh
from app.database.connect_db import db
from config.settings import Config
from requests import post
from collections import defaultdict
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor


def fetch_time_pushes_graphql(token: str, /, username: str) -> tuple[dict[str, Any], int]:
    try:
        url = "https://api.github.com/graphql"
        headers = {"Authorization": f"Bearer {token}"}
        query = """
        {
          user(login: "%s") {
            contributionsCollection {
              contributionCalendar {
                weeks {
                  contributionDays {
                    date
                    contributionCount
                  }
                }
              }
            }
          }
        }
        """ % username

        response = post(url, json={"query": query}, headers=headers, timeout=50)
        data = response.json()

        if "data" not in data or "user" not in data["data"]:
            print("Error from GitHub:", data, flush=True)
            return {}, 0

        monthly_stats = defaultdict(int)
        weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"][
            "weeks"
        ]
        pushes_data: int = 0
        for week in weeks:
            for day in week["contributionDays"]:
                # The date format is 'YYYY-MM-DD', so we take the first 7 characters to get 'YYYY-MM'
                month_key = day["date"][:7]
                monthly_stats[month_key] += day["contributionCount"]
                pushes_data += int(day["contributionCount"])

        return dict(monthly_stats), pushes_data
    except Exception as e:
        print(f"An unexpected error occurred: {e}", flush=True)
        return {}, 0


def gets_info_repo(repo):
    """This function handles data retrieval for a specific repository."""
    if repo.size == 0:
        return 0, 0, 0, 0

    stars = repo.stargazers_count
    pulls = repo.get_pulls(state="all").totalCount
    issues = repo.get_issues(state="all").totalCount
    repo_fork = 1 if repo.fork else 0

    return stars, pulls, issues, repo_fork


def get_github_stats() -> dict[str, int | dict[str, int]] | None:
    try:
        user = gh.get_user(Config.name_gh)
        repos = list(user.get_repos())

        stats: Dict[str, int | Dict[str, int]] = {
            "Starred_Repos": int(user.get_starred().totalCount),  #
            "Stars_Earned": 0,  #
            "Contributed_to": 0,
            "Project_Earned": len(repos),  #
            "Pull_Requests": 0,  #
            "PR_Code_Changes": 0,
            "Issues": 0,  #
            "pushes": 0,  #
            "Time_Pushes": {},  #
            "Issues_Comments": 0,
            "reviews": 0,
            "reviews_comments": 0,
            "Code_Reviews": 0,
        }
        with ThreadPoolExecutor(max_workers=10) as executor:

            future_pushes: Any = executor.submit(
                fetch_time_pushes_graphql, Config.token, Config.name_gh
            )
            future_repos = {
                executor.submit(gets_info_repo, repo): repo for repo in repos
            }

            for future in future_repos:
                stars, pulls, issues, repo_fork = future.result()
                stats["Stars_Earned"] += stars
                stats["Pull_Requests"] += pulls
                stats["Issues"] += issues
                stats["Contributed_to"] += repo_fork
            time_push, push_count = future_pushes.result()
            stats["Time_Pushes"] = time_push
            stats["pushes"] = push_count
        return stats
    except Exception as e:
        print(f"An unexpected error occurred: {e}", flush=True)

