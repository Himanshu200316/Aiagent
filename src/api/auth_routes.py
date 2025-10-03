"""
Authentication API Routes
Handles user authentication and credential management
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from auth.security import SecurityManager, CredentialManager
from storage.data_manager import DataManager

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Pydantic models
class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class SocialCredentials(BaseModel):
    platform: str
    credentials: Dict[str, Any]

class CredentialsResponse(BaseModel):
    platform: str
    has_credentials: bool
    last_updated: str = None

# Global instances
data_manager = DataManager()
credential_manager = CredentialManager(data_manager)
security_manager = SecurityManager()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    token = credentials.credentials
    payload = security_manager.verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload

@router.post("/register", response_model=TokenResponse)
async def register_user(user_data: UserRegister):
    """Register a new user"""
    try:
        # Check if user already exists (placeholder - would use real database)
        # For now, just create a token
        
        # Hash password
        hashed_password = security_manager.get_password_hash(user_data.password)
        
        # Create user (placeholder)
        user_id = f"user_{user_data.username}"
        
        # Create access token
        access_token = security_manager.create_access_token(
            data={"sub": user_id, "username": user_data.username}
        )
        
        logger.info(f"User registered: {user_data.username}")
        
        return TokenResponse(access_token=access_token)
        
    except Exception as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login", response_model=TokenResponse)
async def login_user(user_data: UserLogin):
    """Authenticate user and return access token"""
    try:
        # Verify credentials (placeholder - would use real database)
        # For demo purposes, accept any username/password combination
        
        user_id = f"user_{user_data.username}"
        
        # Create access token
        access_token = security_manager.create_access_token(
            data={"sub": user_id, "username": user_data.username}
        )
        
        logger.info(f"User logged in: {user_data.username}")
        
        return TokenResponse(access_token=access_token)
        
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/credentials")
async def store_social_credentials(
    creds: SocialCredentials,
    current_user: Dict = Depends(get_current_user)
):
    """Store social media credentials for the authenticated user"""
    try:
        user_id = current_user["sub"]
        
        success = await credential_manager.store_credentials(
            user_id=user_id,
            platform=creds.platform,
            credentials=creds.credentials
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid credentials format for {creds.platform}"
            )
        
        return {
            "message": f"Credentials stored successfully for {creds.platform}",
            "platform": creds.platform
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to store credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to store credentials")

@router.get("/credentials", response_model=List[CredentialsResponse])
async def list_user_credentials(current_user: Dict = Depends(get_current_user)):
    """List platforms for which user has stored credentials"""
    try:
        user_id = current_user["sub"]
        
        platforms = await credential_manager.list_user_platforms(user_id)
        
        response = []
        for platform in platforms:
            response.append(CredentialsResponse(
                platform=platform,
                has_credentials=True
            ))
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to list credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to list credentials")

@router.get("/credentials/{platform}")
async def get_platform_credentials(
    platform: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get credentials for a specific platform (returns only metadata, not actual credentials)"""
    try:
        user_id = current_user["sub"]
        
        credentials = await credential_manager.get_credentials(user_id, platform)
        
        if not credentials:
            raise HTTPException(
                status_code=404,
                detail=f"No credentials found for {platform}"
            )
        
        # Return only metadata, not actual credentials
        return {
            "platform": platform,
            "has_credentials": True,
            "fields_present": list(credentials.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get platform credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to get credentials")

@router.put("/credentials/{platform}")
async def update_platform_credentials(
    platform: str,
    credentials: Dict[str, Any],
    current_user: Dict = Depends(get_current_user)
):
    """Update credentials for a specific platform"""
    try:
        user_id = current_user["sub"]
        
        success = await credential_manager.update_credentials(
            user_id=user_id,
            platform=platform,
            credentials=credentials
        )
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid credentials format for {platform}"
            )
        
        return {
            "message": f"Credentials updated successfully for {platform}",
            "platform": platform
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to update credentials")

@router.delete("/credentials/{platform}")
async def delete_platform_credentials(
    platform: str,
    current_user: Dict = Depends(get_current_user)
):
    """Delete credentials for a specific platform"""
    try:
        user_id = current_user["sub"]
        
        success = await credential_manager.delete_credentials(user_id, platform)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"No credentials found for {platform}"
            )
        
        return {
            "message": f"Credentials deleted successfully for {platform}",
            "platform": platform
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete credentials")

@router.post("/test-credentials/{platform}")
async def test_platform_credentials(
    platform: str,
    current_user: Dict = Depends(get_current_user)
):
    """Test if stored credentials work for a platform"""
    try:
        user_id = current_user["sub"]
        
        credentials = await credential_manager.get_credentials(user_id, platform)
        
        if not credentials:
            raise HTTPException(
                status_code=404,
                detail=f"No credentials found for {platform}"
            )
        
        # Test credentials by creating and authenticating with platform module
        if platform == 'instagram':
            from mcp_modules.instagram_module import InstagramModule
            module = InstagramModule(credentials)
        elif platform == 'twitter':
            from mcp_modules.twitter_module import TwitterModule
            module = TwitterModule(credentials)
        elif platform == 'linkedin':
            from mcp_modules.linkedin_module import LinkedInModule
            module = LinkedInModule(credentials)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported platform: {platform}"
            )
        
        # Test authentication
        auth_success = await module.authenticate()
        
        if auth_success:
            # Get account info if authentication successful
            account_info = await module.get_account_info()
            return {
                "platform": platform,
                "authentication": "success",
                "account_info": account_info
            }
        else:
            return {
                "platform": platform,
                "authentication": "failed",
                "error": "Authentication failed with provided credentials"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to test credentials: {e}")
        raise HTTPException(status_code=500, detail="Failed to test credentials")

@router.get("/me")
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    """Get current user information"""
    return {
        "user_id": current_user["sub"],
        "username": current_user.get("username"),
        "authenticated": True
    }