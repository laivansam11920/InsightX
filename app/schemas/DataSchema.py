from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict


class DataSchema(BaseModel):
    Starred_Repos: int = Field(..., ge=0)
    Stars_Earned: int = Field(..., ge=0)
    Contributed_to: int = Field(..., ge=0)
    Project_Earned: int = Field(..., ge=0)
    Pull_Requests: int = Field(..., ge=0)
    PR_Code_Changes: int = Field(..., ge=0)
    Issues: int = Field(..., ge=0)
    pushes: int = Field(..., ge=0)
    Time_Pushes: Dict[str, int] = Field(default_factory=dict)
    Issues_Comments: int = Field(..., ge=0)
    reviews: int = Field(..., ge=0)
    reviews_comments: int = Field(..., ge=0)
    Code_Reviews: int = Field(..., ge=0)
    created_at: datetime = Field(default_factory=datetime.now)
