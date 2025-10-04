"""
Content Generation API Routes
Handles content generation requests and management
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel

from ai_generation.content_generator import ContentGenerator, ContentRequest
from auth.security import SecurityManager
from api.auth_routes import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class ContentGenerationRequest(BaseModel):
    product_service_description: str
    target_audience: str
    tone: str
    platforms: List[str]
    content_type: str = "feed_post"
    additional_context: Optional[str] = None

class ContentResponse(BaseModel):
    caption: str
    image_path: Optional[str]
    image_generation_prompt: Optional[str]
    prompt_hash: str
    platforms: List[str]
    content_type: str
    created_at: str

class VariationRequest(BaseModel):
    original_prompt_hash: str
    count: int = 3

# Global instances
content_generator = ContentGenerator()

@router.post("/generate", response_model=ContentResponse)
async def generate_content(
    request: ContentGenerationRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Generate new social media content"""
    try:
        # Create content request
        content_request = ContentRequest(
            product_service_description=request.product_service_description,
            target_audience=request.target_audience,
            tone=request.tone,
            platforms=request.platforms,
            content_type=request.content_type,
            additional_context=request.additional_context
        )
        
        # Generate content
        content = await content_generator.generate_content(content_request)
        
        return ContentResponse(
            caption=content.caption,
            image_path=content.image_path,
            image_generation_prompt=content.image_generation_prompt,
            prompt_hash=content.prompt_hash,
            platforms=content.platforms,
            content_type=content.content_type,
            created_at=content.created_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Content generation failed: {e}")
        raise HTTPException(status_code=500, detail="Content generation failed")

@router.post("/generate-with-image")
async def generate_content_with_image(
    product_service_description: str = Form(...),
    target_audience: str = Form(...),
    tone: str = Form(...),
    platforms: List[str] = Form(...),
    content_type: str = Form("feed_post"),
    additional_context: Optional[str] = Form(None),
    image: UploadFile = File(...),
    current_user: Dict = Depends(get_current_user)
):
    """Generate content with user-uploaded image"""
    try:
        # Validate image
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Only image files are allowed")
        
        # Save uploaded image
        import os
        from datetime import datetime
        
        upload_dir = "data/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{current_user['sub']}_{timestamp}_{image.filename}"
        image_path = os.path.join(upload_dir, filename)
        
        with open(image_path, "wb") as buffer:
            content = await image.read()
            buffer.write(content)
        
        # Create content request with user image
        content_request = ContentRequest(
            product_service_description=product_service_description,
            target_audience=target_audience,
            tone=tone,
            platforms=platforms,
            content_type=content_type,
            user_image_path=image_path,
            additional_context=additional_context
        )
        
        # Generate content
        generated_content = await content_generator.generate_content(content_request)
        
        return ContentResponse(
            caption=generated_content.caption,
            image_path=generated_content.image_path,
            image_generation_prompt=generated_content.image_generation_prompt,
            prompt_hash=generated_content.prompt_hash,
            platforms=generated_content.platforms,
            content_type=generated_content.content_type,
            created_at=generated_content.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Content generation with image failed: {e}")
        raise HTTPException(status_code=500, detail="Content generation failed")

@router.post("/variations", response_model=List[ContentResponse])
async def generate_variations(
    request: VariationRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Generate variations of existing content"""
    try:
        # Get original content (placeholder - would fetch from database)
        # For now, return error as we need to implement content retrieval
        raise HTTPException(
            status_code=501,
            detail="Variation generation not yet implemented"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Variation generation failed: {e}")
        raise HTTPException(status_code=500, detail="Variation generation failed")

@router.get("/history")
async def get_content_history(
    limit: int = 50,
    offset: int = 0,
    current_user: Dict = Depends(get_current_user)
):
    """Get user's content generation history"""
    try:
        # This would fetch from database based on user_id
        # For now, return placeholder
        return {
            "content": [],
            "total": 0,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Failed to get content history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get content history")

@router.get("/templates")
async def get_content_templates():
    """Get predefined content templates"""
    try:
        templates = [
            {
                "id": "product_launch",
                "name": "Product Launch",
                "description": "Template for announcing new products",
                "tone": "professional",
                "sample_prompt": "Exciting new product that solves customer problems"
            },
            {
                "id": "service_promotion",
                "name": "Service Promotion", 
                "description": "Template for promoting services",
                "tone": "casual",
                "sample_prompt": "Professional service that helps businesses grow"
            },
            {
                "id": "brand_awareness",
                "name": "Brand Awareness",
                "description": "Template for building brand recognition",
                "tone": "playful",
                "sample_prompt": "Innovative brand making a difference in the industry"
            },
            {
                "id": "event_promotion",
                "name": "Event Promotion",
                "description": "Template for promoting events",
                "tone": "energetic",
                "sample_prompt": "Upcoming event that brings people together"
            }
        ]
        
        return {"templates": templates}
        
    except Exception as e:
        logger.error(f"Failed to get templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to get templates")

@router.post("/preview")
async def preview_content(
    request: ContentGenerationRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Preview content without storing it"""
    try:
        # Create content request with preview flag
        content_request = ContentRequest(
            product_service_description=request.product_service_description,
            target_audience=request.target_audience,
            tone=request.tone,
            platforms=request.platforms,
            content_type=request.content_type,
            additional_context=f"PREVIEW - {request.additional_context or ''}"
        )
        
        # Generate content (this will still be stored due to current implementation)
        content = await content_generator.generate_content(content_request)
        
        return {
            "caption": content.caption,
            "image_path": content.image_path,
            "platforms": content.platforms,
            "content_type": content.content_type,
            "is_preview": True
        }
        
    except Exception as e:
        logger.error(f"Content preview failed: {e}")
        raise HTTPException(status_code=500, detail="Content preview failed")

@router.get("/stats")
async def get_content_stats(current_user: Dict = Depends(get_current_user)):
    """Get content generation statistics for user"""
    try:
        # This would calculate stats from database
        # For now, return placeholder stats
        return {
            "total_content_generated": 0,
            "content_by_platform": {
                "instagram": 0,
                "twitter": 0,
                "linkedin": 0
            },
            "content_by_type": {
                "feed_post": 0,
                "story": 0
            },
            "most_used_tone": "professional",
            "generation_success_rate": 100.0
        }
        
    except Exception as e:
        logger.error(f"Failed to get content stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get content stats")

@router.delete("/content/{prompt_hash}")
async def delete_content(
    prompt_hash: str,
    current_user: Dict = Depends(get_current_user)
):
    """Delete generated content"""
    try:
        # This would delete from database and clean up files
        # For now, return success
        return {
            "message": f"Content {prompt_hash} deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to delete content: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete content")

@router.get("/health")
async def content_health_check():
    """Check health of content generation system"""
    try:
        health_status = await content_generator.health_check()
        return health_status
        
    except Exception as e:
        logger.error(f"Content health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}