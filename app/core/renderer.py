
# 1. Standard Library
# 2. Third-party Libraries
# 3. Local Modules
from .collector import GitHubDatabaseManager
from app.database.connect_db import db


class RenderImg(GitHubDatabaseManager):
    def __init__(self):
        super().__init__()

    def render(self) -> None: ...

__all__ = ["RenderImg"]