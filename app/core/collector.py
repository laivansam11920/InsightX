"""
Project: InsightX
Author: Lại Văn Sâm
Email: samvasang1192011@gmail.com
Date: July 2026
License: MIT
Description: Customizable GitHub repository analytics engine with high-precision data visualization.
"""
from fastapi_cloud_cli.commands.env import delete

from app.utils.github_client import get_client
from app.database.connect_db import db
from config import Config
from requests import post
from collections import defaultdict
from typing import Dict, Any
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from utils.logger import logger
from github.Repository import Repository
from utils.queries import CONTRIBUTION_CALENDAR_QUERY
from schemas.DataSchema import DataSchema


#TODO: Improve error handling by using specific exceptions instead of generic ones.


def get_reviews(repo, /) -> int:
    _C: int = 0

    try:

        pulls = repo.get_pulls(state="all")
        for pr in pulls:
            _C += len(list(pr.get_reviews()))
        return _C

    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return _C

def fetch_time_pushes_graphql(
    token: str, /, username: str
) -> tuple[dict[str, Any], int]:

    pushes_data: int = 0
    monthly_stats = defaultdict(int)

    try:
        url: str = Config.GITHUB_GRAPHQL_URL
        headers: dict[str, str] = {"Authorization": f"Bearer {token}"}

        json_data: dict[str, str] = {
            'query': CONTRIBUTION_CALENDAR_QUERY % username,
        }

        response = post(url, json=json_data, headers=headers, timeout=50)
        data = response.json()

        if "data" not in data or "user" not in data["data"]:
            print("Error from GitHub:", data, flush=True)
            return {}, 0

        weeks: list = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]

        for week in weeks:
            for day in week["contributionDays"]:
                # The date format is 'YYYY-MM-DD', so we take the first 7 characters to get 'YYYY-MM'
                month_key = day["date"][:7]
                monthly_stats[month_key] += day["contributionCount"]
                pushes_data += int(day["contributionCount"])

        return dict(monthly_stats), pushes_data
    except KeyError:
        logger.error(f"KeyError occurred")
        return {}, 0
    except TimeoutError:
        logger.error("Time out to connect Github")
        return {}, 0
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return {}, 0

#OPTIMIZE: Need to replace this function with a direct request query to improve performance
def gets_info_repo(repo) -> tuple[int] | tuple[Any, Any, Any, int, int, int, int, int]:
    """This function handles data retrieval for a specific repository."""
    if repo.size == 0:
        return *(0,) * 8,

    stars: int = repo.stargazers_count
    pulls: Any = repo.get_pulls(state="all")
    pulls_count: int = pulls.totalCount

    _add: int = 0
    _delete: int = 0

    for pr in pulls:
        try:
            files_changes = pr.get_files()
            for file in files_changes:
                _add += file.additions
                _delete += file.deletions
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")

    repo_fork = 1 if repo.fork else 0

    issues: Any = repo.get_issues(state="all")
    issues_count: int = issues.totalCount
    issues_comments: int = sum(issue.comments for issue in issues)

    sum_reviews: int = get_reviews(repo)

    return stars, pulls_count, issues_count, issues_comments, repo_fork, sum_reviews, _add, _delete

def get_github_stats() -> DataSchema | None:
    try:
        gh = get_client()
        user = gh.get_user(Config.NAME_GITHUB)
        repos = list(user.get_repos())

        #TODO: Proceed with developing the retrieval of remaining data for the schema.
        stats: dict[str, int | Dict[str, int]] = {
            "Starred_Repos": int(user.get_starred().totalCount),  #
            "Stars_Earned": 0,  #
            "Contributed_to": 0, #
            "Project_Earned": len(repos),  #
            "Pull_Requests": 0,  #
            "PR_Code_Changes": {
                "add": 0,
                "delete": 0
            },
            "Issues": 0,  #
            "pushes": 0,  #
            "Time_Pushes": {},  #
            "Issues_Comments": 0, #
            "reviews": 0, #
            "reviews_comments": 0, #
            "Code_Reviews": 0, #
        }

        with ThreadPoolExecutor(max_workers=10) as executor:

            future_pushes: Any = executor.submit(
                fetch_time_pushes_graphql, Config.TOKEN, Config.NAME_GITHUB
            )
            future_repos: dict[Any, Repository] = {
                executor.submit(gets_info_repo, repo): repo for repo in repos
            }

            for future in as_completed(future_repos):
                #HACK: The code is prone to crashing because it uses [] instead of .get(), and lacks specific exception handling for potential indexing errors.
                stars, pulls, issues_count, issues_comments, repo_fork, sum_reviews, add_changes, delete_changes = future.result()

                keys_mapping: list[tuple[str, int]] = [
                    ("Stars_Earned", stars),
                    ("Pull_Requests", pulls),
                    ("Issues", issues_count),
                    ("Issues_Comments", issues_comments),
                    ("Contributed_to", repo_fork),
                    ("reviews", sum_reviews),
                    ("reviews_comments", sum_reviews),
                    ("Code_Reviews", sum_reviews)
                ]

                for k, v in keys_mapping:
                    if k in stats:
                        stats[k] += v

                stats["PR_Code_Changes"]["add"] += add_changes #type: ignore
                stats["PR_Code_Changes"]["delete"] += delete_changes #type: ignore

            time_push, push_count = future_pushes.result()
            stats["Time_Pushes"] = time_push
            stats["pushes"] = push_count

        return DataSchema(**stats)

    except KeyError:
        #FIXME: Handling KeyError without addressing the root cause; may result in data inconsistencies.
        logger.error(f"KeyError occurred")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

logger.info(get_github_stats())

