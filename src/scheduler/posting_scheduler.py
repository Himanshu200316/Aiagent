"""
Automated posting scheduler for daily ad posting.
"""

import asyncio
import schedule
import time
from datetime import datetime, timedelta
from typing import List, Optional
import os

from src.config.settings import settings
from src.ai.content_generator import ContentGenerator
from src.mcp.social_media_manager import SocialMediaManager
from src.storage.prompt_manager import PromptManager
from src.models.schemas import AdRequirements, Platform, Tone

class PostingScheduler:
    """Automated posting scheduler."""
    
    def __init__(self):
        self.is_running = False
        self.scheduler_task = None
        self.content_generator = None
        self.social_media_manager = None
        self.prompt_manager = None
        
        # Default posting configuration
        self.posting_time = settings.default_post_time
        self.timezone = settings.timezone
        self.platforms = [Platform.INSTAGRAM, Platform.TWITTER, Platform.LINKEDIN]
        
        # Load user configuration
        self._load_configuration()
    
    def _load_configuration(self):
        """Load posting configuration from file."""
        config_path = "./data/posting_config.json"
        
        if os.path.exists(config_path):
            try:
                import json
                with open(config_path, "r") as f:
                    config = json.load(f)
                
                self.posting_time = config.get("time", self.posting_time)
                self.timezone = config.get("timezone", self.timezone)
                self.platforms = [Platform(p) for p in config.get("platforms", [p.value for p in self.platforms])]
                
            except Exception as e:
                print(f"Error loading configuration: {e}")
    
    async def start(self):
        """Start the posting scheduler."""
        if self.is_running:
            return
        
        print(f"🕐 Starting posting scheduler - Daily at {self.posting_time}")
        
        # Initialize components
        self.content_generator = ContentGenerator()
        await self.content_generator.initialize()
        
        self.social_media_manager = SocialMediaManager()
        self.prompt_manager = PromptManager()
        
        # Schedule daily posting
        schedule.every().day.at(self.posting_time).do(self._daily_posting_job)
        
        # Start scheduler loop
        self.is_running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        
        print("✅ Posting scheduler started successfully")
    
    async def stop(self):
        """Stop the posting scheduler."""
        if not self.is_running:
            return
        
        print("🛑 Stopping posting scheduler...")
        
        self.is_running = False
        
        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass
        
        print("✅ Posting scheduler stopped")
    
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self.is_running:
            try:
                schedule.run_pending()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                print(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)
    
    def _daily_posting_job(self):
        """Daily posting job - runs in a separate thread."""
        asyncio.create_task(self._post_daily_content())
    
    async def _post_daily_content(self):
        """Post daily content to all configured platforms."""
        try:
            print(f"📅 Starting daily posting at {datetime.now()}")
            
            # Generate content for today
            content = await self._generate_daily_content()
            
            if not content:
                print("❌ No content generated for today")
                return
            
            # Post to all platforms
            results = []
            for platform in self.platforms:
                try:
                    result = await self.social_media_manager.post_content(
                        platform, content, "feed"
                    )
                    results.append({
                        "platform": platform.value,
                        "success": result["success"],
                        "error": result.get("error")
                    })
                    
                    if result["success"]:
                        print(f"✅ Posted to {platform.value}")
                    else:
                        print(f"❌ Failed to post to {platform.value}: {result.get('error')}")
                        
                except Exception as e:
                    print(f"❌ Error posting to {platform.value}: {e}")
                    results.append({
                        "platform": platform.value,
                        "success": False,
                        "error": str(e)
                    })
            
            # Log the posting results
            await self._log_daily_posting(content, results)
            
            print(f"📊 Daily posting completed: {sum(1 for r in results if r['success'])}/{len(results)} successful")
            
        except Exception as e:
            print(f"❌ Error in daily posting: {e}")
    
    async def _generate_daily_content(self) -> Optional[object]:
        """Generate content for daily posting."""
        try:
            # For now, we'll use a simple default content
            # In a real implementation, this could:
            # - Pull from a content calendar
            # - Use user preferences
            # - Generate based on trending topics
            # - Use stored product information
            
            # Check if we have any stored product information
            product_info = await self._get_daily_product_info()
            
            if not product_info:
                print("⚠️ No product information available for daily posting")
                return None
            
            # Create ad requirements
            requirements = AdRequirements(
                product_description=product_info["description"],
                tone=Tone.PROFESSIONAL,
                target_audience=product_info.get("target_audience", "general audience"),
                platforms=self.platforms
            )
            
            # Generate content
            content = await self.content_generator.generate_ad_content(requirements)
            
            # Store the prompt to prevent duplicates
            await self.prompt_manager.store_prompt(
                requirements.product_description,
                requirements.tone,
                requirements.target_audience,
                content.caption
            )
            
            return content
            
        except Exception as e:
            print(f"❌ Error generating daily content: {e}")
            return None
    
    async def _get_daily_product_info(self) -> Optional[dict]:
        """Get product information for daily posting."""
        # This is a placeholder - in a real implementation, this would:
        # - Load from a database
        # - Use user-configured products
        # - Pull from external APIs
        # - Use content calendars
        
        # For now, return a default product
        return {
            "description": "Discover our amazing products and services!",
            "target_audience": "general audience",
            "call_to_action": "Learn more today!"
        }
    
    async def _log_daily_posting(self, content, results):
        """Log daily posting results."""
        try:
            log_entry = {
                "date": datetime.now().isoformat(),
                "content_id": id(content),
                "platforms": [r["platform"] for r in results],
                "successful": [r["platform"] for r in results if r["success"]],
                "failed": [r["platform"] for r in results if not r["success"]],
                "errors": [r["error"] for r in results if r["error"]]
            }
            
            log_path = "./data/logs"
            os.makedirs(log_path, exist_ok=True)
            
            import json
            with open(f"{log_path}/daily_posting_log.jsonl", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
                
        except Exception as e:
            print(f"Error logging daily posting: {e}")
    
    async def update_schedule(self, time: str, platforms: List[Platform]):
        """Update posting schedule."""
        try:
            self.posting_time = time
            self.platforms = platforms
            
            # Save configuration
            config = {
                "time": time,
                "timezone": self.timezone,
                "platforms": [p.value for p in platforms],
                "updated_at": datetime.now().isoformat()
            }
            
            os.makedirs("./data", exist_ok=True)
            import json
            with open("./data/posting_config.json", "w") as f:
                json.dump(config, f, indent=2)
            
            # Restart scheduler with new settings
            await self.stop()
            await self.start()
            
            print(f"✅ Schedule updated: Daily at {time} to {[p.value for p in platforms]}")
            
        except Exception as e:
            print(f"❌ Error updating schedule: {e}")
    
    def get_status(self) -> dict:
        """Get scheduler status."""
        return {
            "is_running": self.is_running,
            "posting_time": self.posting_time,
            "timezone": self.timezone,
            "platforms": [p.value for p in self.platforms],
            "next_run": schedule.next_run()
        }