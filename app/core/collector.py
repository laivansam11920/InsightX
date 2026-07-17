"""
Author: LaiVanSam
Copyright: LaiVansam
"""

from app.utils.github_client import gh
from app.database.connect_db import db
from config.settings import Config
from requests import post
from collections import defaultdict
from typing import Dict
from concurrent.futures import ThreadPoolExecutor
from time import time
import functools


def do_thoi_gian(func):
    @functools.wraps(func)  # Dòng này giữ lại tên và thông tin của hàm gốc
    def wrapper(*args, **kwargs):
        bat_dau = time()
        ket_qua = func(*args, **kwargs)

        ket_thuc = time()
        print(f"Hàm '{func.__name__}' chạy mất: {ket_thuc - bat_dau:.4f} giây")
        return ket_qua

    return wrapper


def fetch_time_pushes_graphql(token: str, username: str) -> Dict[str, int]:
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
            return {}

        monthly_stats = defaultdict(int)
        weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"][
            "weeks"
        ]

        for week in weeks:
            for day in week["contributionDays"]:
                # The date format is 'YYYY-MM-DD', so we take the first 7 characters to get 'YYYY-MM'
                month_key = day["date"][:7]
                monthly_stats[month_key] += day["contributionCount"]
        return dict(monthly_stats)
    except Exception as e:
        print(f"{e}", flush=True)
        return {}


def lay_thong_tin_mot_repo(repo):
    """This function handles data retrieval for a specific repository."""
    if repo.size == 0:
        return 0, 0, 0

    stars = repo.stargazers_count
    pulls = repo.get_pulls(state="all").totalCount
    issues = repo.get_issues(state="all").totalCount
    return stars, pulls, issues


def get_github_stats() -> dict[str, int | dict[str, int]] | None:
    try:
        user = gh.get_user(Config.name_gh)
        repos = list(user.get_repos())
        print(repos)
        stats: Dict[str, int | Dict[str, int]] = {
            "Starred_Repos": int(user.get_starred().totalCount),
            "Stars_Earned": 0,
            "Contributed_to": 0,
            "Project_Earned": len(repos),
            "Pull_Requests": 0,
            "PR_Code_Changes": 0,
            "Issues": 0,
            "pushes": 0,
            "Time_Pushes": {},
            "Issues_Comments": 0,
            "reviews": 0,
            "reviews_comments": 0,
            "Code_Reviews": 0,
        }
        with ThreadPoolExecutor(max_workers=10) as executor:

            future_pushes = executor.submit(
                fetch_time_pushes_graphql, Config.token, Config.name_gh
            )
            future_repos = {
                executor.submit(lay_thong_tin_mot_repo, repo): repo for repo in repos
            }

            for future in future_repos:
                stars, pulls, issues = future.result()
                stats["Stars_Earned"] += stars
                stats["Pull_Requests"] += pulls
                stats["Issues"] += issues
            stats["Time_Pushes"] = future_pushes.result()
        return stats
    except Exception as e:
        print(f"{e}", flush=True)
