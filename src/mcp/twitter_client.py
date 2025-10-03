"""
Twitter (X) MCP client for posting content.
"""

import httpx
import json
import base64
from typing import Dict, Any, Optional
from src.models.schemas import GeneratedContent, PostType

class TwitterClient:
    """Twitter API client using MCP."""
    
    def __init__(self):
        self.base_url = "https://api.twitter.com/2"
        self.upload_url = "https://upload.twitter.com/1.1"
    
    async def test_connection(self, credentials: Dict[str, Any]) -> bool:
        """Test Twitter API connection."""
        try:
            bearer_token = credentials.get("bearer_token")
            if not bearer_token:
                return False
            
            headers = {"Authorization": f"Bearer {bearer_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/users/me",
                    headers=headers
                )
                return response.status_code == 200
                
        except Exception:
            return False
    
    async def post_content(self, content: GeneratedContent, credentials: Dict[str, Any], post_type: PostType) -> Dict[str, Any]:
        """Post content to Twitter."""
        try:
            bearer_token = credentials.get("bearer_token")
            if not bearer_token:
                return {"success": False, "error": "No bearer token provided"}
            
            # Twitter only supports feed posts (tweets)
            if post_type != PostType.FEED:
                return {"success": False, "error": "Twitter only supports feed posts"}
            
            return await self._post_tweet(content, bearer_token)
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _post_tweet(self, content: GeneratedContent, bearer_token: str) -> Dict[str, Any]:
        """Post a tweet with optional media."""
        try:
            headers = {"Authorization": f"Bearer {bearer_token}"}
            
            tweet_data = {
                "text": content.caption
            }
            
            # If there's an image, upload it first
            if content.image_url:
                media_id = await self._upload_media(content.image_url, bearer_token)
                if media_id:
                    tweet_data["media"] = {"media_ids": [media_id]}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/tweets",
                    headers=headers,
                    json=tweet_data
                )
                
                if response.status_code == 201:
                    return {
                        "success": True,
                        "post_id": response.json()["data"]["id"],
                        "platform": "twitter"
                    }
                else:
                    return {"success": False, "error": f"Failed to post tweet: {response.text}"}
                    
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _upload_media(self, image_url: str, bearer_token: str) -> Optional[str]:
        """Upload media to Twitter."""
        try:
            # Download image
            async with httpx.AsyncClient() as client:
                image_response = await client.get(image_url)
                image_data = image_response.content
            
            # Upload to Twitter
            headers = {"Authorization": f"Bearer {bearer_token}"}
            
            files = {"media": image_data}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.upload_url}/media/upload",
                    headers=headers,
                    files=files
                )
                
                if response.status_code == 200:
                    return response.json()["media_id_string"]
                else:
                    return None
                    
        except Exception as e:
            print(f"Error uploading media to Twitter: {e}")
            return None