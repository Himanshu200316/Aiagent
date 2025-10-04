"""
Posting Management API Routes
Handles posting schedules, campaigns, and posting history
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import time, datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from scheduler.post_scheduler import PostScheduler
from storage.data_manager import DataManager
from api.auth_routes import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class CampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    product_service_description: str
    target_audience: str
    tone: str
    platforms: List[str]

class CampaignResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    product_service_description: str
    target_audience: str
    tone: str
    is_active: bool
    created_at: str

class ScheduleUpdate(BaseModel):
    platform: str
    post_time: str  # Format: "HH:MM"
    timezone: str = "UTC"

class PostHistoryResponse(BaseModel):
    id: int
    platform: str
    platform_post_id: Optional[str]
    post_url: Optional[str]
    posted_at: str
    status: str
    caption: str
    image_path: Optional[str]

# Global instances
post_scheduler = PostScheduler()
data_manager = DataManager()

@router.post("/campaigns", response_model=CampaignResponse)
async def create_campaign(
    campaign: CampaignCreate,
    current_user: Dict = Depends(get_current_user)
):
    """Create a new advertising campaign"""
    try:
        user_id = current_user["sub"]
        
        campaign_data = {
            "name": campaign.name,
            "description": campaign.description,
            "product_service_description": campaign.product_service_description,
            "target_audience": campaign.target_audience,
            "tone": campaign.tone,
            "user_id": user_id
        }
        
        campaign_id = await data_manager.create_campaign(campaign_data)
        
        # Schedule the campaign
        campaign_record = {
            "id": campaign_id,
            **campaign_data,
            "is_active": True,
            "created_at": datetime.now()
        }
        
        await post_scheduler._schedule_campaign(campaign_record)
        
        return CampaignResponse(
            id=campaign_id,
            name=campaign.name,
            description=campaign.description,
            product_service_description=campaign.product_service_description,
            target_audience=campaign.target_audience,
            tone=campaign.tone,
            is_active=True,
            created_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Failed to create campaign: {e}")
        raise HTTPException(status_code=500, detail="Failed to create campaign")

@router.get("/campaigns", response_model=List[CampaignResponse])
async def get_campaigns(
    active_only: bool = True,
    current_user: Dict = Depends(get_current_user)
):
    """Get user's campaigns"""
    try:
        user_id = current_user["sub"]
        
        campaigns = await data_manager.get_campaigns(user_id=user_id, active_only=active_only)
        
        return [
            CampaignResponse(
                id=campaign["id"],
                name=campaign["name"],
                description=campaign.get("description"),
                product_service_description=campaign["product_service_description"],
                target_audience=campaign["target_audience"],
                tone=campaign["tone"],
                is_active=bool(campaign["is_active"]),
                created_at=campaign["created_at"]
            )
            for campaign in campaigns
        ]
        
    except Exception as e:
        logger.error(f"Failed to get campaigns: {e}")
        raise HTTPException(status_code=500, detail="Failed to get campaigns")

