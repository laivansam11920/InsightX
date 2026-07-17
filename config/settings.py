"""
Author: LaiVanSam
Copyright: LaiVansam
"""

from dotenv import find_dotenv, load_dotenv
from os import getenv
import sys

load_dotenv(find_dotenv(), override=True)


class Config:
    DB_NAME: str = getenv("DB_NAME", "TEST")
    DB_COLLECTION: str = getenv("DB_COLLECTION", "TEST_DB")
    uri: str = str(getenv("MONGO_URI"))
    token: str = str(getenv("GITHUB_TOKEN"))
    PORT: int = int(getenv("PORT", 2011))
    allow_population_by_field_name = True

    if not uri or not token:
        print("Error: MONGO_URI or GITHUB_TOKEN not found in .env file!")
        sys.exit(1)