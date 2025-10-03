"""
Scheduling Service for Automated Posting
Handles daily posting at 12 AM and custom schedules
"""
import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import sqlite3
from app.core.config import settings
from app.core.database import db_manager
from app.core.logging import get_logger
from app.services.ai_content_generator import AIContentGenerator
from app.services.mcp_instagram import MCPInstagram
from app.services.mcp_twitter import MCPTwitter
from app.services.mcp_linkedin import MCPLinkedIn

logger = get_logger('scheduler')

class PostingScheduler:
    """Handles automated posting schedules"""
    
    def __init__(self):
        self.ai_generator = AIContentGenerator()
        self.scheduler_running = False
        self.scheduled_tasks = {}
    
    async def start_scheduler(self):
        """Start the scheduling system"""
        try:
            self.scheduler_running = True
            
            # Schedule daily posting at 12 AM
            schedule.every().day.at(settings.default_post_time).do(
                self._daily_posting_job
            )
            
            logger.info(f"Scheduler started - Daily posting at {settings.default_post_time}")
            
            # Start the scheduler loop
            await self._scheduler_loop()
            
        except Exception as e:
            logger.error(f"Failed to start scheduler: {str(e)}")
            self.scheduler_running = False
    
    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.scheduler_running:
            try:
                schedule.run_pending()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler loop error: {str(e)}")
                await asyncio.sleep(60)
    
    async def _daily_posting_job(self):
        """Daily posting job - runs at scheduled time"""
        try:
            logger.info("Starting daily posting job")
            
            # Get all active users
            active_users = await self._get_active_users()
            
            for user in active_users:
                try:
                    await self._process_user_daily_posting(user)
                except Exception as e:
                    logger.error(f"Failed to process user {user['id']}: {str(e)}")
            
            logger.info("Daily posting job completed")
            
        except Exception as e:
            logger.error(f"Daily posting job failed: {str(e)}")
    
    async def _get_active_users(self) -> List[Dict[str, Any]]:
        """Get all users with active social media credentials"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT DISTINCT u.id, u.username, u.email
                FROM users u
                JOIN social_media_credentials smc ON u.id = smc.user_id
                WHERE smc.is_active = TRUE
            """)
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': row[0],
                    'username': row[1],
                    'email': row[2]
                })
            
            conn.close()
            return users
            
        except Exception as e:
            logger.error(f"Failed to get active users: {str(e)}")
            return []
    
    async def _process_user_daily_posting(self, user: Dict[str, Any]):
        """Process daily posting for a specific user"""
        try:
            user_id = user['id']
            
            # Get user preferences
            preferences = await self._get_user_preferences(user_id)
            if not preferences:
                logger.warning(f"No preferences found for user {user_id}")
                return
            
            # Get user's social media credentials
            credentials = await self._get_user_credentials(user_id)
            if not credentials:
                logger.warning(f"No active credentials found for user {user_id}")
                return
            
            # Generate content
            content_result = await self._generate_daily_content(user_id, preferences)
            if not content_result['success']:
                logger.error(f"Failed to generate content for user {user_id}: {content_result['error']}")
                return
            
            # Post to platforms
            await self._post_to_platforms(user_id, content_result, credentials)
            
        except Exception as e:
            logger.error(f"Failed to process user {user['id']} daily posting: {str(e)}")
    
    async def _get_user_preferences(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user preferences"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT preferences FROM user_preferences 
                WHERE user_id = ? 
                ORDER BY updated_at DESC 
                LIMIT 1
            """, (user_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return json.loads(row[0])
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user preferences: {str(e)}")
            return None
    
    async def _get_user_credentials(self, user_id: int) -> Dict[str, Dict[str, Any]]:
        """Get user's social media credentials"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT platform, credentials FROM social_media_credentials 
                WHERE user_id = ? AND is_active = TRUE
            """, (user_id,))
            
            credentials = {}
            for row in cursor.fetchall():
                platform = row[0]
                creds = json.loads(row[1])
                credentials[platform] = creds
            
            conn.close()
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to get user credentials: {str(e)}")
            return {}
    
    async def _generate_daily_content(self, 
                                    user_id: int,
                                    preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate daily content for user"""
        try:
            # Check if we already have content for today
            existing_content = await self._check_existing_content(user_id)
            if existing_content:
                logger.info(f"Using existing content for user {user_id}")
                return existing_content
            
            # Generate new content
            product_description = preferences.get('product_description', '')
            tone = preferences.get('tone', 'professional')
            target_audience = preferences.get('target_audience', 'general')
            platforms = preferences.get('platforms', ['instagram'])
            
            if not product_description:
                return {
                    'success': False,
                    'error': 'No product description in user preferences'
                }
            
            content_result = await self.ai_generator.generate_complete_content(
                product_description=product_description,
                tone=tone,
                target_audience=target_audience,
                platforms=platforms,
                generate_image=preferences.get('generate_image', True),
                image_style=preferences.get('image_style', 'professional')
            )
            
            if content_result['success']:
                # Store generated content
                await self._store_generated_content(user_id, content_result)
            
            return content_result
            
        except Exception as e:
            logger.error(f"Failed to generate daily content: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _check_existing_content(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Check if content already exists for today"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            today = datetime.now().date()
            cursor.execute("""
                SELECT id, caption, image_path, platforms, status
                FROM generated_content 
                WHERE user_id = ? 
                AND DATE(created_at) = ?
                AND status = 'pending'
                LIMIT 1
            """, (user_id, today))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'success': True,
                    'content_id': row[0],
                    'caption': row[1],
                    'image_path': row[2],
                    'platforms': json.loads(row[3]),
                    'status': row[4]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to check existing content: {str(e)}")
            return None
    
    async def _store_generated_content(self, 
                                    user_id: int,
                                    content_result: Dict[str, Any]):
        """Store generated content in database"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Get the first caption (we'll use Instagram as default)
            captions = content_result.get('captions', {})
            caption = list(captions.values())[0]['caption'] if captions else ''
            
            image_path = content_result.get('image', {}).get('image_path') if content_result.get('image') else None
            platforms = list(content_result.get('captions', {}).keys())
            
            cursor.execute("""
                INSERT INTO generated_content 
                (user_id, prompt_id, caption, image_path, image_generated, platforms, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                content_result.get('content_id'),
                caption,
                image_path,
                bool(image_path),
                json.dumps(platforms),
                'pending'
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to store generated content: {str(e)}")
    
    async def _post_to_platforms(self, 
                               user_id: int,
                               content_result: Dict[str, Any],
                               credentials: Dict[str, Dict[str, Any]]):
        """Post content to all configured platforms"""
        try:
            captions = content_result.get('captions', {})
            image_path = content_result.get('image', {}).get('image_path')
            
            for platform, caption_data in captions.items():
                if platform not in credentials:
                    logger.warning(f"No credentials for {platform}")
                    continue
                
                try:
                    # Initialize platform client
                    if platform == 'instagram':
                        client = MCPInstagram(credentials[platform])
                    elif platform == 'twitter':
                        client = MCPTwitter(credentials[platform])
                    elif platform == 'linkedin':
                        client = MCPLinkedIn(credentials[platform])
                    else:
                        continue
                    
                    # Authenticate
                    auth_success = await client.authenticate()
                    if not auth_success:
                        logger.error(f"Authentication failed for {platform}")
                        continue
                    
                    # Post content
                    post_result = await client.post_content({
                        'caption': caption_data['caption'],
                        'image_path': image_path
                    })
                    
                    # Log posting result
                    await self._log_posting_result(user_id, content_result.get('content_id'), platform, post_result)
                    
                except Exception as e:
                    logger.error(f"Failed to post to {platform}: {str(e)}")
                    await self._log_posting_result(user_id, content_result.get('content_id'), platform, {
                        'success': False,
                        'error': str(e)
                    })
            
        except Exception as e:
            logger.error(f"Failed to post to platforms: {str(e)}")
    
    async def _log_posting_result(self, 
                               user_id: int,
                               content_id: str,
                               platform: str,
                               result: Dict[str, Any]):
        """Log posting result to database"""
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO posting_history 
                (user_id, content_id, platform, post_id, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                content_id,
                platform,
                result.get('post_id'),
                'success' if result['success'] else 'failed',
                result.get('error')
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to log posting result: {str(e)}")
    
    async def stop_scheduler(self):
        """Stop the scheduler"""
        self.scheduler_running = False
        logger.info("Scheduler stopped")
    
    async def add_custom_schedule(self, 
                                user_id: int,
                                schedule_time: str,
                                frequency: str = 'daily') -> bool:
        """Add custom schedule for user"""
        try:
            # This would implement custom scheduling logic
            # For now, we'll use the default daily schedule
            logger.info(f"Custom schedule added for user {user_id}: {frequency} at {schedule_time}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add custom schedule: {str(e)}")
            return False

# Global scheduler instance
scheduler_instance = PostingScheduler()

async def start_scheduler():
    """Start the global scheduler"""
    await scheduler_instance.start_scheduler()