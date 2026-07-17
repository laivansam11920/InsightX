"""
Author: LaiVanSam
Copyright: LaiVansam
"""

from dotenv import find_dotenv, load_dotenv
from os import  getenv

load_dotenv(find_dotenv(), override=True)


class Config:
    DB_NAME: str = "TEST"
    DB_COLLECTION: str = "TEST_DB"
    uri: str = str(getenv("MONGO_URI"))
    token: str = str(getenv("GITHUB_TOKEN"))
    PORT: int = int(getenv("PORT", 2011))