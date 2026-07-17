"""
Author: LaiVanSam
Copyright: LaiVansam
"""

from typing import Any, Mapping
from pymongo import MongoClient
from config.settings import Config
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

try:
    client: MongoClient[Mapping[str, Any]] = MongoClient(Config.uri, timeoutMS=5000, serverSelectionTimeoutMS=5000)
    client.admin.command('ping')
    db = client[str(Config.DB_NAME)]
    print("Successfully connected to MongoDB")
except ServerSelectionTimeoutError:
    print("Error: Connection timed out (check your IP or permissions)", flush=True)
except ConnectionFailure:
    print("Error: Could not connect to the MongoDB server", flush=True)
except Exception as e:
    print(f"An unexpected error occurred: {e}", flush=True)
