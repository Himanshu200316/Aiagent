from typing import Callable, Dict, Any, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import time

from .storage import Storage
from .generation.caption_generator import generate_caption
from .generation.image_generator import generate_image
from .utils.prompt_utils import build_prompt_key
from .posters.instagram import InstagramPoster
from .posters.twitter import TwitterPoster
from .posters.linkedin import LinkedInPoster


class PostScheduler:
    def __init__(self, storage: Storage) -> None:
        self.storage = storage
        self.scheduler = BackgroundScheduler(timezone="UTC")
        self.scheduler.start()

    def schedule_user(self, user_id: str) -> None:
        sched = self.storage.get_schedule(user_id)
        tz = pytz.timezone(sched.get("timezone", "UTC"))
        hour = int(sched.get("hour", 0))
        minute = int(sched.get("minute", 0))
        job_id = f"post-{user_id}"
        # Remove existing job
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)
        trigger = CronTrigger(hour=hour, minute=minute, timezone=tz)
        self.scheduler.add_job(self._post_for_user, trigger=trigger, id=job_id, args=[user_id])

    def _post_for_user(self, user_id: str) -> None:
        # Default platforms if not specified: all three
        platforms = ["instagram", "twitter", "linkedin"]
        product_description = "Daily scheduled promotion"
        tone = "persuasive"
        target_audience = "general audience"
        self.generate_and_post(user_id, product_description, tone, target_audience, platforms, instagram_post_type="feed")

    def generate_and_post(
        self,
        user_id: str,
        product_description: str,
        tone: str,
        target_audience: str,
        platforms: list,
        instagram_post_type: str = "feed",
        use_uploaded_image_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        caption = generate_caption(product_description, tone, target_audience)
        if use_uploaded_image_path:
            image_path = use_uploaded_image_path
        else:
            img_bytes = generate_image(product_description, tone, target_audience)
            image_path = self.storage.save_image(user_id, img_bytes)
        results: Dict[str, Any] = {}
        prompt_key = build_prompt_key(product_description, tone, target_audience, ",".join(platforms))
        if self.storage.prompt_exists(user_id, prompt_key):
            # Ensure uniqueness by appending a timestamp-based suffix
            prompt_key = f"{prompt_key}-{int(time.time())}"
        self.storage.save_prompt(user_id, prompt_key, {
            "product_description": product_description,
            "tone": tone,
            "target_audience": target_audience,
            "caption": caption,
            "image_path": image_path,
        })
        # Post
        for platform in platforms:
            try:
                cred = self.storage.load_credentials(user_id, platform)
                if not cred:
                    results[platform] = {"error": "missing_credentials"}
                    continue
                if platform == "instagram":
                    poster = InstagramPoster(cred)
                    if instagram_post_type == "story":
                        post_id = poster.post_story(image_path)
                    else:
                        post_id = poster.post_feed(image_path, caption)
                elif platform == "twitter":
                    poster = TwitterPoster(cred)
                    post_id = poster.post(image_path, caption)
                elif platform == "linkedin":
                    # LinkedIn requires public URL for image unless using upload API; we fallback to caption-only if no URL
                    poster = LinkedInPoster(cred)
                    # In this scaffold we cannot host the local image; so post text-only as fallback
                    post_id = poster.post(image_url="https://example.com/placeholder.png", caption=caption)
                else:
                    results[platform] = {"error": "unknown_platform"}
                    continue
                results[platform] = {"post_id": post_id}
            except Exception as e:
                results[platform] = {"error": str(e)}
        self.storage.append_history(user_id, {
            "prompt_key": prompt_key,
            "caption": caption,
            "image_path": image_path,
            "platforms": results,
        })
        return {"caption": caption, "image_path": image_path, "prompt_key": prompt_key, "results": results}
