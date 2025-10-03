"""
Scheduling API routes
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime, time
from app.api.routes.auth import get_current_user
from app.services.storage_manager import storage_manager
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger('scheduling')

class ScheduleRequest(BaseModel):
    post_time: str = "00:00"  # Format: "HH:MM"
    frequency: str = "daily"  # "daily", "weekly", "custom"
    platforms: List[str] = ["instagram"]
    enabled: bool = True

class ScheduleResponse(BaseModel):
    schedule_id: str
    user_id: int
    post_time: str
    frequency: str
    platforms: List[str]
    enabled: bool
    created_at: str
    updated_at: str

@router.post("/setup")
async def setup_schedule(
    schedule: ScheduleRequest,
    current_user: dict = Depends(get_current_user)
):
    """Set up posting schedule for user"""
    try:
        user_id = current_user["id"]
        
        # Validate time format
        try:
            time.fromisoformat(schedule.post_time)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid time format. Use HH:MM format (e.g., '12:00')"
            )
        
        # Validate frequency
        if schedule.frequency not in ["daily", "weekly", "custom"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid frequency. Supported: daily, weekly, custom"
            )
        
        # Validate platforms
        supported_platforms = ["instagram", "twitter", "linkedin"]
        for platform in schedule.platforms:
            if platform not in supported_platforms:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported platform: {platform}. Supported: {supported_platforms}"
                )
        
        # Store schedule preferences
        schedule_data = {
            "post_time": schedule.post_time,
            "frequency": schedule.frequency,
            "platforms": schedule.platforms,
            "enabled": schedule.enabled
        }
        
        # Update user preferences
        preferences = storage_manager.get_user_preferences(user_id) or {}
        preferences["schedule"] = schedule_data
        preferences["updated_at"] = datetime.now().isoformat()
        
        storage_manager.store_user_preferences(user_id, preferences)
        
        schedule_id = f"schedule_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Schedule set up for user {user_id}: {schedule.post_time} {schedule.frequency}")
        
        return ScheduleResponse(
            schedule_id=schedule_id,
            user_id=user_id,
            post_time=schedule.post_time,
            frequency=schedule.frequency,
            platforms=schedule.platforms,
            enabled=schedule.enabled,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to setup schedule: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to setup schedule"
        )

@router.get("/current")
async def get_current_schedule(
    current_user: dict = Depends(get_current_user)
):
    """Get user's current posting schedule"""
    try:
        user_id = current_user["id"]
        
        preferences = storage_manager.get_user_preferences(user_id)
        
        if not preferences or "schedule" not in preferences:
            return {
                "success": True,
                "schedule": None,
                "message": "No schedule configured"
            }
        
        schedule_data = preferences["schedule"]
        
        return {
            "success": True,
            "schedule": {
                "post_time": schedule_data.get("post_time", "00:00"),
                "frequency": schedule_data.get("frequency", "daily"),
                "platforms": schedule_data.get("platforms", ["instagram"]),
                "enabled": schedule_data.get("enabled", True),
                "updated_at": preferences.get("updated_at")
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get current schedule: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get current schedule"
        )

@router.put("/update")
async def update_schedule(
    schedule: ScheduleRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update user's posting schedule"""
    try:
        user_id = current_user["id"]
        
        # Validate time format
        try:
            time.fromisoformat(schedule.post_time)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid time format. Use HH:MM format (e.g., '12:00')"
            )
        
        # Get current preferences
        preferences = storage_manager.get_user_preferences(user_id) or {}
        
        # Update schedule
        preferences["schedule"] = {
            "post_time": schedule.post_time,
            "frequency": schedule.frequency,
            "platforms": schedule.platforms,
            "enabled": schedule.enabled
        }
        preferences["updated_at"] = datetime.now().isoformat()
        
        # Store updated preferences
        storage_manager.store_user_preferences(user_id, preferences)
        
        logger.info(f"Schedule updated for user {user_id}: {schedule.post_time} {schedule.frequency}")
        
        return {
            "success": True,
            "message": "Schedule updated successfully",
            "schedule": preferences["schedule"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update schedule: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update schedule"
        )

@router.post("/enable")
async def enable_schedule(
    current_user: dict = Depends(get_current_user)
):
    """Enable user's posting schedule"""
    try:
        user_id = current_user["id"]
        
        preferences = storage_manager.get_user_preferences(user_id) or {}
        
        if "schedule" not in preferences:
            raise HTTPException(
                status_code=400,
                detail="No schedule configured. Please set up a schedule first."
            )
        
        preferences["schedule"]["enabled"] = True
        preferences["updated_at"] = datetime.now().isoformat()
        
        storage_manager.store_user_preferences(user_id, preferences)
        
        logger.info(f"Schedule enabled for user {user_id}")
        
        return {
            "success": True,
            "message": "Schedule enabled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to enable schedule: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to enable schedule"
        )

@router.post("/disable")
async def disable_schedule(
    current_user: dict = Depends(get_current_user)
):
    """Disable user's posting schedule"""
    try:
        user_id = current_user["id"]
        
        preferences = storage_manager.get_user_preferences(user_id) or {}
        
        if "schedule" not in preferences:
            raise HTTPException(
                status_code=400,
                detail="No schedule configured"
            )
        
        preferences["schedule"]["enabled"] = False
        preferences["updated_at"] = datetime.now().isoformat()
        
        storage_manager.store_user_preferences(user_id, preferences)
        
        logger.info(f"Schedule disabled for user {user_id}")
        
        return {
            "success": True,
            "message": "Schedule disabled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to disable schedule: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to disable schedule"
        )

@router.get("/history")
async def get_posting_history(
    platform: Optional[str] = None,
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """Get user's posting history"""
    try:
        user_id = current_user["id"]
        
        history = storage_manager.get_posting_history(user_id, platform, limit)
        
        return {
            "success": True,
            "history": history,
            "count": len(history),
            "platform_filter": platform
        }
        
    except Exception as e:
        logger.error(f"Failed to get posting history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get posting history"
        )

@router.post("/test-post")
async def test_post(
    current_user: dict = Depends(get_current_user)
):
    """Test posting functionality (generates and posts sample content)"""
    try:
        user_id = current_user["id"]
        
        # Get user preferences
        preferences = storage_manager.get_user_preferences(user_id)
        if not preferences:
            raise HTTPException(
                status_code=400,
                detail="No user preferences found. Please set up your preferences first."
            )
        
        # Generate test content
        from app.services.ai_content_generator import AIContentGenerator
        ai_generator = AIContentGenerator()
        
        test_result = await ai_generator.generate_complete_content(
            product_description="Test post from Social Media Agent",
            tone="professional",
            target_audience="general",
            platforms=["instagram"],
            generate_image=True,
            image_style="professional"
        )
        
        if not test_result["success"]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate test content: {test_result['error']}"
            )
        
        # Store test content
        storage_manager.store_content_history(user_id, test_result)
        
        logger.info(f"Test content generated for user {user_id}")
        
        return {
            "success": True,
            "message": "Test content generated successfully",
            "content": test_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate test post: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate test post"
        )