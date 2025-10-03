"""
Content Generation API routes
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.api.routes.auth import get_current_user
from app.services.ai_content_generator import AIContentGenerator
from app.services.storage_manager import storage_manager
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger('content_generation')

class ContentGenerationRequest(BaseModel):
    product_description: str
    tone: str = "professional"
    target_audience: str = "general"
    platforms: List[str] = ["instagram"]
    generate_image: bool = True
    image_style: str = "professional"

class ImageAnalysisRequest(BaseModel):
    image_path: str

@router.post("/generate")
async def generate_content(
    request: ContentGenerationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Generate AI content (image + captions)"""
    try:
        user_id = current_user["id"]
        
        # Check if similar content already exists
        prompt_data = {
            "product_description": request.product_description,
            "tone": request.tone,
            "target_audience": request.target_audience,
            "platforms": request.platforms
        }
        
        if storage_manager.check_prompt_exists(prompt_data):
            return {
                "success": False,
                "error": "Similar content already exists. Please modify your request to avoid duplicates."
            }
        
        # Generate content
        ai_generator = AIContentGenerator()
        result = await ai_generator.generate_complete_content(
            product_description=request.product_description,
            tone=request.tone,
            target_audience=request.target_audience,
            platforms=request.platforms,
            generate_image=request.generate_image,
            image_style=request.image_style
        )
        
        if result["success"]:
            # Store prompt to avoid duplicates
            prompt_hash = storage_manager.store_prompt(user_id, prompt_data)
            
            # Store content history
            storage_manager.store_content_history(user_id, result)
            
            logger.info(f"Content generated for user {user_id}: {result.get('content_id')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate content: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate content"
        )

@router.post("/generate-caption")
async def generate_caption(
    product_description: str,
    tone: str = "professional",
    target_audience: str = "general",
    platform: str = "instagram",
    max_length: int = 200,
    current_user: dict = Depends(get_current_user)
):
    """Generate AI caption only"""
    try:
        user_id = current_user["id"]
        
        ai_generator = AIContentGenerator()
        result = await ai_generator.generate_caption(
            product_description=product_description,
            tone=tone,
            target_audience=target_audience,
            platform=platform,
            max_length=max_length
        )
        
        if result["success"]:
            logger.info(f"Caption generated for user {user_id}: {platform}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate caption: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate caption"
        )

@router.post("/generate-image")
async def generate_image(
    prompt: str,
    style: str = "professional",
    size: tuple = (1024, 1024),
    quality: int = 95,
    current_user: dict = Depends(get_current_user)
):
    """Generate AI image only"""
    try:
        user_id = current_user["id"]
        
        ai_generator = AIContentGenerator()
        result = await ai_generator.generate_image(
            prompt=prompt,
            style=style,
            size=size,
            quality=quality
        )
        
        if result["success"]:
            logger.info(f"Image generated for user {user_id}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to generate image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate image"
        )

@router.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload user image for analysis and caption generation"""
    try:
        user_id = current_user["id"]
        
        # Validate file type
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )
        
        # Save uploaded file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"uploaded_{user_id}_{timestamp}_{file.filename}"
        
        import os
        from app.core.config import settings
        os.makedirs(settings.images_dir, exist_ok=True)
        
        file_path = os.path.join(settings.images_dir, filename)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Analyze image
        ai_generator = AIContentGenerator()
        analysis_result = await ai_generator.analyze_uploaded_image(file_path)
        
        logger.info(f"Image uploaded and analyzed for user {user_id}: {filename}")
        
        return {
            "success": True,
            "image_path": file_path,
            "filename": filename,
            "analysis": analysis_result.get("analysis", ""),
            "uploaded_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to upload image"
        )

@router.get("/history")
async def get_content_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get user's content generation history"""
    try:
        user_id = current_user["id"]
        
        history = storage_manager.get_user_content_history(user_id, limit)
        
        return {
            "success": True,
            "history": history,
            "count": len(history)
        }
        
    except Exception as e:
        logger.error(f"Failed to get content history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get content history"
        )

@router.get("/prompts")
async def get_prompts(
    current_user: dict = Depends(get_current_user)
):
    """Get user's stored prompts"""
    try:
        user_id = current_user["id"]
        
        # Get all prompt files for user
        import os
        from pathlib import Path
        from app.core.config import settings
        
        prompts_dir = Path(settings.prompts_dir)
        user_prompts = []
        
        for prompt_file in prompts_dir.glob(f"prompt_{user_id}_*.json"):
            with open(prompt_file, 'r') as f:
                import json
                prompt_data = json.load(f)
                user_prompts.append({
                    "prompt_id": prompt_data["prompt_id"],
                    "prompt_hash": prompt_data["prompt_hash"],
                    "prompt_data": prompt_data["prompt_data"],
                    "created_at": prompt_data["created_at"],
                    "used_count": prompt_data["used_count"],
                    "last_used": prompt_data["last_used"]
                })
        
        # Sort by creation date (newest first)
        user_prompts.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "success": True,
            "prompts": user_prompts,
            "count": len(user_prompts)
        }
        
    except Exception as e:
        logger.error(f"Failed to get prompts: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get prompts"
        )

@router.delete("/prompts/{prompt_hash}")
async def delete_prompt(
    prompt_hash: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a stored prompt"""
    try:
        user_id = current_user["id"]
        
        # Find and delete prompt file
        import os
        from pathlib import Path
        from app.core.config import settings
        
        prompts_dir = Path(settings.prompts_dir)
        prompt_file = prompts_dir / f"prompt_{user_id}_{prompt_hash}.json"
        
        if prompt_file.exists():
            prompt_file.unlink()
            logger.info(f"Prompt deleted: {prompt_hash}")
            
            return {
                "success": True,
                "message": "Prompt deleted successfully"
            }
        else:
            raise HTTPException(
                status_code=404,
                detail="Prompt not found"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete prompt: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete prompt"
        )