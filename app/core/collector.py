"""
Project: InsightX
Author: Lại Văn Sâm
Email: samvasang1192011@gmail.com
Date: July 2026
License: MIT
Description: Customizable GitHub repository analytics engine with high-precision data visualization.
"""
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
from abc import ABC


#TODO: Improve error handling by using specific exceptions instead of generic ones

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

        except KeyError:
            logger.error(f"KeyError occurred")
            return {}, 0
        except TimeoutError:
            logger.error("Time out to connect Github")
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
            except Exception as e:
                logger.error(f"An unexpected error occurred: {e}")

        repo_fork = 1 if repo.fork else 0

        issues: Any = repo.get_issues(state="all")
        issues_count: int = issues.totalCount
        issues_comments: int = sum(issue.comments for issue in issues)

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

            #TODO: Proceed with developing the retrieval of remaining data for the schema.
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

                stats["Time_Pushes"] = time_push
                stats["pushes"] = push_count

            return DataSchema(**stats)

        except KeyError:
            #FIXME: Handling KeyError without addressing the root cause; may result in data inconsistencies.
            logger.error(f"KeyError occurred")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")


class GitHubDatabaseManager(GitHubStatsCollector):
    def __init__(self):
        super().__init__()

    def update_db(self):
        try:
            collection_db = db[f"{Config.DB_COLLECTION}"]

            data = self.get_github_stats()

            if data is not None:
                data_dict = data.model_dump()
                result = collection_db.replace_one({"User": self.username}, data_dict, upsert=True)
                return f"success to save id {result.upserted_id}"
            else:
                return "data is None"
        except Exception as e:
            return f"An unexpected error occurred: {e}"

"""if __name__ == "__main__":
    a=GitHubDatabaseManager()
    logger.info(a.update_db())"""