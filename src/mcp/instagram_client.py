"""
Instagram MCP client for posting content.
"""

import httpx
import json
from typing import Dict, Any, Optional
from src.models.schemas import GeneratedContent, PostType

class InstagramClient:
    """Instagram API client using MCP."""
    
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v18.0"
    
    async def test_connection(self, credentials: Dict[str, Any]) -> bool:
        """Test Instagram API connection."""
        try:
            access_token = credentials.get("access_token")
            if not access_token:
                return False
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/me",
                    params={"access_token": access_token}
                )
                return response.status_code == 200
                
        except Exception:
            return False
    
    async def post_content(self, content: GeneratedContent, credentials: Dict[str, Any], post_type: PostType) -> Dict[str, Any]:
        """Post content to Instagram."""
        try:
            access_token = credentials.get("access_token")
            if not access_token:
                return {"success": False, "error": "No access token provided"}
            
            if post_type == PostType.FEED:
                return await self._post_to_feed(content, access_token)
            elif post_type == PostType.STORY:
                return await self._post_to_story(content, access_token)
            else:
                return {"success": False, "error": "Unsupported post type"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _post_to_feed(self, content: GeneratedContent, access_token: str) -> Dict[str, Any]:
        """Post to Instagram feed."""
        try:
            # Step 1: Create media container
            container_data = {
                "image_url": content.image_url,
                "caption": content.caption,
                "access_token": access_token
            }
            
            async with httpx.AsyncClient() as client:
                # Create media container
                container_response = await client.post(
                    f"{self.base_url}/me/media",
                    data=container_data
                )
                
                if container_response.status_code != 200:
                    return {"success": False, "error": "Failed to create media container"}
                
                container_id = container_response.json()["id"]
                
                # Step 2: Publish the media
                publish_data = {
                    "creation_id": container_id,
                    "access_token": access_token
                }
                
                publish_response = await client.post(
                    f"{self.base_url}/me/media_publish",
                    data=publish_data
                )
                
                if publish_response.status_code == 200:
                    return {
                        "success": True,
                        "post_id": publish_response.json()["id"],
                        "platform": "instagram"
                    }
                else:
                    return {"success": False, "error": "Failed to publish media"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _post_to_story(self, content: GeneratedContent, access_token: str) -> Dict[str, Any]:
        """Post to Instagram story."""
        try:
            # Instagram Stories API implementation
            story_data = {
                "image_url": content.image_url,
                "access_token": access_token
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/me/media",
                    data=story_data
                )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "post_id": response.json()["id"],
                        "platform": "instagram_story"
                    }
                else:
                    return {"success": False, "error": "Failed to post story"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}