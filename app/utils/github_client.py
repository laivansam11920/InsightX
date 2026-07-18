"""
Project: InsightX
Author: Lại Văn Sâm
Email: samvasang1192011@gmail.com
Date: July 2026
License: MIT
Description: Customizable GitHub repository analytics engine with high-precision data visualization.
"""

from config.settings import Config
from github import Auth, Github, GithubException, RateLimitExceededException


def get_github_client() -> Github | None:
    try:
        tk: str = Config.token
        if not tk:
            raise ValueError("GITHUB_TOKEN not found in .env file!")
        auth = Auth.Token(tk)
        return Github(auth=auth, timeout=50)
    except RateLimitExceededException:
        print("You have exceeded the API rate limit!", flush=True)
    except GithubException as e:
        print(f"An error occurred: {e.status}, {e.data}.", flush=True)
    except Exception as e:
        print(f"An error occurred: {e}.", flush=True)


gh = get_github_client()
