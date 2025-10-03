"""
API routes for the social media advertising agent.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import List, Optional
import json
from datetime import datetime

from src.api.cerebrus_client import CerebrusClient
from src.models.schemas import (
    CredentialsRequest, AdRequirements, ImageRequest, 
    GeneratedContent, PostingSchedule, UserInteraction,
    Platform, PostType
)
from src.ai.content_generator import ContentGenerator
from src.storage.prompt_manager import PromptManager
from src.mcp.social_media_manager import SocialMediaManager

router = APIRouter()

# Dependency injection
async def get_cerebrus_client():
    client = CerebrusClient()
    try:
        yield client
    finally:
        await client.close()

async def get_content_generator():
    generator = ContentGenerator()
    await generator.initialize()
    return generator

async def get_prompt_manager():
    return PromptManager()

async def get_social_media_manager():
    return SocialMediaManager()

@router.post("/chat")
async def chat_with_agent(
    user_interaction: UserInteraction,
    cerebrus_client: CerebrusClient = Depends(get_cerebrus_client)
):
    """Main chat endpoint for user interaction."""
    try:
        response = await cerebrus_client.process_user_input(user_interaction)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/credentials")
async def store_credentials(
    credentials_request: CredentialsRequest,
    social_media_manager: SocialMediaManager = Depends(get_social_media_manager)
):
    """Store social media platform credentials."""
    try:
        success = await social_media_manager.store_credentials(
            credentials_request.platform,
            credentials_request.credentials,
            credentials_request.user_id
        )
        
        if success:
            return {"message": f"Credentials stored successfully for {credentials_request.platform}"}
        else:
            raise HTTPException(status_code=400, detail="Failed to store credentials")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-ad")
async def generate_ad(
    requirements: AdRequirements,
    content_generator: ContentGenerator = Depends(get_content_generator),
    prompt_manager: PromptManager = Depends(get_prompt_manager)
):
    """Generate ad content based on requirements."""
    try:
        # Generate content
        generated_content = await content_generator.generate_ad_content(requirements)
        
        # Store prompt to prevent duplicates
        await prompt_manager.store_prompt(
            requirements.product_description,
            requirements.tone,
            requirements.target_audience,
            generated_content.caption
        )
        
        return generated_content
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate-image")
async def generate_image(
    image_request: ImageRequest,
    content_generator: ContentGenerator = Depends(get_content_generator)
):
    """Generate or process image for ads."""
    try:
        if image_request.type == "generate":
            image_url = await content_generator.generate_image(image_request.prompt, image_request.style)
            return {"image_url": image_url, "type": "generated"}
        elif image_request.type == "upload":
            # Process uploaded image
            processed_url = await content_generator.process_uploaded_image(image_request.image_data)
            return {"image_url": processed_url, "type": "uploaded"}
        else:
            raise HTTPException(status_code=400, detail="Invalid image type")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    content_generator: ContentGenerator = Depends(get_content_generator)
):
    """Upload custom image for ads."""
    try:
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Read file content
        content = await file.read()
        
        # Process image
        image_url = await content_generator.process_uploaded_image(content)
        
        return {"image_url": image_url, "filename": file.filename}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/post-content")
async def post_content(
    content: GeneratedContent,
    platforms: List[Platform],
    social_media_manager: SocialMediaManager = Depends(get_social_media_manager)
):
    """Post generated content to social media platforms."""
    try:
        results = []
        
        for platform in platforms:
            result = await social_media_manager.post_content(
                platform, content, PostType.FEED
            )
            results.append({
                "platform": platform,
                "success": result["success"],
                "post_id": result.get("post_id"),
                "error": result.get("error")
            })
        
        return {"results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/posting-history")
async def get_posting_history(
    limit: int = 50,
    prompt_manager: PromptManager = Depends(get_prompt_manager)
):
    """Get posting history."""
    try:
        history = await prompt_manager.get_posting_history(limit)
        return {"history": history}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/schedule")
async def update_schedule(
    schedule: PostingSchedule
):
    """Update posting schedule."""
    try:
        # This would update the scheduler configuration
        return {"message": "Schedule updated successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/schedule")
async def get_schedule():
    """Get current posting schedule."""
    try:
        # This would return current schedule configuration
        return {
            "enabled": True,
            "time": "00:00",
            "timezone": "UTC",
            "platforms": ["instagram", "twitter", "linkedin"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/platforms")
async def get_supported_platforms():
    """Get list of supported platforms."""
    return {
        "platforms": [
            {"name": "Instagram", "value": "instagram", "features": ["feed", "stories"]},
            {"name": "Twitter", "value": "twitter", "features": ["tweets"]},
            {"name": "LinkedIn", "value": "linkedin", "features": ["posts"]}
        ]
    }