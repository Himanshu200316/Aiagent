"""
Application configuration settings
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """Application settings"""
    
    # API Keys
    openai_api_key: str
    instagram_access_token: Optional[str] = None
    instagram_app_id: Optional[str] = None
    instagram_app_secret: Optional[str] = None
    
    twitter_api_key: Optional[str] = None
    twitter_api_secret: Optional[str] = None
    twitter_access_token: Optional[str] = None
    twitter_access_token_secret: Optional[str] = None
    twitter_bearer_token: Optional[str] = None
    
    linkedin_client_id: Optional[str] = None
    linkedin_client_secret: Optional[str] = None
    linkedin_access_token: Optional[str] = None
    
    # Cerebrus API
    cerebrus_api_key: Optional[str] = None
    cerebrus_api_url: str = "https://api.cerebrus.com"
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str = "sqlite:///./data/social_media_agent.db"
    
    # Redis
    redis_url: str = "redis://redis:6379"
    
    # Scheduling
    default_post_time: str = "00:00"
    timezone: str = "UTC"
    
    # Image Generation
    stable_diffusion_model: str = "runwayml/stable-diffusion-v1-5"
    max_image_size: int = 1024
    image_quality: int = 95
    
    # File paths
    data_dir: str = "/app/data"
    images_dir: str = "/app/images"
    logs_dir: str = "/app/logs"
    prompts_dir: str = "/app/prompts"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create global settings instance
settings = Settings()