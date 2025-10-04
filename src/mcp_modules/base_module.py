"""
Base MCP module for social media platforms
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class PostResult:
    """Result of a social media post"""
    success: bool
    platform_post_id: Optional[str] = None
    post_url: Optional[str] = None
    error_message: Optional[str] = None
    posted_at: Optional[datetime] = None

@dataclass
class MediaItem:
    """Media item for posting"""
    file_path: str
    media_type: str  # 'image', 'video'
    caption: Optional[str] = None
    alt_text: Optional[str] = None

class BaseSocialMediaModule(ABC):
    """Base class for social media platform modules"""
    
    def __init__(self, credentials: Dict[str, Any]):
        self.credentials = credentials
        self.platform_name = self.__class__.__name__.lower().replace('module', '')
        self.rate_limiter = RateLimiter(self.platform_name)
        
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the platform"""
        pass
    
    @abstractmethod
    async def post_content(self, content: str, media: Optional[List[MediaItem]] = None) -> PostResult:
        """Post content to the platform"""
        pass
    
    @abstractmethod
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if the module is healthy"""
        try:
            auth_result = await self.authenticate()
            return {
                "platform": self.platform_name,
                "authenticated": auth_result,
                "status": "healthy" if auth_result else "authentication_failed"
            }
        except Exception as e:
            logger.error(f"Health check failed for {self.platform_name}: {e}")
            return {
                "platform": self.platform_name,
                "authenticated": False,
                "status": "error",
                "error": str(e)
            }

class RateLimiter:
    """Simple rate limiter for API calls"""
    
    def __init__(self, platform: str):
        self.platform = platform
        self.requests = []
        self.limits = {
            'instagram': {'posts_per_hour': 5, 'stories_per_hour': 10},
            'twitter': {'tweets_per_hour': 50},
            'linkedin': {'posts_per_hour': 10}
        }
    
    async def wait_if_needed(self, action_type: str = 'posts'):
        """Wait if rate limit would be exceeded"""
        current_time = datetime.now()
        limit_key = f"{action_type}_per_hour"
        
        if self.platform not in self.limits:
            return
            
        platform_limits = self.limits[self.platform]
        if limit_key not in platform_limits:
            return
            
        limit = platform_limits[limit_key]
        
        # Remove requests older than 1 hour
        self.requests = [req for req in self.requests if (current_time - req).seconds < 3600]
        
        if len(self.requests) >= limit:
            # Calculate wait time
            oldest_request = min(self.requests)
            wait_time = 3600 - (current_time - oldest_request).seconds
            if wait_time > 0:
                logger.info(f"Rate limit reached for {self.platform}. Waiting {wait_time} seconds.")
                await asyncio.sleep(wait_time)
        
        self.requests.append(current_time)