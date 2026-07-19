"""
Project: InsightX
Author: Lại Văn Sâm
Email: samvasang1192011@gmail.com
Date: July 2026
License: MIT
Description: Customizable GitHub repository analytics engine with high-precision data visualization.
"""

from typing import Any, Mapping
from pymongo import MongoClient
from config import Config
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from utils.logger import logger

try:
    client: MongoClient[Mapping[str, Any]] = MongoClient(
        Config.URI, timeoutMS=5000, serverSelectionTimeoutMS=5000
    )
    client.admin.command("ping")
    db = client[str(Config.DB_NAME)]
    logger.info("Successfully connected to MongoDB")
except ServerSelectionTimeoutError:
    logger.error("Error: Connection timed out (check your IP or permissions)")
except ConnectionFailure:
    logger.error("Error: Could not connect to the MongoDB server")
except Exception as e:
    logger.error(f"An unexpected error occurred: {e}")
