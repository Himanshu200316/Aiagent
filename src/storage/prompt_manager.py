"""
Prompt management system to prevent duplicate content generation.
"""

import json
import os
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime

class PromptManager:
    """Manages prompts and prevents duplicate content generation."""
    
    def __init__(self):
        self.storage_path = "./data"
        self.prompts_file = f"{self.storage_path}/prompts.json"
        self.history_file = f"{self.storage_path}/posting_history.jsonl"
        
        # Ensure storage directories exist
        os.makedirs(self.storage_path, exist_ok=True)
        
        # Initialize prompts file if it doesn't exist
        if not os.path.exists(self.prompts_file):
            self._initialize_prompts_file()
    
    def _initialize_prompts_file(self):
        """Initialize the prompts storage file."""
        with open(self.prompts_file, "w") as f:
            json.dump({
                "prompts": [],
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "total_prompts": 0
                }
            }, f, indent=2)
    
    def _generate_prompt_hash(self, product_description: str, tone: str, target_audience: str) -> str:
        """Generate a hash for the prompt to detect duplicates."""
        prompt_string = f"{product_description.lower().strip()}|{tone.lower()}|{target_audience.lower().strip()}"
        return hashlib.md5(prompt_string.encode()).hexdigest()
    
    async def store_prompt(self, product_description: str, tone: str, target_audience: str, generated_caption: str) -> bool:
        """Store a generated prompt to prevent duplicates."""
        try:
            prompt_hash = self._generate_prompt_hash(product_description, tone, target_audience)
            
            # Load existing prompts
            with open(self.prompts_file, "r") as f:
                data = json.load(f)
            
            # Check if prompt already exists
            existing_prompts = [p for p in data["prompts"] if p["hash"] == prompt_hash]
            if existing_prompts:
                print(f"Duplicate prompt detected: {prompt_hash}")
                return False
            
            # Add new prompt
            new_prompt = {
                "hash": prompt_hash,
                "product_description": product_description,
                "tone": tone,
                "target_audience": target_audience,
                "generated_caption": generated_caption,
                "created_at": datetime.now().isoformat(),
                "used_count": 0
            }
            
            data["prompts"].append(new_prompt)
            data["metadata"]["total_prompts"] = len(data["prompts"])
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # Save updated prompts
            with open(self.prompts_file, "w") as f:
                json.dump(data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error storing prompt: {e}")
            return False
    
    async def check_duplicate(self, product_description: str, tone: str, target_audience: str) -> bool:
        """Check if a prompt would be a duplicate."""
        try:
            prompt_hash = self._generate_prompt_hash(product_description, tone, target_audience)
            
            with open(self.prompts_file, "r") as f:
                data = json.load(f)
            
            existing_prompts = [p for p in data["prompts"] if p["hash"] == prompt_hash]
            return len(existing_prompts) > 0
            
        except Exception as e:
            print(f"Error checking duplicate: {e}")
            return False
    
    async def get_prompt_suggestions(self, product_description: str) -> List[Dict[str, Any]]:
        """Get similar prompts for inspiration."""
        try:
            with open(self.prompts_file, "r") as f:
                data = json.load(f)
            
            # Simple similarity check based on keywords
            product_words = set(product_description.lower().split())
            suggestions = []
            
            for prompt in data["prompts"]:
                prompt_words = set(prompt["product_description"].lower().split())
                similarity = len(product_words.intersection(prompt_words)) / len(product_words.union(prompt_words))
                
                if similarity > 0.3:  # 30% similarity threshold
                    suggestions.append({
                        "product_description": prompt["product_description"],
                        "tone": prompt["tone"],
                        "target_audience": prompt["target_audience"],
                        "similarity": similarity,
                        "created_at": prompt["created_at"]
                    })
            
            # Sort by similarity and return top 5
            suggestions.sort(key=lambda x: x["similarity"], reverse=True)
            return suggestions[:5]
            
        except Exception as e:
            print(f"Error getting prompt suggestions: {e}")
            return []
    
    async def log_posting(self, prompt_hash: str, platforms: List[str], success: bool, error_message: Optional[str] = None):
        """Log a posting attempt."""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "prompt_hash": prompt_hash,
                "platforms": platforms,
                "success": success,
                "error_message": error_message
            }
            
            with open(self.history_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
            
            # Update usage count in prompts file
            await self._update_usage_count(prompt_hash)
            
        except Exception as e:
            print(f"Error logging posting: {e}")
    
    async def _update_usage_count(self, prompt_hash: str):
        """Update the usage count for a prompt."""
        try:
            with open(self.prompts_file, "r") as f:
                data = json.load(f)
            
            for prompt in data["prompts"]:
                if prompt["hash"] == prompt_hash:
                    prompt["used_count"] += 1
                    break
            
            with open(self.prompts_file, "w") as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"Error updating usage count: {e}")
    
    async def get_posting_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get posting history."""
        try:
            history = []
            
            if os.path.exists(self.history_file):
                with open(self.history_file, "r") as f:
                    lines = f.readlines()
                
                # Get last N lines
                recent_lines = lines[-limit:] if len(lines) > limit else lines
                
                for line in recent_lines:
                    if line.strip():
                        history.append(json.loads(line))
            
            return history
            
        except Exception as e:
            print(f"Error getting posting history: {e}")
            return []
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get prompt and posting statistics."""
        try:
            stats = {
                "total_prompts": 0,
                "total_postings": 0,
                "successful_postings": 0,
                "failed_postings": 0,
                "most_used_tone": None,
                "platform_usage": {}
            }
            
            # Load prompts data
            with open(self.prompts_file, "r") as f:
                prompts_data = json.load(f)
            
            stats["total_prompts"] = len(prompts_data["prompts"])
            
            # Analyze tones
            tone_counts = {}
            for prompt in prompts_data["prompts"]:
                tone = prompt["tone"]
                tone_counts[tone] = tone_counts.get(tone, 0) + 1
            
            if tone_counts:
                stats["most_used_tone"] = max(tone_counts, key=tone_counts.get)
            
            # Load posting history
            history = await self.get_posting_history(1000)  # Get more history for stats
            
            stats["total_postings"] = len(history)
            
            for entry in history:
                if entry["success"]:
                    stats["successful_postings"] += 1
                else:
                    stats["failed_postings"] += 1
                
                # Count platform usage
                for platform in entry["platforms"]:
                    stats["platform_usage"][platform] = stats["platform_usage"].get(platform, 0) + 1
            
            return stats
            
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}