"""
Project: InsightX
Author: Lại Văn Sâm
Email: samvasang1192011@gmail.com
Date: July 2026
License: MIT
Description: Customizable GitHub repository analytics engine with high-precision data visualization.
"""

from dotenv import find_dotenv, load_dotenv
from os import getenv
import sys

load_dotenv(find_dotenv(), override=True)


class Config:
    # Database setting
    DB_NAME: str = str(getenv("DB_NAME", "TEST"))
    DB_COLLECTION: str = str(getenv("DB_COLLECTION", "TEST_DB"))
    uri: str = str(getenv("MONGO_URI"))

    # GitHub setting
    token: str = str(getenv("GITHUB_TOKEN"))
    name_gh: str = str(getenv("NAME_GITHUB"))

    # Flask setting
    PORT: int = int(getenv("PORT", 2011))
    allow_population_by_field_name = True

    if not uri or not token or not name_gh:
        print(
            "Error: MONGO_URI or GITHUB_TOKEN or NAME_GITHUB not found in .env file!",
            flush=True,
        )
        sys.exit(1)
