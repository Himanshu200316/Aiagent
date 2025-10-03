"""
LinkedIn MCP client for posting content.
"""

import httpx
import json
from typing import Dict, Any, Optional
from src.models.schemas import GeneratedContent, PostType

class LinkedInClient:
    """LinkedIn API client using MCP."""
    
    def __init__(self):
        self.base_url = "https://api.linkedin.com/v2"
    
    async def test_connection(self, credentials: Dict[str, Any]) -> bool:
        """Test LinkedIn API connection."""
        try:
            access_token = credentials.get("access_token")
            if not access_token:
                return False
            
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/people/~",
                    headers=headers
                )
                return response.status_code == 200
                
        except Exception:
            return False
    
    async def post_content(self, content: GeneratedContent, credentials: Dict[str, Any], post_type: PostType) -> Dict[str, Any]:
        """Post content to LinkedIn."""
        try:
            access_token = credentials.get("access_token")
            if not access_token:
                return {"success": False, "error": "No access token provided"}
            
            # LinkedIn only supports feed posts
            if post_type != PostType.FEED:
                return {"success": False, "error": "LinkedIn only supports feed posts"}
            
            return await self._post_to_feed(content, access_token)
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _post_to_feed(self, content: GeneratedContent, access_token: str) -> Dict[str, Any]:
        """Post to LinkedIn feed."""
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # LinkedIn post data structure
            post_data = {
                "author": "urn:li:person:YOUR_PERSON_URN",  # This needs to be dynamically set
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": content.caption
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            # If there's an image, add it to the post
            if content.image_url:
                # Upload image first
                image_urn = await self._upload_image(content.image_url, access_token)
                if image_urn:
                    post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["shareMediaCategory"] = "IMAGE"
                    post_data["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = [
                        {
                            "status": "READY",
                            "description": {
                                "text": content.caption
                            },
                            "media": image_urn,
                            "title": {
                                "text": "Advertisement"
                            }
                        }
                    ]
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/ugcPosts",
                    headers=headers,
                    json=post_data
                )
                
                if response.status_code == 201:
                    return {
                        "success": True,
                        "post_id": response.json()["id"],
                        "platform": "linkedin"
                    }
                else:
                    return {"success": False, "error": f"Failed to post to LinkedIn: {response.text}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _upload_image(self, image_url: str, access_token: str) -> Optional[str]:
        """Upload image to LinkedIn."""
        try:
            # Download image
            async with httpx.AsyncClient() as client:
                image_response = await client.get(image_url)
                image_data = image_response.content
            
            # Upload to LinkedIn
            headers = {"Authorization": f"Bearer {access_token}"}
            
            files = {"file": image_data}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/assets?action=registerUpload",
                    headers=headers,
                    files=files
                )
                
                if response.status_code == 201:
                    return response.json()["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
                else:
                    return None
                    
        except Exception as e:
            print(f"Error uploading image to LinkedIn: {e}")
            return None