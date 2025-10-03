"""
Application configuration settings.
"""

from pydantic import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings."""
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    # Cerebrus API
    cerebrus_api_key: str
    cerebrus_base_url: str = "https://api.cerebrus.com"
    
    # OpenAI
    openai_api_key: str
    
    # Social Media APIs
    instagram_app_id: str
    instagram_app_secret: str
    instagram_access_token: str
    
    twitter_api_key: str
    twitter_api_secret: str
    twitter_access_token: str
    twitter_access_token_secret: str
    
    linkedin_client_id: str
    linkedin_client_secret: str
    linkedin_access_token: str
    
    # Database
    database_url: str = "sqlite:///./data/agent.db"
    redis_url: str = "redis://localhost:6379"
    
    # Storage
    storage_path: str = "./data"
    max_image_size: int = 10485760  # 10MB
    allowed_image_types: str = "jpg,jpeg,png,gif"
    
    # Scheduling
    default_post_time: str = "00:00"  # 12 AM
    timezone: str = "UTC"
    
    # Security
    secret_key: str
    encryption_key: str
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()