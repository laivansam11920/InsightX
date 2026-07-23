from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

from .settings import *

__all__ = ["Config"]
