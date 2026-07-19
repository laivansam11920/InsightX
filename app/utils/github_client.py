"""
Project: InsightX
Author: Lại Văn Sâm
Email: samvasang1192011@gmail.com
Date: July 2026
License: MIT
Description: Customizable GitHub repository analytics engine with high-precision data visualization.
"""

from config import Config
from github import Auth, Github, GithubException, RateLimitExceededException
from utils.logger import logger

def get_github_client() -> Github | None:
    try:
        tk: str = Config.TOKEN
        if not tk:
            raise ValueError("GITHUB_TOKEN not found in .env file!")
        auth = Auth.Token(tk)
        return Github(auth=auth, timeout=50)
    except RateLimitExceededException:
        logger.error("You have exceeded the API rate limit!")
    except GithubException as e:
        logger.error(f"An error occurred: {e.status}, {e.data}.", flush=True)
    except Exception as e:
        logger.error(f"An error occurred: {e}.", flush=True)

_client: Github | None = None

def get_client():
    global _client
    if _client is None:
        _client = get_github_client()
    return _client