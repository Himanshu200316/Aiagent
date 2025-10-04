"""
Instagram MCP Module
"""

import logging
from typing import Dict, Any, Optional, List
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, PleaseWaitFewMinutes

from .base_module import BaseSocialMediaModule, PostResult, MediaItem

logger = logging.getLogger(__name__)

class InstagramModule(BaseSocialMediaModule):
    """Instagram posting module using instagrapi"""
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__(credentials)
        self.client = Client()
        self.authenticated = False
        
    async def authenticate(self) -> bool:
        """Authenticate with Instagram"""
        try:
            username = self.credentials.get('username')
            password = self.credentials.get('password')
            
            if not username or not password:
                logger.error("Instagram credentials missing")
                return False
            
            # Try to login
            self.client.login(username, password)
            self.authenticated = True
            logger.info(f"Successfully authenticated with Instagram as {username}")
            return True
            
        except LoginRequired as e:
            logger.error(f"Instagram login required: {e}")
            return False
        except PleaseWaitFewMinutes as e:
            logger.error(f"Instagram rate limited: {e}")
            return False
        except Exception as e:
            logger.error(f"Instagram authentication failed: {e}")
            return False
    
    async def post_content(self, content: str, media: Optional[List[MediaItem]] = None) -> PostResult:
        """Post content to Instagram feed"""
        try:
            if not self.authenticated:
                auth_result = await self.authenticate()
                if not auth_result:
                    return PostResult(
                        success=False,
                        error_message="Authentication failed"
                    )
            
            await self.rate_limiter.wait_if_needed('posts')
            
            if media and len(media) > 0:
                # Post with media
                media_item = media[0]  # Instagram supports one image per post for now
                
                if media_item.media_type == 'image':
                    media_pk = self.client.photo_upload(
                        path=media_item.file_path,
                        caption=content
                    )
                else:
                    return PostResult(
                        success=False,
                        error_message="Video posting not implemented yet"
                    )
            else:
                # Text-only post (not supported by Instagram API directly)
                return PostResult(
                    success=False,
                    error_message="Instagram requires media for posts"
                )
            
            # Get post URL
            post_info = self.client.media_info(media_pk)
            post_url = f"https://www.instagram.com/p/{post_info.code}/"
            
            return PostResult(
                success=True,
                platform_post_id=str(media_pk),
                post_url=post_url
            )
            
        except Exception as e:
            logger.error(f"Instagram posting failed: {e}")
            return PostResult(
                success=False,
                error_message=str(e)
            )
    
    async def post_story(self, media: MediaItem, content: Optional[str] = None) -> PostResult:
        """Post content to Instagram story"""
        try:
            if not self.authenticated:
                auth_result = await self.authenticate()
                if not auth_result:
                    return PostResult(
                        success=False,
                        error_message="Authentication failed"
                    )
            
            await self.rate_limiter.wait_if_needed('stories')
            
            if media.media_type == 'image':
                story_pk = self.client.photo_upload_to_story(
                    path=media.file_path,
                    caption=content or ""
                )
            else:
                return PostResult(
                    success=False,
                    error_message="Video stories not implemented yet"
                )
            
            return PostResult(
                success=True,
                platform_post_id=str(story_pk)
            )
            
        except Exception as e:
            logger.error(f"Instagram story posting failed: {e}")
            return PostResult(
                success=False,
                error_message=str(e)
            )
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get Instagram account information"""
        try:
            if not self.authenticated:
                auth_result = await self.authenticate()
                if not auth_result:
                    return {"error": "Authentication failed"}
            
            user_info = self.client.user_info_by_username(self.credentials['username'])
            
            return {
                "platform": "instagram",
                "username": user_info.username,
                "full_name": user_info.full_name,
                "follower_count": user_info.follower_count,
                "following_count": user_info.following_count,
                "media_count": user_info.media_count,
                "is_verified": user_info.is_verified,
                "is_business": user_info.is_business
            }
            
        except Exception as e:
            logger.error(f"Failed to get Instagram account info: {e}")
            return {"error": str(e)}