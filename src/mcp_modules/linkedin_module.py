"""
LinkedIn MCP Module
"""

import logging
from typing import Dict, Any, Optional, List
import requests
from datetime import datetime
import json

from .base_module import BaseSocialMediaModule, PostResult, MediaItem

logger = logging.getLogger(__name__)

class LinkedInModule(BaseSocialMediaModule):
    """LinkedIn posting module using LinkedIn API"""
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__(credentials)
        self.access_token = credentials.get('access_token')
        self.person_id = None
        self.authenticated = False
        self.base_url = "https://api.linkedin.com/v2"
        
    async def authenticate(self) -> bool:
        """Authenticate with LinkedIn API"""
        try:
            if not self.access_token:
                logger.error("LinkedIn access token missing")
                return False
            
            # Test authentication by getting profile info
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f"{self.base_url}/me",
                headers=headers
            )
            
            if response.status_code == 200:
                profile_data = response.json()
                self.person_id = profile_data['id']
                self.authenticated = True
                logger.info(f"Successfully authenticated with LinkedIn")
                return True
            else:
                logger.error(f"LinkedIn authentication failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"LinkedIn authentication failed: {e}")
            return False
    
    async def post_content(self, content: str, media: Optional[List[MediaItem]] = None) -> PostResult:
        """Post content to LinkedIn"""
        try:
            if not self.authenticated:
                auth_result = await self.authenticate()
                if not auth_result:
                    return PostResult(
                        success=False,
                        error_message="Authentication failed"
                    )
            
            await self.rate_limiter.wait_if_needed('posts')
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Prepare post data
            post_data = {
                "author": f"urn:li:person:{self.person_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": content
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            # Handle media if provided
            if media and len(media) > 0:
                media_item = media[0]  # LinkedIn supports one image per post
                
                if media_item.media_type == 'image':
                    # Upload image first
                    image_urn = await self._upload_image(media_item.file_path)
                    if image_urn:
                        post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
                        post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                            {
                                "status": "READY",
                                "description": {
                                    "text": media_item.alt_text or ""
                                },
                                "media": image_urn,
                                "title": {
                                    "text": "Generated Advertisement"
                                }
                            }
                        ]
            
            # Post to LinkedIn
            response = requests.post(
                f"{self.base_url}/ugcPosts",
                headers=headers,
                json=post_data
            )
            
            if response.status_code == 201:
                post_id = response.headers.get('x-restli-id')
                post_url = f"https://www.linkedin.com/feed/update/{post_id}/"
                
                return PostResult(
                    success=True,
                    platform_post_id=post_id,
                    post_url=post_url,
                    posted_at=datetime.now()
                )
            else:
                logger.error(f"LinkedIn posting failed: {response.status_code} - {response.text}")
                return PostResult(
                    success=False,
                    error_message=f"HTTP {response.status_code}: {response.text}"
                )
            
        except Exception as e:
            logger.error(f"LinkedIn posting failed: {e}")
            return PostResult(
                success=False,
                error_message=str(e)
            )
    
    async def _upload_image(self, image_path: str) -> Optional[str]:
        """Upload image to LinkedIn and return asset URN"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Register upload
            register_data = {
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner": f"urn:li:person:{self.person_id}",
                    "serviceRelationships": [
                        {
                            "relationshipType": "OWNER",
                            "identifier": "urn:li:userGeneratedContent"
                        }
                    ]
                }
            }
            
            response = requests.post(
                f"{self.base_url}/assets?action=registerUpload",
                headers=headers,
                json=register_data
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to register upload: {response.text}")
                return None
            
            upload_data = response.json()
            upload_url = upload_data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
            asset_urn = upload_data['value']['asset']
            
            # Upload image
            with open(image_path, 'rb') as image_file:
                upload_response = requests.put(
                    upload_url,
                    data=image_file,
                    headers={'Authorization': f'Bearer {self.access_token}'}
                )
            
            if upload_response.status_code == 201:
                return asset_urn
            else:
                logger.error(f"Failed to upload image: {upload_response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Image upload failed: {e}")
            return None
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get LinkedIn account information"""
        try:
            if not self.authenticated:
                auth_result = await self.authenticate()
                if not auth_result:
                    return {"error": "Authentication failed"}
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Get profile info
            response = requests.get(
                f"{self.base_url}/me?projection=(id,firstName,lastName,headline,profilePicture(displayImage~:playableStreams))",
                headers=headers
            )
            
            if response.status_code == 200:
                profile_data = response.json()
                
                return {
                    "platform": "linkedin",
                    "id": profile_data.get('id'),
                    "first_name": profile_data.get('firstName', {}).get('localized', {}).get('en_US'),
                    "last_name": profile_data.get('lastName', {}).get('localized', {}).get('en_US'),
                    "headline": profile_data.get('headline', {}).get('localized', {}).get('en_US')
                }
            else:
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            logger.error(f"Failed to get LinkedIn account info: {e}")
            return {"error": str(e)}