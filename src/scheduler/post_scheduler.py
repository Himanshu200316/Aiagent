"""
Automated Post Scheduler
Handles scheduled posting of generated content to social media platforms
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, time, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
import pytz

from storage.data_manager import DataManager
from ai_generation.content_generator import ContentGenerator, ContentRequest
from mcp_modules.instagram_module import InstagramModule
from mcp_modules.twitter_module import TwitterModule
from mcp_modules.linkedin_module import LinkedInModule
from mcp_modules.base_module import MediaItem

logger = logging.getLogger(__name__)

class PostScheduler:
    """Automated posting scheduler"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.data_manager = DataManager()
        self.content_generator = ContentGenerator()
        self.platform_modules = {}
        self.active_campaigns = {}
        self.running = False
        
    async def start(self):
        """Start the scheduler"""
        try:
            # Initialize components
            await self.data_manager.initialize()
            await self.content_generator.initialize()
            
            # Load active campaigns
            await self._load_active_campaigns()
            
            # Start scheduler
            self.scheduler.start()
            self.running = True
            
            # Schedule cleanup task
            self.scheduler.add_job(
                self._cleanup_old_data,
                trigger=CronTrigger(hour=2, minute=0),  # Daily at 2 AM
                id='cleanup_task',
                replace_existing=True
            )
            
            logger.info("Post scheduler started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {e}")
            raise
    
    async def stop(self):
        """Stop the scheduler"""
        if self.running:
            self.scheduler.shutdown(wait=True)
            self.running = False
            logger.info("Post scheduler stopped")
    
    async def _load_active_campaigns(self):
        """Load active campaigns and schedule their posts"""
        try:
            campaigns = await self.data_manager.get_campaigns(active_only=True)
            
            for campaign in campaigns:
                await self._schedule_campaign(campaign)
            
            logger.info(f"Loaded {len(campaigns)} active campaigns")
            
        except Exception as e:
            logger.error(f"Failed to load active campaigns: {e}")
    
    async def _schedule_campaign(self, campaign: Dict[str, Any]):
        """Schedule posts for a specific campaign"""
        try:
            campaign_id = campaign['id']
            self.active_campaigns[campaign_id] = campaign
            
            # Get posting schedule for this campaign
            # For now, use default daily at 12 AM
            default_time = time(0, 0)  # 12:00 AM
            timezone = pytz.UTC
            
            # Create job for each platform
            platforms = ['instagram', 'twitter', 'linkedin']  # Default platforms
            
            for platform in platforms:
                job_id = f"campaign_{campaign_id}_{platform}"
                
                self.scheduler.add_job(
                    self._generate_and_post,
                    trigger=CronTrigger(
                        hour=default_time.hour,
                        minute=default_time.minute,
                        timezone=timezone
                    ),
                    args=[campaign_id, platform],
                    id=job_id,
                    replace_existing=True
                )
            
            logger.info(f"Scheduled posts for campaign {campaign_id}")
            
        except Exception as e:
            logger.error(f"Failed to schedule campaign {campaign.get('id')}: {e}")
    
    async def _generate_and_post(self, campaign_id: str, platform: str):
        """Generate content and post to platform"""
        try:
            campaign = self.active_campaigns.get(campaign_id)
            if not campaign:
                logger.warning(f"Campaign {campaign_id} not found")
                return
            
            logger.info(f"Generating content for campaign {campaign_id} on {platform}")
            
            # Create content request
            request = ContentRequest(
                product_service_description=campaign.get('product_service_description', ''),
                target_audience=campaign.get('target_audience', ''),
                tone=campaign.get('tone', 'professional'),
                platforms=[platform],
                content_type='feed_post'
            )
            
            # Generate content
            content = await self.content_generator.generate_content(request)
            
            # Get platform module
            platform_module = await self._get_platform_module(platform, campaign_id)
            if not platform_module:
                logger.error(f"Platform module not available for {platform}")
                return
            
            # Prepare media if image exists
            media = None
            if content.image_path:
                media = [MediaItem(
                    file_path=content.image_path,
                    media_type='image',
                    caption=content.caption,
                    alt_text=f"Advertisement for {campaign.get('name', 'product')}"
                )]
            
            # Post to platform
            post_result = await platform_module.post_content(
                content=content.caption,
                media=media
            )
            
            # Store post result
            content_id = await self.data_manager.store_content(content, {
                'campaign_id': campaign_id,
                'platform': platform
            })
            
            await self.data_manager.store_post_result(
                content_id=content_id,
                platform=platform,
                post_result=post_result
            )
            
            if post_result.success:
                logger.info(f"Successfully posted to {platform} for campaign {campaign_id}")
            else:
                logger.error(f"Failed to post to {platform}: {post_result.error_message}")
            
        except Exception as e:
            logger.error(f"Failed to generate and post for campaign {campaign_id} on {platform}: {e}")
    
    async def _get_platform_module(self, platform: str, campaign_id: str):
        """Get or create platform module"""
        try:
            module_key = f"{platform}_{campaign_id}"
            
            if module_key not in self.platform_modules:
                # Load credentials for this campaign/platform
                credentials = await self._get_platform_credentials(platform, campaign_id)
                
                if not credentials:
                    logger.warning(f"No credentials found for {platform}")
                    return None
                
                # Create platform module
                if platform == 'instagram':
                    module = InstagramModule(credentials)
                elif platform == 'twitter':
                    module = TwitterModule(credentials)
                elif platform == 'linkedin':
                    module = LinkedInModule(credentials)
                else:
                    logger.error(f"Unsupported platform: {platform}")
                    return None
                
                # Test authentication
                if await module.authenticate():
                    self.platform_modules[module_key] = module
                else:
                    logger.error(f"Authentication failed for {platform}")
                    return None
            
            return self.platform_modules.get(module_key)
            
        except Exception as e:
            logger.error(f"Failed to get platform module for {platform}: {e}")
            return None
    
    async def _get_platform_credentials(self, platform: str, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get platform credentials (placeholder - would integrate with secure storage)"""
        # In a real implementation, this would fetch encrypted credentials from database
        # For now, return environment-based credentials
        import os
        
        if platform == 'instagram':
            username = os.getenv('INSTAGRAM_USERNAME')
            password = os.getenv('INSTAGRAM_PASSWORD')
            if username and password:
                return {'username': username, 'password': password}
        
        elif platform == 'twitter':
            return {
                'api_key': os.getenv('TWITTER_API_KEY'),
                'api_secret': os.getenv('TWITTER_API_SECRET'),
                'access_token': os.getenv('TWITTER_ACCESS_TOKEN'),
                'access_token_secret': os.getenv('TWITTER_ACCESS_TOKEN_SECRET'),
                'bearer_token': os.getenv('TWITTER_BEARER_TOKEN')
            }
        
        elif platform == 'linkedin':
            access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
            if access_token:
                return {'access_token': access_token}
        
        return None
    
    async def add_campaign_schedule(self, campaign_id: str, platform: str, 
                                  post_time: time, timezone: str = 'UTC'):
        """Add or update posting schedule for a campaign"""
        try:
            tz = pytz.timezone(timezone)
            job_id = f"campaign_{campaign_id}_{platform}"
            
            # Remove existing job if it exists
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # Add new job
            self.scheduler.add_job(
                self._generate_and_post,
                trigger=CronTrigger(
                    hour=post_time.hour,
                    minute=post_time.minute,
                    timezone=tz
                ),
                args=[campaign_id, platform],
                id=job_id,
                replace_existing=True
            )
            
            logger.info(f"Updated schedule for campaign {campaign_id} on {platform}")
            
        except Exception as e:
            logger.error(f"Failed to add campaign schedule: {e}")
            raise
    
    async def remove_campaign_schedule(self, campaign_id: str, platform: Optional[str] = None):
        """Remove posting schedule for a campaign"""
        try:
            if platform:
                # Remove specific platform
                job_id = f"campaign_{campaign_id}_{platform}"
                if self.scheduler.get_job(job_id):
                    self.scheduler.remove_job(job_id)
                    logger.info(f"Removed schedule for campaign {campaign_id} on {platform}")
            else:
                # Remove all platforms for this campaign
                platforms = ['instagram', 'twitter', 'linkedin']
                for p in platforms:
                    job_id = f"campaign_{campaign_id}_{p}"
                    if self.scheduler.get_job(job_id):
                        self.scheduler.remove_job(job_id)
                
                # Remove from active campaigns
                if campaign_id in self.active_campaigns:
                    del self.active_campaigns[campaign_id]
                
                logger.info(f"Removed all schedules for campaign {campaign_id}")
            
        except Exception as e:
            logger.error(f"Failed to remove campaign schedule: {e}")
    
    async def trigger_immediate_post(self, campaign_id: str, platform: str) -> Dict[str, Any]:
        """Trigger an immediate post for testing"""
        try:
            logger.info(f"Triggering immediate post for campaign {campaign_id} on {platform}")
            
            # Run the generation and posting task
            await self._generate_and_post(campaign_id, platform)
            
            return {
                'success': True,
                'message': f'Post triggered for campaign {campaign_id} on {platform}'
            }
            
        except Exception as e:
            logger.error(f"Failed to trigger immediate post: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_scheduled_jobs(self) -> List[Dict[str, Any]]:
        """Get list of all scheduled jobs"""
        try:
            jobs = []
            
            for job in self.scheduler.get_jobs():
                jobs.append({
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                })
            
            return jobs
            
        except Exception as e:
            logger.error(f"Failed to get scheduled jobs: {e}")
            return []
    
    async def _cleanup_old_data(self):
        """Clean up old data (runs daily)"""
        try:
            logger.info("Running daily cleanup task")
            
            # Clean up old content and posts (30 days)
            await self.data_manager.cleanup_old_data(days=30)
            
            # Clean up inactive platform modules
            active_campaigns = set(self.active_campaigns.keys())
            modules_to_remove = []
            
            for module_key in self.platform_modules.keys():
                campaign_id = module_key.split('_', 1)[1] if '_' in module_key else None
                if campaign_id and campaign_id not in active_campaigns:
                    modules_to_remove.append(module_key)
            
            for module_key in modules_to_remove:
                del self.platform_modules[module_key]
            
            logger.info(f"Cleanup completed. Removed {len(modules_to_remove)} inactive modules")
            
        except Exception as e:
            logger.error(f"Cleanup task failed: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check scheduler health"""
        try:
            return {
                'running': self.running,
                'scheduler_state': self.scheduler.state if self.scheduler else None,
                'active_campaigns': len(self.active_campaigns),
                'scheduled_jobs': len(self.scheduler.get_jobs()) if self.scheduler else 0,
                'platform_modules': len(self.platform_modules)
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'running': False
            }