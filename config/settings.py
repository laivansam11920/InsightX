"""
Project: InsightX
Author: Lại Văn Sâm
Email: samvasang1192011@gmail.com
Date: July 2026
License: MIT
Description: Customizable GitHub repository analytics engine with high-precision data visualization.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Database setting
    DB_NAME: str = Field(default="InsightX", alias="DB_NAME")
    DB_COLLECTION: str = Field(default="EXAMPLE_DB", alias="DB_COLLECTION")
    URI: str = Field(alias="MONGO_URI")
    GITHUB_GRAPHQL_URL: str = "https://api.github.com/graphql"

    # GitHub setting
    TOKEN: str = Field(alias="GITHUB_TOKEN")
    NAME_GITHUB: str = Field(alias="NAME_GITHUB")

    # Flask setting
    PORT: int = Field(default=2011, alias="PORT")
    DEBUG: bool = Field(default=False, alias="DEBUG")
    TEST: bool = Field(default=False, alias="TEST")
    model_config = SettingsConfigDict(populate_by_name=True)

Config = Settings()