from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Dict
from config import Config
import uuid

class DataSchema(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    User: str = Config.NAME_GITHUB
    Starred_Repos: int = Field(..., ge=0)
    Stars_Earned: int = Field(..., ge=0)
    Contributed_to: int = Field(..., ge=0)
    Project_Earned: int = Field(..., ge=0)
    Pull_Requests: int = Field(..., ge=0)
    PR_Code_Changes: Dict[str, int] = Field(default_factory=dict)
    Issues: int = Field(..., ge=0)
    pushes: int = Field(..., ge=0)
    Time_Pushes: Dict[str, int] = Field(default_factory=dict)
    Issues_Comments: int = Field(..., ge=0)
    reviews: int = Field(..., ge=0)
    reviews_comments: int = Field(..., ge=0)
    Code_Reviews: int = Field(..., ge=0)
    created_at: datetime = Field(default_factory=datetime.now)