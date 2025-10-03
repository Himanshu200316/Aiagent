#!/usr/bin/env python3
"""
Prompt Manager - Handles storage and retrieval of ad prompts to avoid repetition
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import hashlib
import random

logger = logging.getLogger(__name__)

class PromptManager:
    """Manages ad prompts to ensure no repetition and track usage"""

    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.prompts_file = self.storage_path / "prompts.json"
        self.usage_file = self.storage_path / "usage_history.json"
        self._prompts = {}
        self._usage_history = {}
        self.load_data()

    def load_data(self):
        """Load prompts and usage history from files"""
        try:
            # Load prompts
            if self.prompts_file.exists():
                with open(self.prompts_file, 'r', encoding='utf-8') as f:
                    self._prompts = json.load(f)

            # Load usage history
            if self.usage_file.exists():
                with open(self.usage_file, 'r', encoding='utf-8') as f:
                    self._usage_history = json.load(f)

        except Exception as e:
            logger.error(f"Error loading prompt data: {e}")
            self._prompts = {}
            self._usage_history = {}

    def save_data(self):
        """Save prompts and usage history to files"""
        try:
            # Save prompts
            with open(self.prompts_file, 'w', encoding='utf-8') as f:
                json.dump(self._prompts, f, indent=2, ensure_ascii=False)

            # Save usage history
            with open(self.usage_file, 'w', encoding='utf-8') as f:
                json.dump(self._usage_history, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Error saving prompt data: {e}")

    def _generate_prompt_hash(self, prompt_data: Dict) -> str:
        """Generate a unique hash for a prompt"""
        # Create a string representation of the prompt data
        prompt_str = json.dumps(prompt_data, sort_keys=True)
        return hashlib.sha256(prompt_str.encode()).hexdigest()[:16]

    def add_prompt(self, prompt_data: Dict, platform: str, ad_type: str) -> str:
        """
        Add a new prompt to the storage

        Args:
            prompt_data: Dictionary containing prompt information
            platform: Social media platform (instagram, twitter, linkedin)
            ad_type: Type of ad (feed_post, story, etc.)

        Returns:
            Unique prompt ID
        """
        prompt_hash = self._generate_prompt_hash(prompt_data)

        # Check if prompt already exists
        if prompt_hash in self._prompts:
            logger.info(f"Prompt already exists with hash: {prompt_hash}")
            return prompt_hash

        # Create prompt entry
        prompt_entry = {
            "id": prompt_hash,
            "data": prompt_data,
            "platform": platform,
            "ad_type": ad_type,
            "created_at": datetime.now().isoformat(),
            "usage_count": 0,
            "last_used": None
        }

        self._prompts[prompt_hash] = prompt_entry

        # Initialize usage tracking
        self._usage_history[prompt_hash] = {
            "platform": platform,
            "usage_dates": []
        }

        self.save_data()
        logger.info(f"Added new prompt with hash: {prompt_hash}")

        return prompt_hash

    def get_unused_prompt(self, platform: str, ad_type: str) -> Optional[Dict]:
        """
        Get an unused prompt for the specified platform and ad type

        Args:
            platform: Social media platform
            ad_type: Type of ad

        Returns:
            Prompt data dictionary or None if no unused prompts available
        """
        available_prompts = []

        for prompt_id, prompt_entry in self._prompts.items():
            if (prompt_entry["platform"] == platform and
                prompt_entry["ad_type"] == ad_type):

                # Check if prompt was used recently (within last 7 days)
                if prompt_entry["last_used"]:
                    last_used = datetime.fromisoformat(prompt_entry["last_used"])
                    if datetime.now() - last_used < timedelta(days=7):
                        continue  # Skip recently used prompts

                available_prompts.append(prompt_entry)

        if not available_prompts:
            logger.warning(f"No unused prompts available for {platform} {ad_type}")
            return None

        # Select a random prompt from available ones
        selected_prompt = random.choice(available_prompts)
        return selected_prompt

    def mark_prompt_used(self, prompt_id: str, platform: str):
        """
        Mark a prompt as used

        Args:
            prompt_id: Unique prompt identifier
            platform: Social media platform where it was used
        """
        if prompt_id not in self._prompts:
            logger.error(f"Prompt {prompt_id} not found")
            return

        # Update prompt usage count and last used time
        self._prompts[prompt_id]["usage_count"] += 1
        self._prompts[prompt_id]["last_used"] = datetime.now().isoformat()

        # Update usage history
        if prompt_id not in self._usage_history:
            self._usage_history[prompt_id] = {
                "platform": platform,
                "usage_dates": []
            }

        self._usage_history[prompt_id]["usage_dates"].append({
            "platform": platform,
            "used_at": datetime.now().isoformat()
        })

        self.save_data()
        logger.info(f"Marked prompt {prompt_id} as used on {platform}")

    def get_prompt_stats(self) -> Dict:
        """Get statistics about prompt usage"""
        total_prompts = len(self._prompts)
        used_prompts = sum(1 for p in self._prompts.values() if p["usage_count"] > 0)

        platform_stats = {}
        for prompt in self._prompts.values():
            platform = prompt["platform"]
            if platform not in platform_stats:
                platform_stats[platform] = {"total": 0, "used": 0}
            platform_stats[platform]["total"] += 1
            if prompt["usage_count"] > 0:
                platform_stats[platform]["used"] += 1

        return {
            "total_prompts": total_prompts,
            "used_prompts": used_prompts,
            "unused_prompts": total_prompts - used_prompts,
            "platform_stats": platform_stats
        }

    def cleanup_old_prompts(self, days: int = 30):
        """
        Remove prompts that haven't been used for specified number of days

        Args:
            days: Number of days after which to remove unused prompts
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        prompts_to_remove = []

        for prompt_id, prompt_entry in self._prompts.items():
            # Keep prompts that have been used recently or never used
            if prompt_entry["usage_count"] == 0:
                created_at = datetime.fromisoformat(prompt_entry["created_at"])
                if created_at < cutoff_date:
                    prompts_to_remove.append(prompt_id)

        for prompt_id in prompts_to_remove:
            del self._prompts[prompt_id]
            if prompt_id in self._usage_history:
                del self._usage_history[prompt_id]

        if prompts_to_remove:
            self.save_data()
            logger.info(f"Removed {len(prompts_to_remove)} old unused prompts")

        return len(prompts_to_remove)