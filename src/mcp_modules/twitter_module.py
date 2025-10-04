"""
Twitter/X MCP Module
"""

import logging
from typing import Dict, Any, Optional, List
import tweepy
from datetime import datetime

from .base_module import BaseSocialMediaModule, PostResult, MediaItem

logger = logging.getLogger(__name__)

class TwitterModule(BaseSocialMediaModule):
    """Twitter/X posting module using tweepy"""
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__(credentials)
        self.api = None
        self.client = None
        self.authenticated = False
        
    async def authenticate(self) -> bool:
        """Authenticate with Twitter API"""
        try:
            api_key = self.credentials.get('api_key')
            api_secret = self.credentials.get('api_secret')
            access_token = self.credentials.get('access_token')
            access_token_secret = self.credentials.get('access_token_secret')
            bearer_token = self.credentials.get('bearer_token')
            
            if not all([api_key, api_secret, access_token, access_token_secret]):
                logger.error("Twitter credentials missing")
                return False
            
            # Initialize API v1.1 for media upload
            auth = tweepy.OAuthHandler(api_key, api_secret)
            auth.set_access_token(access_token, access_token_secret)
            self.api = tweepy.API(auth, wait_on_rate_limit=True)
            
            # Initialize API v2 for posting
            self.client = tweepy.Client(
                bearer_token=bearer_token,
                consumer_key=api_key,
                consumer_secret=api_secret,
                access_token=access_token,
                access_token_secret=access_token_secret,
                wait_on_rate_limit=True
            )
            
            # Test authentication
            user = self.client.get_me()
            if user.data:
                self.authenticated = True
                logger.info(f"Successfully authenticated with Twitter as @{user.data.username}")
                return True
            else:
                logger.error("Twitter authentication failed - no user data")
                return False
                
        except Exception as e:
            logger.error(f"Twitter authentication failed: {e}")
            return False
    
    async def post_content(self, content: str, media: Optional[List[MediaItem]] = None) -> PostResult:
        """Post content to Twitter"""
        try:
            if not self.authenticated:
                auth_result = await self.authenticate()
                if not auth_result:
                    return PostResult(
                        success=False,
                        error_message="Authentication failed"
                    )
            
            await self.rate_limiter.wait_if_needed('tweets')
            
            media_ids = []
            if media and len(media) > 0:
                # Upload media (Twitter supports up to 4 images)
                for media_item in media[:4]:
                    if media_item.media_type == 'image':
                        media_upload = self.api.media_upload(media_item.file_path)
                        media_ids.append(media_upload.media_id)
                        
                        # Add alt text if provided
                        if media_item.alt_text:
                            self.api.create_media_metadata(
                                media_upload.media_id,
                                alt_text=media_item.alt_text
                            )
            
            # Post tweet
            if media_ids:
                response = self.client.create_tweet(
                    text=content,
                    media_ids=media_ids
                )
            else:
                response = self.client.create_tweet(text=content)
            
            if response.data:
                tweet_id = response.data['id']
                # Get username for URL construction
                user = self.client.get_me()
                username = user.data.username
                post_url = f"https://twitter.com/{username}/status/{tweet_id}"
                
                return PostResult(
                    success=True,
                    platform_post_id=tweet_id,
                    post_url=post_url,
                    posted_at=datetime.now()
                )
            else:
                return PostResult(
                    success=False,
                    error_message="Failed to create tweet - no response data"
                )
            
        except Exception as e:
            logger.error(f"Twitter posting failed: {e}")
            return PostResult(
                success=False,
                error_message=str(e)
            )
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get Twitter account information"""
        try:
            if not self.authenticated:
                auth_result = await self.authenticate()
                if not auth_result:
                    return {"error": "Authentication failed"}
            
            user = self.client.get_me(
                user_fields=['public_metrics', 'verified', 'description', 'location']
            )
            
            if user.data:
                return {
                    "platform": "twitter",
                    "username": user.data.username,
                    "name": user.data.name,
                    "description": user.data.description,
                    "location": user.data.location,
                    "follower_count": user.data.public_metrics['followers_count'],
                    "following_count": user.data.public_metrics['following_count'],
                    "tweet_count": user.data.public_metrics['tweet_count'],
                    "is_verified": user.data.verified
                }
            else:
                return {"error": "No user data available"}
                
        except Exception as e:
            logger.error(f"Failed to get Twitter account info: {e}")
            return {"error": str(e)}