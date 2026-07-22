"""
Project: InsightX
Author: Lại Văn Sâm
Email: samvasang1192011@gmail.com
Date: July 2026
License: MIT
Description: Customizable GitHub repository analytics engine with high-precision data visualization.
"""

# 1. Standard Library
from abc import ABC
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict

# 2. Third-party Libraries
from github import GithubException, RateLimitExceededException
from github.Repository import Repository
from pymongo.errors import ConnectionFailure, PyMongoError
from requests import post
from requests.exceptions import RequestException

# 3. Local Modules
from config import Config
from app.database.connect_db import db
from app.utils.github_client import get_client
from schemas.DataSchema import DataSchema
from utils.logger import logger
from utils.queries import CONTRIBUTION_CALENDAR_QUERY

class BaseGitHubCollector(ABC):
    def __init__(self):
        self.token = Config.TOKEN
        self.username = Config.NAME_GITHUB
        self.github_client = get_client()
        self.url = Config.GITHUB_GRAPHQL_URL


class GraphQLStatsCollector(BaseGitHubCollector):
    def __init__(self):
        super().__init__()

    def fetch_time_pushes_graphql(self) -> tuple[dict[str, Any], int]:
        pushes_data: int = 0
        monthly_stats = defaultdict(int)

        try:
            url: str = self.url
            headers: dict[str, str] = {"Authorization": f"Bearer {self.token}"}
            json_data: dict[str, str] = {
                'query': CONTRIBUTION_CALENDAR_QUERY % self.username,
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

        except (KeyError, TypeError) as e:
            logger.error(f"Data parsing error due to unexpected structure: {e}")
            return {}, 0
        except RequestException as e:
            logger.error(f"Network request failed: {e}")
            return {}, 0
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return {}, 0


class RestStatsCollector(BaseGitHubCollector):
    def __init__(self):
        super().__init__()

    @staticmethod
    def _get_reviews(repo: Repository, /) -> int:
        reviews_count: int = 0

        try:
            pulls = repo.get_pulls(state="all")
            for pr in pulls:
                reviews_count += len(list(pr.get_reviews()))
            return reviews_count
        except RateLimitExceededException:
            logger.error("GitHub API rate limit exceeded while fetching reviews.")
            return reviews_count
        except GithubException as e:
            logger.error(f"GitHub API error [{e.status}]: {e.data}")
            return reviews_count
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return  reviews_count

    def gets_info_repo(self, repo) -> tuple:
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
            except GithubException as e:
                logger.error(f"GitHub error while fetching PR files: {e.data}")
            except AttributeError as e:
                logger.error(f"Attribute error while processing file changes: {e}")

        repo_fork = 1 if repo.fork else 0

        try:
            issues: Any = repo.get_issues(state="all")
            issues_count: int = issues.totalCount
            issues_comments: int = sum(issue.comments for issue in issues)
        except GithubException as e:
            logger.error(f"Failed to fetch issues for repo {repo.name}: {e.data}")
            issues_count, issues_comments = 0, 0

        sum_reviews: int = self._get_reviews(repo)

        return stars, pulls_count, issues_count, issues_comments, repo_fork, sum_reviews, _add, _delete


class GitHubStatsCollector(BaseGitHubCollector):
    def __init__(self):
        super().__init__()
        self.rest_collector = RestStatsCollector()
        self.graphql_collector = GraphQLStatsCollector()

    def get_github_stats(self) -> DataSchema | None:
        try:
            gh = self.github_client
            user = gh.get_user(self.username)
            repos = list(user.get_repos())

            stats: dict[str, int | Dict[str, int]] = {
                "Starred_Repos": int(user.get_starred().totalCount),
                "Stars_Earned": 0,
                "Contributed_to": 0,
                "Project_Earned": len(repos),
                "Pull_Requests": 0,
                "PR_Code_Changes": {
                    "add": 0,
                    "delete": 0
                },
                "Issues": 0,
                "pushes": 0,
                "Time_Pushes": {},
                "Issues_Comments": 0,
                "reviews": 0,
                "reviews_comments": 0,
                "Code_Reviews": 0,
            }

            with ThreadPoolExecutor(max_workers=10) as executor:

                future_pushes: Any = executor.submit(self.graphql_collector.fetch_time_pushes_graphql)
                future_repos: dict[Any, Repository] = {
                    executor.submit(self.rest_collector.gets_info_repo, repo): repo for repo in repos
                }
                time_push, push_count = future_pushes.result()
                for future in as_completed(future_repos):

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

                stats["Time_Pushes"] = time_push
                stats["pushes"] = push_count

            return DataSchema(**stats)

        except RateLimitExceededException:
            logger.error("GitHub API rate limit exceeded globally during stats collection.")
        except GithubException as e:
            logger.error(f"GitHub API error occurred: {e.status} - {e.data}")
        except (KeyError, TypeError) as e:
            logger.error(f"Mapping or data structure error in statistics aggregation: {e}")


class GitHubDatabaseManager(GitHubStatsCollector):
    def __init__(self):
        super().__init__()

    def update_db(self) -> str | None:
        try:
            collection_db = db[Config.DB_COLLECTION]

            data = self.get_github_stats()

            if data is not None:
                data_dict = data.model_dump()
                doc_id = data_dict.pop("id", 0)
                collection_db.replace_one({"User": self.username}, data_dict, upsert=True)
                logger.info(f"success to save id {doc_id}")
            else:
                logger.error("Data is None")
        except ConnectionFailure:
            logger.critical("Database connection lost. Verify network settings or server availability")
        except PyMongoError as e:
            logger.error(f"An unexpected error occurred: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    a=GitHubDatabaseManager()
    a.update_db()