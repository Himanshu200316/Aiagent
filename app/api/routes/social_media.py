"""
Social Media API routes
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
from app.api.routes.auth import get_current_user
from app.services.mcp_instagram import MCPInstagram
from app.services.mcp_twitter import MCPTwitter
from app.services.mcp_linkedin import MCPLinkedIn
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger('social_media')

class SocialMediaCredentials(BaseModel):
    platform: str
    credentials: Dict[str, Any]

class PostContent(BaseModel):
    caption: str
    image_path: Optional[str] = None
    platforms: List[str] = ["instagram"]
    content_type: str = "feed"  # "feed" or "story"

class TestCredentials(BaseModel):
    platform: str
    credentials: Dict[str, Any]

@router.post("/credentials")
async def set_credentials(
    credentials: SocialMediaCredentials,
    current_user: dict = Depends(get_current_user)
):
    """Set social media credentials for user"""
    try:
        user_id = current_user["id"]
        platform = credentials.platform.lower()
        
        # Validate platform
        if platform not in ["instagram", "twitter", "linkedin"]:
            raise HTTPException(
                status_code=400,
                detail="Unsupported platform. Supported: instagram, twitter, linkedin"
            )
        
        # Test credentials
        test_result = await test_credentials_internal(platform, credentials.credentials)
        if not test_result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid credentials: {test_result['error']}"
            )
        
        # Store credentials in database
        from app.core.database import db_manager
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Check if credentials already exist
        cursor.execute(
            "SELECT id FROM social_media_credentials WHERE user_id = ? AND platform = ?",
            (user_id, platform)
        )
        
        if cursor.fetchone():
            # Update existing credentials
            cursor.execute(
                "UPDATE social_media_credentials SET credentials = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND platform = ?",
                (json.dumps(credentials.credentials), user_id, platform)
            )
        else:
            # Insert new credentials
            cursor.execute(
                "INSERT INTO social_media_credentials (user_id, platform, credentials) VALUES (?, ?, ?)",
                (user_id, platform, json.dumps(credentials.credentials))
            )
        
        conn.commit()
        conn.close()
        
        logger.info(f"Credentials set for {platform}: {user_id}")
        
        return {
            "success": True,
            "message": f"{platform.title()} credentials set successfully",
            "platform": platform
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set credentials: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to set credentials"
        )

@router.post("/test-credentials")
async def test_credentials(
    test_data: TestCredentials,
    current_user: dict = Depends(get_current_user)
):
    """Test social media credentials"""
    try:
        platform = test_data.platform.lower()
        credentials = test_data.credentials
        
        result = await test_credentials_internal(platform, credentials)
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to test credentials: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to test credentials"
        )

async def test_credentials_internal(platform: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
    """Internal function to test credentials"""
    try:
        if platform == "instagram":
            client = MCPInstagram(credentials)
        elif platform == "twitter":
            client = MCPTwitter(credentials)
        elif platform == "linkedin":
            client = MCPLinkedIn(credentials)
        else:
            return {
                "success": False,
                "error": "Unsupported platform"
            }
        
        # Test authentication
        auth_success = await client.authenticate()
        
        if auth_success:
            return {
                "success": True,
                "message": f"{platform.title()} credentials are valid",
                "platform": platform
            }
        else:
            return {
                "success": False,
                "error": f"Authentication failed for {platform}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/post")
async def post_content(
    content: PostContent,
    current_user: dict = Depends(get_current_user)
):
    """Post content to social media platforms"""
    try:
        user_id = current_user["id"]
        results = {}
        
        # Get user's credentials for each platform
        from app.core.database import db_manager
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        for platform in content.platforms:
            try:
                # Get credentials for platform
                cursor.execute(
                    "SELECT credentials FROM social_media_credentials WHERE user_id = ? AND platform = ? AND is_active = TRUE",
                    (user_id, platform)
                )
                
                cred_row = cursor.fetchone()
                if not cred_row:
                    results[platform] = {
                        "success": False,
                        "error": f"No credentials found for {platform}"
                    }
                    continue
                
                platform_credentials = json.loads(cred_row[0])
                
                # Initialize platform client
                if platform == "instagram":
                    client = MCPInstagram(platform_credentials)
                elif platform == "twitter":
                    client = MCPTwitter(platform_credentials)
                elif platform == "linkedin":
                    client = MCPLinkedIn(platform_credentials)
                else:
                    results[platform] = {
                        "success": False,
                        "error": f"Unsupported platform: {platform}"
                    }
                    continue
                
                # Authenticate
                auth_success = await client.authenticate()
                if not auth_success:
                    results[platform] = {
                        "success": False,
                        "error": f"Authentication failed for {platform}"
                    }
                    continue
                
                # Post content
                if content.content_type == "story" and platform == "instagram":
                    post_result = await client.post_story(content.image_path, content.caption)
                else:
                    post_result = await client.post_content({
                        "caption": content.caption,
                        "image_path": content.image_path
                    })
                
                results[platform] = post_result
                
            except Exception as e:
                logger.error(f"Failed to post to {platform}: {str(e)}")
                results[platform] = {
                    "success": False,
                    "error": str(e)
                }
        
        conn.close()
        
        # Log posting results
        await log_posting_results(user_id, content, results)
        
        return {
            "success": True,
            "results": results,
            "posted_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to post content: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to post content"
        )

@router.get("/credentials")
async def get_credentials(current_user: dict = Depends(get_current_user)):
    """Get user's social media credentials (without sensitive data)"""
    try:
        user_id = current_user["id"]
        
        from app.core.database import db_manager
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT platform, is_active, created_at FROM social_media_credentials WHERE user_id = ?",
            (user_id,)
        )
        
        credentials = []
        for row in cursor.fetchall():
            credentials.append({
                "platform": row[0],
                "is_active": bool(row[1]),
                "created_at": row[2]
            })
        
        conn.close()
        
        return {
            "success": True,
            "credentials": credentials
        }
        
    except Exception as e:
        logger.error(f"Failed to get credentials: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get credentials"
        )

@router.delete("/credentials/{platform}")
async def delete_credentials(
    platform: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete social media credentials"""
    try:
        user_id = current_user["id"]
        platform = platform.lower()
        
        from app.core.database import db_manager
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE social_media_credentials SET is_active = FALSE WHERE user_id = ? AND platform = ?",
            (user_id, platform)
        )
        
        conn.commit()
        conn.close()
        
        logger.info(f"Credentials deleted for {platform}: {user_id}")
        
        return {
            "success": True,
            "message": f"{platform.title()} credentials deleted"
        }
        
    except Exception as e:
        logger.error(f"Failed to delete credentials: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete credentials"
        )

async def log_posting_results(user_id: int, content: PostContent, results: Dict[str, Any]):
    """Log posting results to database"""
    try:
        from app.core.database import db_manager
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        for platform, result in results.items():
            cursor.execute(
                "INSERT INTO posting_history (user_id, content_id, platform, post_id, status, error_message) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    f"manual_post_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    platform,
                    result.get("post_id"),
                    "success" if result["success"] else "failed",
                    result.get("error")
                )
            )
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        logger.error(f"Failed to log posting results: {str(e)}")