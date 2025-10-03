"""
File-based Storage Manager
Handles prompt storage, history tracking, and content management
"""
import json
import os
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger('storage_manager')

class StorageManager:
    """Manages file-based storage for prompts and content"""
    
    def __init__(self):
        self.prompts_dir = Path(settings.prompts_dir)
        self.data_dir = Path(settings.data_dir)
        self.images_dir = Path(settings.images_dir)
        self.logs_dir = Path(settings.logs_dir)
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.prompts_dir,
            self.data_dir,
            self.images_dir,
            self.logs_dir,
            self.prompts_dir / "history",
            self.prompts_dir / "templates",
            self.data_dir / "backups"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def store_prompt(self, 
                    user_id: int,
                    prompt_data: Dict[str, Any]) -> str:
        """Store a prompt with unique hash"""
        try:
            # Generate unique prompt hash
            prompt_hash = self._generate_prompt_hash(prompt_data)
            
            # Create prompt file
            prompt_file = self.prompts_dir / f"prompt_{user_id}_{prompt_hash}.json"
            
            prompt_record = {
                'prompt_id': f"prompt_{user_id}_{prompt_hash}",
                'user_id': user_id,
                'prompt_hash': prompt_hash,
                'prompt_data': prompt_data,
                'created_at': datetime.now().isoformat(),
                'used_count': 0,
                'last_used': None
            }
            
            with open(prompt_file, 'w') as f:
                json.dump(prompt_record, f, indent=2)
            
            logger.info(f"Stored prompt: {prompt_hash}")
            return prompt_hash
            
        except Exception as e:
            logger.error(f"Failed to store prompt: {str(e)}")
            raise
    
    def get_prompt_by_hash(self, prompt_hash: str) -> Optional[Dict[str, Any]]:
        """Get prompt by hash"""
        try:
            # Search for prompt file
            for prompt_file in self.prompts_dir.glob(f"*_{prompt_hash}.json"):
                with open(prompt_file, 'r') as f:
                    return json.load(f)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get prompt by hash: {str(e)}")
            return None
    
    def check_prompt_exists(self, prompt_data: Dict[str, Any]) -> bool:
        """Check if prompt already exists"""
        try:
            prompt_hash = self._generate_prompt_hash(prompt_data)
            
            # Check if file exists
            for prompt_file in self.prompts_dir.glob(f"*_{prompt_hash}.json"):
                if prompt_file.exists():
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check prompt existence: {str(e)}")
            return False
    
    def update_prompt_usage(self, prompt_hash: str):
        """Update prompt usage statistics"""
        try:
            prompt_record = self.get_prompt_by_hash(prompt_hash)
            if not prompt_record:
                return
            
            prompt_record['used_count'] += 1
            prompt_record['last_used'] = datetime.now().isoformat()
            
            # Find and update the file
            for prompt_file in self.prompts_dir.glob(f"*_{prompt_hash}.json"):
                with open(prompt_file, 'w') as f:
                    json.dump(prompt_record, f, indent=2)
                break
                
        except Exception as e:
            logger.error(f"Failed to update prompt usage: {str(e)}")
    
    def store_content_history(self, 
                            user_id: int,
                            content_data: Dict[str, Any]) -> str:
        """Store content generation history"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            history_file = self.prompts_dir / "history" / f"content_{user_id}_{timestamp}.json"
            
            history_record = {
                'content_id': content_data.get('content_id'),
                'user_id': user_id,
                'content_data': content_data,
                'created_at': datetime.now().isoformat(),
                'status': 'generated'
            }
            
            with open(history_file, 'w') as f:
                json.dump(history_record, f, indent=2)
            
            logger.info(f"Stored content history: {history_file.name}")
            return history_file.name
            
        except Exception as e:
            logger.error(f"Failed to store content history: {str(e)}")
            raise
    
    def get_user_content_history(self, 
                               user_id: int,
                               limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's content generation history"""
        try:
            history_files = list((self.prompts_dir / "history").glob(f"content_{user_id}_*.json"))
            history_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            history = []
            for history_file in history_files[:limit]:
                with open(history_file, 'r') as f:
                    history.append(json.load(f))
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get user content history: {str(e)}")
            return []
    
    def store_posting_history(self, 
                            user_id: int,
                            posting_data: Dict[str, Any]) -> str:
        """Store posting history"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            history_file = self.prompts_dir / "history" / f"posting_{user_id}_{timestamp}.json"
            
            history_record = {
                'posting_id': posting_data.get('posting_id'),
                'user_id': user_id,
                'posting_data': posting_data,
                'created_at': datetime.now().isoformat(),
                'status': 'posted'
            }
            
            with open(history_file, 'w') as f:
                json.dump(history_record, f, indent=2)
            
            logger.info(f"Stored posting history: {history_file.name}")
            return history_file.name
            
        except Exception as e:
            logger.error(f"Failed to store posting history: {str(e)}")
            raise
    
    def get_posting_history(self, 
                          user_id: int,
                          platform: Optional[str] = None,
                          limit: int = 50) -> List[Dict[str, Any]]:
        """Get posting history"""
        try:
            history_files = list((self.prompts_dir / "history").glob(f"posting_{user_id}_*.json"))
            history_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            history = []
            for history_file in history_files[:limit]:
                with open(history_file, 'r') as f:
                    record = json.load(f)
                    
                    # Filter by platform if specified
                    if platform:
                        posting_data = record.get('posting_data', {})
                        if posting_data.get('platform') != platform:
                            continue
                    
                    history.append(record)
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get posting history: {str(e)}")
            return []
    
    def store_user_preferences(self, 
                             user_id: int,
                             preferences: Dict[str, Any]) -> str:
        """Store user preferences"""
        try:
            preferences_file = self.data_dir / f"preferences_{user_id}.json"
            
            preferences_record = {
                'user_id': user_id,
                'preferences': preferences,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            with open(preferences_file, 'w') as f:
                json.dump(preferences_record, f, indent=2)
            
            logger.info(f"Stored user preferences: {user_id}")
            return preferences_file.name
            
        except Exception as e:
            logger.error(f"Failed to store user preferences: {str(e)}")
            raise
    
    def get_user_preferences(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user preferences"""
        try:
            preferences_file = self.data_dir / f"preferences_{user_id}.json"
            
            if preferences_file.exists():
                with open(preferences_file, 'r') as f:
                    return json.load(f)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get user preferences: {str(e)}")
            return None
    
    def store_credentials(self, 
                        user_id: int,
                        platform: str,
                        credentials: Dict[str, Any]) -> str:
        """Store encrypted credentials"""
        try:
            credentials_file = self.data_dir / f"credentials_{user_id}_{platform}.json"
            
            credentials_record = {
                'user_id': user_id,
                'platform': platform,
                'credentials': credentials,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            with open(credentials_file, 'w') as f:
                json.dump(credentials_record, f, indent=2)
            
            logger.info(f"Stored credentials for {platform}: {user_id}")
            return credentials_file.name
            
        except Exception as e:
            logger.error(f"Failed to store credentials: {str(e)}")
            raise
    
    def get_credentials(self, user_id: int, platform: str) -> Optional[Dict[str, Any]]:
        """Get stored credentials"""
        try:
            credentials_file = self.data_dir / f"credentials_{user_id}_{platform}.json"
            
            if credentials_file.exists():
                with open(credentials_file, 'r') as f:
                    return json.load(f)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get credentials: {str(e)}")
            return None
    
    def create_backup(self) -> str:
        """Create backup of all data"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.data_dir / "backups" / f"backup_{timestamp}"
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy all data files
            import shutil
            shutil.copytree(self.prompts_dir, backup_dir / "prompts")
            shutil.copytree(self.data_dir / "preferences_*.json", backup_dir / "preferences")
            shutil.copytree(self.data_dir / "credentials_*.json", backup_dir / "credentials")
            
            logger.info(f"Created backup: {backup_dir}")
            return str(backup_dir)
            
        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            raise
    
    def cleanup_old_files(self, days: int = 30):
        """Clean up old files"""
        try:
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            
            # Clean up old history files
            for history_file in (self.prompts_dir / "history").glob("*.json"):
                if history_file.stat().st_mtime < cutoff_date:
                    history_file.unlink()
            
            # Clean up old backups
            for backup_dir in (self.data_dir / "backups").glob("backup_*"):
                if backup_dir.stat().st_mtime < cutoff_date:
                    import shutil
                    shutil.rmtree(backup_dir)
            
            logger.info(f"Cleaned up files older than {days} days")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {str(e)}")
    
    def _generate_prompt_hash(self, prompt_data: Dict[str, Any]) -> str:
        """Generate hash for prompt data"""
        # Create a normalized string from prompt data
        normalized_data = {
            'product_description': prompt_data.get('product_description', ''),
            'tone': prompt_data.get('tone', ''),
            'target_audience': prompt_data.get('target_audience', ''),
            'platforms': sorted(prompt_data.get('platforms', []))
        }
        
        data_string = json.dumps(normalized_data, sort_keys=True)
        return hashlib.md5(data_string.encode()).hexdigest()

# Global storage manager instance
storage_manager = StorageManager()