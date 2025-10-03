from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any


class CredentialsIn(BaseModel):
    platform: Literal["instagram", "twitter", "linkedin"]
    data: Dict[str, Any]


class AdRequest(BaseModel):
    user_id: str
    product_description: str
    tone: str = Field(default="persuasive")
    target_audience: str
    generate_image: bool = True
    use_uploaded_image: Optional[str] = None  # image_id in storage
    platforms: List[Literal["instagram", "twitter", "linkedin"]] = Field(default_factory=lambda: ["instagram", "twitter", "linkedin"])
    instagram_post_type: Literal["feed", "story"] = "feed"


class ScheduleRequest(BaseModel):
    user_id: str
    hour: int = 0
    minute: int = 0
    timezone: str = "UTC"


class CerebrusMessage(BaseModel):
    user_id: str
    message: str
    payload: Optional[Dict[str, Any]] = None


class GeneratedAd(BaseModel):
    caption: str
    image_path: str
    prompt_key: str
