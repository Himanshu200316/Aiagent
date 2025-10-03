#!/usr/bin/env python3
"""
Posting Scheduler - Handles automated daily posting at specified times
"""

import os
import logging
import asyncio
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)

class PostingScheduler:
    """Schedules and manages automated social media posting"""

    def __init__(self, social_media_manager, prompt_manager):
        self.social_media_manager = social_media_manager
        self.prompt_manager = prompt_manager
        self.is_running = False
        self.scheduler_task = None
        self.posting_history = []

        # Load posting history
        self.history_file = "/app/data/scheduler_history.json"
        self.load_history()

    def load_history(self):
        """Load posting history from file"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.posting_history = json.load(f)
        except Exception as e:
            logger.error(f"Error loading posting history: {e}")
            self.posting_history = []

    def save_history(self):
        """Save posting history to file"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.posting_history[-100:], f, indent=2)  # Keep last 100 entries
        except Exception as e:
            logger.error(f"Error saving posting history: {e}")

    def start_daily_scheduler(self, hour: int = 0, minute: int = 0):
        """
        Start the daily posting scheduler

        Args:
            hour: Hour for daily posting (0-23)
            minute: Minute for daily posting (0-59)
        """
        if self.is_running:
            logger.warning("Scheduler is already running")
            return

        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop(hour, minute))
        logger.info(f"Started daily scheduler for {hour:02d}:{minute:02d}")

    def stop_scheduler(self):
        """Stop the daily posting scheduler"""
        if not self.is_running:
            return

        self.is_running = False
        if self.scheduler_task:
            self.scheduler_task.cancel()
        logger.info("Stopped daily scheduler")

    async def _scheduler_loop(self, hour: int, minute: int):
        """Main scheduler loop"""
        while self.is_running:
            try:
                # Calculate time until next posting
                now = datetime.now()
                target_time = time(hour, minute)

                # If it's already past the target time today, schedule for tomorrow
                if (now.time() > target_time):
                    next_post = datetime.combine(now.date() + timedelta(days=1), target_time)
                else:
                    next_post = datetime.combine(now.date(), target_time)

                # Wait until next posting time
                wait_seconds = (next_post - now).total_seconds()
                logger.info(f"Next posting scheduled for: {next_post}")

                await asyncio.sleep(wait_seconds)

                # Execute daily posting
                if self.is_running:  # Check if still running after sleep
                    await self._execute_daily_posting()

            except asyncio.CancelledError:
                logger.info("Scheduler task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                # Wait 1 hour before retrying on error
                await asyncio.sleep(3600)

    async def _execute_daily_posting(self):
        """Execute the daily posting routine"""
        try:
            logger.info("Starting daily posting routine...")

            # Get all active users
            active_users = self._get_active_users()

            if not active_users:
                logger.info("No active users found for posting")
                return

            total_posts = 0
            successful_posts = 0

            for user_id in active_users:
                try:
                    user_result = await self._post_for_user(user_id)
                    total_posts += user_result["total_posts"]
                    successful_posts += user_result["successful_posts"]

                    # Add small delay between users to avoid rate limits
                    await asyncio.sleep(5)

                except Exception as e:
                    logger.error(f"Error posting for user {user_id}: {e}")

            # Log results
            logger.info(f"Daily posting completed: {successful_posts}/{total_posts} successful")

            # Record in history
            self.posting_history.append({
                "timestamp": datetime.now().isoformat(),
                "total_posts": total_posts,
                "successful_posts": successful_posts,
                "users_processed": len(active_users)
            })
            self.save_history()

        except Exception as e:
            logger.error(f"Error in daily posting execution: {e}")

    def _get_active_users(self) -> List[str]:
        """Get list of users who should receive daily posts"""
        # This would typically query the user manager for users with auto_post enabled
        # For now, return a placeholder
        return ["demo_user"]  # Replace with actual user retrieval logic

    async def _post_for_user(self, user_id: str) -> Dict:
        """Post content for a specific user"""
        try:
            # This would typically:
            # 1. Get user's preferences and enabled platforms
            # 2. Generate or retrieve content based on preferences
            # 3. Post to each enabled platform
            # 4. Record the posting results

            # For demo purposes, simulate posting
            user_posts = {
                "total_posts": 3,  # One for each platform
                "successful_posts": 3,
                "platforms": ["instagram", "twitter", "linkedin"],
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Posted for user {user_id}: {user_posts['successful_posts']}/{user_posts['total_posts']} successful")
            return user_posts

        except Exception as e:
            logger.error(f"Error posting for user {user_id}: {e}")
            return {
                "total_posts": 0,
                "successful_posts": 0,
                "error": str(e),
                "user_id": user_id
            }

    def schedule_immediate_post(self, user_id: str, platforms: List[str] = None) -> str:
        """
        Schedule an immediate post for testing or manual triggering

        Args:
            user_id: User identifier
            platforms: List of platforms to post to

        Returns:
            Task ID for the scheduled post
        """
        task_id = f"immediate_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Create task for immediate posting
        asyncio.create_task(self._execute_immediate_post(user_id, platforms, task_id))

        logger.info(f"Scheduled immediate post {task_id} for user {user_id}")
        return task_id

    async def _execute_immediate_post(self, user_id: str, platforms: List[str], task_id: str):
        """Execute immediate posting for a user"""
        try:
            logger.info(f"Executing immediate post {task_id} for user {user_id}")

            # Simulate immediate posting
            await asyncio.sleep(2)  # Simulate processing time

            result = await self._post_for_user(user_id)

            logger.info(f"Immediate post {task_id} completed: {result['successful_posts']}/{result['total_posts']}")

        except Exception as e:
            logger.error(f"Error in immediate post {task_id}: {e}")

    def get_scheduler_status(self) -> Dict:
        """Get current scheduler status"""
        return {
            "is_running": self.is_running,
            "next_post_time": self._get_next_post_time(),
            "posting_history": self.posting_history[-10:],  # Last 10 posts
            "total_posts_today": self._get_posts_today(),
            "active_users": len(self._get_active_users())
        }

    def _get_next_post_time(self) -> Optional[str]:
        """Get the next scheduled posting time"""
        if not self.is_running:
            return None

        now = datetime.now()
        target_time = time(0, 0)  # 12:00 AM

        if now.time() > target_time:
            next_post = datetime.combine(now.date() + timedelta(days=1), target_time)
        else:
            next_post = datetime.combine(now.date(), target_time)

        return next_post.isoformat()

    def _get_posts_today(self) -> int:
        """Get number of posts made today"""
        today = datetime.now().date()
        today_posts = 0

        for entry in self.posting_history:
            try:
                post_date = datetime.fromisoformat(entry["timestamp"]).date()
                if post_date == today:
                    today_posts += entry.get("successful_posts", 0)
            except:
                pass

        return today_posts

    def get_posting_stats(self) -> Dict:
        """Get posting statistics"""
        if not self.posting_history:
            return {"message": "No posting history available"}

        total_posts = sum(entry.get("successful_posts", 0) for entry in self.posting_history)
        total_attempts = sum(entry.get("total_posts", 0) for entry in self.posting_history)
        success_rate = (total_posts / total_attempts * 100) if total_attempts > 0 else 0

        # Posts by platform (if available in history)
        platform_stats = {}
        for entry in self.posting_history:
            if "platforms" in entry:
                for platform in entry["platforms"]:
                    platform_stats[platform] = platform_stats.get(platform, 0) + 1

        return {
            "total_posts": total_posts,
            "total_attempts": total_attempts,
            "success_rate": round(success_rate, 2),
            "total_scheduled_posts": len(self.posting_history),
            "platform_stats": platform_stats,
            "last_post": self.posting_history[-1]["timestamp"] if self.posting_history else None
        }