from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    # General
    app_name: str = "ad-agent"
    data_dir: str = "data"
    encryption_key: Optional[str] = Field(default=None, description="Base64 Fernet key used to encrypt credentials")

    # Default schedule
    default_post_hour: int = 0  # 12 AM
    default_post_minute: int = 0
    default_timezone: str = "UTC"

    # Providers
    openai_api_key: Optional[str] = None
    stability_api_key: Optional[str] = None

    # Posting modes
    instagram_api_mode: str = Field(default="instagrapi", description="instagrapi or graph")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()