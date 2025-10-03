"""
Social Media Manager using MCP modules for Instagram, Twitter, and LinkedIn.
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

from src.models.schemas import Platform, GeneratedContent, PostType
from src.mcp.instagram_client import InstagramClient
from src.mcp.twitter_client import TwitterClient
from src.mcp.linkedin_client import LinkedInClient

class SocialMediaManager:
    """Manages posting to different social media platforms."""
    
    def __init__(self):
        self.clients = {
            Platform.INSTAGRAM: InstagramClient(),
            Platform.TWITTER: TwitterClient(),
            Platform.LINKEDIN: LinkedInClient()
        }
        self.credentials_path = "./data/credentials"
        os.makedirs(self.credentials_path, exist_ok=True)
    
    async def store_credentials(self, platform: Platform, credentials: Dict[str, Any], user_id: Optional[str] = None) -> bool:
        """Store credentials for a social media platform."""
        try:
            # Encrypt credentials before storing
            encrypted_credentials = self._encrypt_credentials(credentials)
            
            filename = f"{self.credentials_path}/{platform.value}_credentials.json"
            if user_id:
                filename = f"{self.credentials_path}/{platform.value}_{user_id}_credentials.json"
            
            with open(filename, "w") as f:
                json.dump({
                    "platform": platform.value,
                    "credentials": encrypted_credentials,
                    "user_id": user_id,
                    "stored_at": datetime.now().isoformat()
                }, f)
            
            # Test the credentials
            return await self._test_credentials(platform, credentials)
            
        except Exception as e:
            print(f"Error storing credentials for {platform}: {e}")
            return False
    
    async def _test_credentials(self, platform: Platform, credentials: Dict[str, Any]) -> bool:
        """Test if credentials are valid."""
        try:
            client = self.clients[platform]
            return await client.test_connection(credentials)
        except Exception as e:
            print(f"Error testing credentials for {platform}: {e}")
            return False
    
    async def post_content(self, platform: Platform, content: GeneratedContent, post_type: PostType) -> Dict[str, Any]:
        """Post content to a specific platform."""
        try:
            # Load credentials
            credentials = await self._load_credentials(platform)
            if not credentials:
                return {"success": False, "error": "No credentials found"}
            
            # Get platform client
            client = self.clients[platform]
            
            # Post content
            result = await client.post_content(content, credentials, post_type)
            
            # Log the post
            await self._log_post(platform, content, result)
            
            return result
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _load_credentials(self, platform: Platform) -> Optional[Dict[str, Any]]:
        """Load credentials for a platform."""
        try:
            filename = f"{self.credentials_path}/{platform.value}_credentials.json"
            
            if not os.path.exists(filename):
                return None
            
            with open(filename, "r") as f:
                data = json.load(f)
                return self._decrypt_credentials(data["credentials"])
                
        except Exception as e:
            print(f"Error loading credentials for {platform}: {e}")
            return None
    
    def _encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypt credentials for storage."""
        # Simple base64 encoding for now - implement proper encryption in production
        import base64
        return base64.b64encode(json.dumps(credentials).encode()).decode()
    
    def _decrypt_credentials(self, encrypted_credentials: str) -> Dict[str, Any]:
        """Decrypt credentials from storage."""
        import base64
        return json.loads(base64.b64decode(encrypted_credentials.encode()).decode())
    
    async def _log_post(self, platform: Platform, content: GeneratedContent, result: Dict[str, Any]):
        """Log posting activity."""
        log_entry = {
            "platform": platform.value,
            "timestamp": datetime.now().isoformat(),
            "content_id": id(content),
            "success": result.get("success", False),
            "post_id": result.get("post_id"),
            "error": result.get("error")
        }
        
        log_path = "./data/logs"
        os.makedirs(log_path, exist_ok=True)
        
        log_file = f"{log_path}/posting_log.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    async def get_posting_stats(self) -> Dict[str, Any]:
        """Get posting statistics."""
        stats = {
            "total_posts": 0,
            "successful_posts": 0,
            "failed_posts": 0,
            "platforms": {}
        }
        
        log_path = "./data/logs/posting_log.jsonl"
        if os.path.exists(log_path):
            with open(log_path, "r") as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        stats["total_posts"] += 1
                        
                        if entry["success"]:
                            stats["successful_posts"] += 1
                        else:
                            stats["failed_posts"] += 1
                        
                        platform = entry["platform"]
                        if platform not in stats["platforms"]:
                            stats["platforms"][platform] = {"successful": 0, "failed": 0}
                        
                        if entry["success"]:
                            stats["platforms"][platform]["successful"] += 1
                        else:
                            stats["platforms"][platform]["failed"] += 1
        
        return stats