@router.get("/campaigns/{campaign_id}", response_model=CampaignResponse)
async def get_campaign(
    campaign_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Get specific campaign details"""
    try:
        campaigns = await data_manager.get_campaigns(active_only=False)
        campaign = next((c for c in campaigns if c["id"] == campaign_id), None)
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Check if user owns this campaign
        if campaign.get("user_id") != current_user["sub"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return CampaignResponse(
            id=campaign["id"],
            name=campaign["name"],
            description=campaign.get("description"),
            product_service_description=campaign["product_service_description"],
            target_audience=campaign["target_audience"],
            tone=campaign["tone"],
            is_active=bool(campaign["is_active"]),
            created_at=campaign["created_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get campaign: {e}")
        raise HTTPException(status_code=500, detail="Failed to get campaign")

@router.put("/campaigns/{campaign_id}/schedule")
async def update_campaign_schedule(
    campaign_id: str,
    schedule: ScheduleUpdate,
    current_user: Dict = Depends(get_current_user)
):
    """Update posting schedule for a campaign"""
    try:
        # Verify campaign ownership
        campaigns = await data_manager.get_campaigns(active_only=False)
        campaign = next((c for c in campaigns if c["id"] == campaign_id), None)
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        if campaign.get("user_id") != current_user["sub"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Parse time
        try:
            hour, minute = map(int, schedule.post_time.split(':'))
            post_time = time(hour, minute)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid time format. Use HH:MM")
        
        # Update schedule
        await post_scheduler.add_campaign_schedule(
            campaign_id=campaign_id,
            platform=schedule.platform,
            post_time=post_time,
            timezone=schedule.timezone
        )
        
        return {
            "message": f"Schedule updated for campaign {campaign_id} on {schedule.platform}",
            "campaign_id": campaign_id,
            "platform": schedule.platform,
            "post_time": schedule.post_time,
            "timezone": schedule.timezone
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update campaign schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to update schedule")

@router.post("/campaigns/{campaign_id}/post-now")
async def trigger_immediate_post(
    campaign_id: str,
    platform: str,
    current_user: Dict = Depends(get_current_user)
):
    """Trigger an immediate post for testing"""
    try:
        # Verify campaign ownership
        campaigns = await data_manager.get_campaigns(active_only=False)
        campaign = next((c for c in campaigns if c["id"] == campaign_id), None)
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        if campaign.get("user_id") != current_user["sub"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Trigger immediate post
        result = await post_scheduler.trigger_immediate_post(campaign_id, platform)
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to trigger immediate post: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger post")

@router.delete("/campaigns/{campaign_id}")
async def delete_campaign(
    campaign_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Delete/deactivate a campaign"""
    try:
        # Verify campaign ownership
        campaigns = await data_manager.get_campaigns(active_only=False)
        campaign = next((c for c in campaigns if c["id"] == campaign_id), None)
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        if campaign.get("user_id") != current_user["sub"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Remove from scheduler
        await post_scheduler.remove_campaign_schedule(campaign_id)
        
        # Deactivate in database (don't actually delete for history)
        # This would be implemented in data_manager
        
        return {
            "message": f"Campaign {campaign_id} deactivated successfully",
            "campaign_id": campaign_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete campaign: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete campaign")

@router.get("/history", response_model=List[PostHistoryResponse])
async def get_posting_history(
    platform: Optional[str] = None,
    days: int = 30,
    limit: int = 50,
    offset: int = 0,
    current_user: Dict = Depends(get_current_user)
):
    """Get posting history for user"""
    try:
        # Get posting history from data manager
        history = await data_manager.get_posting_history(platform=platform, days=days)
        
        # Filter by user's campaigns (would need to join with campaigns table)
        # For now, return all history
        
        # Apply pagination
        paginated_history = history[offset:offset + limit]
        
        return [
            PostHistoryResponse(
                id=post["id"],
                platform=post["platform"],
                platform_post_id=post.get("platform_post_id"),
                post_url=post.get("post_url"),
                posted_at=post["posted_at"],
                status=post["status"],
                caption=post.get("generated_caption", ""),
                image_path=post.get("image_path")
            )
            for post in paginated_history
        ]
        
    except Exception as e:
        logger.error(f"Failed to get posting history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get posting history")

@router.get("/schedule")
async def get_scheduled_jobs(current_user: Dict = Depends(get_current_user)):
    """Get list of scheduled posting jobs"""
    try:
        jobs = await post_scheduler.get_scheduled_jobs()
        
        return {
            "scheduled_jobs": jobs,
            "total_jobs": len(jobs)
        }
        
    except Exception as e:
        logger.error(f"Failed to get scheduled jobs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get scheduled jobs")

@router.get("/stats")
async def get_posting_stats(
    days: int = 30,
    current_user: Dict = Depends(get_current_user)
):
    """Get posting statistics"""
    try:
        # Get stats from data manager
        stats = await data_manager.get_stats()
        
        return {
            "total_posts": stats.get("total_posts", 0),
            "success_rate": stats.get("success_rate", 0),
            "posts_by_platform": stats.get("posts_by_platform", {}),
            "active_campaigns": stats.get("active_campaigns", 0),
            "period_days": days
        }
        
    except Exception as e:
        logger.error(f"Failed to get posting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get posting stats")

@router.get("/health")
async def posting_health_check():
    """Check health of posting system"""
    try:
        scheduler_health = await post_scheduler.health_check()
        data_health = await data_manager.health_check()
        
        return {
            "scheduler": scheduler_health,
            "data_manager": data_health,
            "overall_status": "healthy" if scheduler_health.get("running") and data_health.get("initialized") else "unhealthy"
        }
        
    except Exception as e:
        logger.error(f"Posting health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}