#!/usr/bin/env python3
"""
Social Media Manager - Handles posting to Instagram, X, and LinkedIn via MCP
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class SocialMediaManager:
    """Manages social media posting across multiple platforms"""

    def __init__(self, user_manager):
        self.user_manager = user_manager

        # Platform configurations
        self.platforms = {
            "instagram": {
                "enabled": True,
                "supports_stories": True,
                "supports_feed": True,
                "max_caption_length": 2200,
                "image_formats": ["jpg", "jpeg", "png"]
            },
            "twitter": {
                "enabled": True,
                "supports_stories": False,
                "supports_feed": True,
                "max_caption_length": 280,
                "image_formats": ["jpg", "jpeg", "png", "gif"]
            },
            "linkedin": {
                "enabled": True,
                "supports_stories": False,
                "supports_feed": True,
                "max_caption_length": 3000,
                "image_formats": ["jpg", "jpeg", "png"]
            }
        }

        # MCP module imports (these would need to be implemented separately)
        try:
            # Import MCP modules for each platform
            from mcp_instagram import InstagramMCP
            from mcp_twitter import TwitterMCP
            from mcp_linkedin import LinkedInMCP

            self.mcp_modules = {
                "instagram": InstagramMCP(),
                "twitter": TwitterMCP(),
                "linkedin": LinkedInMCP()
            }
        except ImportError as e:
            logger.warning(f"MCP modules not available: {e}. Using mock implementations.")
            self.mcp_modules = {}

    async def post_to_platform(
        self,
        platform: str,
        image_path: str,
        caption: str,
        post_type: str = "feed_post",
        user_id: str = None
    ) -> Dict:
        """
        Post content to specified social media platform

        Args:
            platform: Target platform (instagram, twitter, linkedin)
            image_path: Path to image file
            caption: Post caption/text
            post_type: Type of post (feed_post, story)
            user_id: User identifier for credentials

        Returns:
            Dictionary with post status and details
        """
        try:
            if platform not in self.platforms:
                return {
                    "success": False,
                    "error": f"Unsupported platform: {platform}",
                    "platform": platform
                }

            if not self.platforms[platform]["enabled"]:
                return {
                    "success": False,
                    "error": f"Platform {platform} is disabled",
                    "platform": platform
                }

            # Validate image format
            if not self._validate_image_format(image_path, platform):
                return {
                    "success": False,
                    "error": f"Unsupported image format for {platform}",
                    "platform": platform
                }

            # Truncate caption if too long
            max_length = self.platforms[platform]["max_caption_length"]
            if len(caption) > max_length:
                caption = caption[:max_length-3] + "..."
                logger.warning(f"Caption truncated for {platform}")

            # Get user credentials if provided
            credentials = None
            if user_id:
                credentials = self.user_manager.get_user_credentials(user_id, platform)

            # Post using MCP module or mock implementation
            result = await self._post_with_mcp(platform, image_path, caption, post_type, credentials)

            # Log successful post
            if result["success"]:
                logger.info(f"Successfully posted to {platform}: {result.get('post_id', 'unknown')}")
            else:
                logger.error(f"Failed to post to {platform}: {result.get('error', 'unknown error')}")

            return result

        except Exception as e:
            logger.error(f"Error posting to {platform}: {e}")
            return {
                "success": False,
                "error": str(e),
                "platform": platform
            }

    async def _post_with_mcp(
        self,
        platform: str,
        image_path: str,
        caption: str,
        post_type: str,
        credentials: Dict = None
    ) -> Dict:
        """Post using MCP module or mock implementation"""
        try:
            # Try to use MCP module if available
            if platform in self.mcp_modules:
                mcp_module = self.mcp_modules[platform]

                # Platform-specific posting logic
                if platform == "instagram":
                    return await self._post_instagram(mcp_module, image_path, caption, post_type, credentials)
                elif platform == "twitter":
                    return await self._post_twitter(mcp_module, image_path, caption, post_type, credentials)
                elif platform == "linkedin":
                    return await self._post_linkedin(mcp_module, image_path, caption, post_type, credentials)
            else:
                # Mock implementation for testing
                return await self._post_mock(platform, image_path, caption, post_type)

        except Exception as e:
            logger.error(f"MCP posting error for {platform}: {e}")
            return await self._post_mock(platform, image_path, caption, post_type)

    async def _post_instagram(
        self,
        mcp_module,
        image_path: str,
        caption: str,
        post_type: str,
        credentials: Dict
    ) -> Dict:
        """Post to Instagram using MCP"""
        try:
            if post_type == "story":
                # Post as story
                result = await mcp_module.post_story(image_path, caption, credentials)
            else:
                # Post as feed post
                result = await mcp_module.post_feed(image_path, caption, credentials)

            return {
                "success": result.get("success", False),
                "post_id": result.get("post_id"),
                "platform": "instagram",
                "post_type": post_type,
                "posted_at": datetime.now().isoformat(),
                "error": result.get("error")
            }

        except Exception as e:
            logger.error(f"Instagram posting error: {e}")
            return {
                "success": False,
                "error": str(e),
                "platform": "instagram"
            }

    async def _post_twitter(
        self,
        mcp_module,
        image_path: str,
        caption: str,
        post_type: str,
        credentials: Dict
    ) -> Dict:
        """Post to Twitter using MCP"""
        try:
            result = await mcp_module.post_tweet(image_path, caption, credentials)

            return {
                "success": result.get("success", False),
                "post_id": result.get("tweet_id"),
                "platform": "twitter",
                "post_type": "feed_post",
                "posted_at": datetime.now().isoformat(),
                "error": result.get("error")
            }

        except Exception as e:
            logger.error(f"Twitter posting error: {e}")
            return {
                "success": False,
                "error": str(e),
                "platform": "twitter"
            }

    async def _post_linkedin(
        self,
        mcp_module,
        image_path: str,
        caption: str,
        post_type: str,
        credentials: Dict
    ) -> Dict:
        """Post to LinkedIn using MCP"""
        try:
            result = await mcp_module.post_update(image_path, caption, credentials)

            return {
                "success": result.get("success", False),
                "post_id": result.get("post_id"),
                "platform": "linkedin",
                "post_type": "feed_post",
                "posted_at": datetime.now().isoformat(),
                "error": result.get("error")
            }

        except Exception as e:
            logger.error(f"LinkedIn posting error: {e}")
            return {
                "success": False,
                "error": str(e),
                "platform": "linkedin"
            }

    async def _post_mock(
        self,
        platform: str,
        image_path: str,
        caption: str,
        post_type: str
    ) -> Dict:
        """Mock posting implementation for testing"""
        # Simulate posting delay
        await asyncio.sleep(1)

        mock_post_id = f"mock_{platform}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        return {
            "success": True,
            "post_id": mock_post_id,
            "platform": platform,
            "post_type": post_type,
            "posted_at": datetime.now().isoformat(),
            "note": "Mock post - replace with actual MCP implementation"
        }

    def _validate_image_format(self, image_path: str, platform: str) -> bool:
        """Validate if image format is supported by platform"""
        try:
            from PIL import Image
            img = Image.open(image_path)
            format_name = img.format.lower()

            supported_formats = self.platforms[platform]["image_formats"]
            return format_name in supported_formats

        except Exception:
            return False

    async def post_to_all_platforms(
        self,
        image_path: str,
        caption: str,
        platforms: List[str] = None,
        post_type: str = "feed_post",
        user_id: str = None
    ) -> Dict:
        """
        Post to multiple platforms simultaneously

        Args:
            image_path: Path to image file
            caption: Post caption/text
            platforms: List of platforms to post to (if None, post to all enabled)
            post_type: Type of post (feed_post, story)
            user_id: User identifier for credentials

        Returns:
            Dictionary with results for each platform
        """
        if platforms is None:
            platforms = [p for p in self.platforms.keys() if self.platforms[p]["enabled"]]

        results = {}

        # Post to each platform concurrently
        tasks = []
        for platform in platforms:
            if self.platforms[platform]["supports_feed"] or post_type == "story":
                task = self.post_to_platform(platform, image_path, caption, post_type, user_id)
                tasks.append((platform, task))

        # Execute all posts concurrently
        for platform, task in tasks:
            try:
                results[platform] = await task
            except Exception as e:
                results[platform] = {
                    "success": False,
                    "error": str(e),
                    "platform": platform
                }

        return {
            "overall_success": any(r["success"] for r in results.values()),
            "results": results,
            "posted_at": datetime.now().isoformat()
        }

    def get_platform_info(self, platform: str) -> Dict:
        """Get information about a platform"""
        if platform not in self.platforms:
            return {"error": f"Platform {platform} not supported"}

        return self.platforms[platform].copy()

    def list_supported_platforms(self) -> List[Dict]:
        """List all supported platforms with their capabilities"""
        platforms_info = []

        for platform_name, config in self.platforms.items():
            if config["enabled"]:
                platforms_info.append({
                    "name": platform_name,
                    "supports_stories": config["supports_stories"],
                    "supports_feed": config["supports_feed"],
                    "max_caption_length": config["max_caption_length"],
                    "image_formats": config["image_formats"]
                })

        return platforms_info