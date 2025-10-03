#!/usr/bin/env python3
"""
User Manager - Handles user credentials, preferences, and authentication
"""

import os
import json
import logging
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import hashlib
import secrets

logger = logging.getLogger(__name__)

class UserManager:
    """Manages user data, credentials, and preferences"""

    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.users_file = self.storage_path / "users.json"
        self.credentials_file = self.storage_path / "credentials.json"
        self.preferences_file = self.storage_path / "preferences.json"

        self._users = {}
        self._credentials = {}
        self._preferences = {}

        self.load_data()

    def load_data(self):
        """Load user data from files"""
        try:
            # Load users
            if self.users_file.exists():
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    self._users = json.load(f)

            # Load credentials
            if self.credentials_file.exists():
                with open(self.credentials_file, 'r', encoding='utf-8') as f:
                    self._credentials = json.load(f)

            # Load preferences
            if self.preferences_file.exists():
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    self._preferences = json.load(f)

        except Exception as e:
            logger.error(f"Error loading user data: {e}")
            self._users = {}
            self._credentials = {}
            self._preferences = {}

    def save_data(self):
        """Save user data to files"""
        try:
            # Save users
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self._users, f, indent=2, ensure_ascii=False)

            # Save credentials (encrypted)
            with open(self.credentials_file, 'w', encoding='utf-8') as f:
                json.dump(self._credentials, f, indent=2, ensure_ascii=False)

            # Save preferences
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(self._preferences, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Error saving user data: {e}")

    def create_user(self, email: str, name: str = None) -> str:
        """
        Create a new user account

        Args:
            email: User email address
            name: User display name

        Returns:
            User ID string
        """
        user_id = str(uuid.uuid4())

        # Check if email already exists
        for uid, user in self._users.items():
            if user.get("email") == email:
                raise ValueError(f"User with email {email} already exists")

        # Create user entry
        user_data = {
            "id": user_id,
            "email": email,
            "name": name or email.split("@")[0],
            "created_at": datetime.now().isoformat(),
            "last_login": None,
            "is_active": True
        }

        self._users[user_id] = user_data

        # Initialize empty preferences
        self._preferences[user_id] = {
            "platforms": {
                "instagram": {"enabled": False, "posting_time": "12:00"},
                "twitter": {"enabled": False, "posting_time": "12:00"},
                "linkedin": {"enabled": False, "posting_time": "12:00"}
            },
            "posting_preferences": {
                "frequency": "daily",
                "auto_post": True,
                "include_stories": True,
                "ai_generation": True
            },
            "content_preferences": {
                "tone": "professional",
                "target_audience": "general",
                "custom_keywords": []
            }
        }

        self.save_data()
        logger.info(f"Created new user: {email} with ID: {user_id}")

        return user_id

    def authenticate_user(self, email: str) -> Optional[str]:
        """
        Authenticate user by email

        Args:
            email: User email address

        Returns:
            User ID if authenticated, None otherwise
        """
        for user_id, user_data in self._users.items():
            if user_data.get("email") == email and user_data.get("is_active"):
                # Update last login
                user_data["last_login"] = datetime.now().isoformat()
                self.save_data()
                return user_id

        return None

    def store_credentials(self, user_id: str, platform: str, credentials: Dict) -> bool:
        """
        Store social media credentials for a user

        Args:
            user_id: User identifier
            platform: Social media platform
            credentials: Platform-specific credentials

        Returns:
            True if stored successfully
        """
        if user_id not in self._users:
            raise ValueError(f"User {user_id} not found")

        # Encrypt sensitive data before storing
        encrypted_credentials = self._encrypt_credentials(credentials)

        # Store credentials
        if user_id not in self._credentials:
            self._credentials[user_id] = {}

        self._credentials[user_id][platform] = {
            "credentials": encrypted_credentials,
            "stored_at": datetime.now().isoformat(),
            "last_used": None
        }

        self.save_data()
        logger.info(f"Stored {platform} credentials for user {user_id}")

        return True

    def get_user_credentials(self, user_id: str, platform: str) -> Optional[Dict]:
        """
        Retrieve user credentials for a platform

        Args:
            user_id: User identifier
            platform: Social media platform

        Returns:
            Decrypted credentials or None if not found
        """
        if user_id not in self._credentials or platform not in self._credentials[user_id]:
            return None

        encrypted_data = self._credentials[user_id][platform]["credentials"]
        credentials = self._decrypt_credentials(encrypted_data)

        # Update last used timestamp
        self._credentials[user_id][platform]["last_used"] = datetime.now().isoformat()
        self.save_data()

        return credentials

    def update_user_preferences(self, user_id: str, preferences: Dict) -> bool:
        """
        Update user preferences

        Args:
            user_id: User identifier
            preferences: Updated preferences dictionary

        Returns:
            True if updated successfully
        """
        if user_id not in self._users:
            raise ValueError(f"User {user_id} not found")

        # Merge with existing preferences
        if user_id in self._preferences:
            self._preferences[user_id].update(preferences)
        else:
            self._preferences[user_id] = preferences

        self.save_data()
        logger.info(f"Updated preferences for user {user_id}")

        return True

    def get_user_preferences(self, user_id: str) -> Dict:
        """
        Get user preferences

        Args:
            user_id: User identifier

        Returns:
            User preferences dictionary
        """
        return self._preferences.get(user_id, {})

    def list_users(self) -> List[Dict]:
        """List all users (without sensitive data)"""
        users = []

        for user_id, user_data in self._users.items():
            if user_data.get("is_active"):
                users.append({
                    "id": user_id,
                    "email": user_data.get("email"),
                    "name": user_data.get("name"),
                    "created_at": user_data.get("created_at"),
                    "last_login": user_data.get("last_login"),
                    "platforms_configured": self._get_configured_platforms(user_id)
                    "preferences": self._preferences.get(user_id, {})
                })

        return users

    def _get_configured_platforms(self, user_id: str) -> List[str]:
        """Get list of platforms configured for a user"""
        if user_id not in self._credentials:
            return []

        return list(self._credentials[user_id].keys())

    def _encrypt_credentials(self, credentials: Dict) -> str:
        """Encrypt credentials (simple implementation - use proper encryption in production)"""
        # In a real implementation, use proper encryption like AES
        # For now, we'll use base64 encoding with a simple salt
        import base64

        credentials_str = json.dumps(credentials, sort_keys=True)
        # Add a simple salt (in production, use proper key management)
        salt = "ai_social_media_agent_salt_2024"

        # Simple obfuscation (NOT secure for production)
        encoded = base64.b64encode((credentials_str + salt).encode()).decode()
        return encoded

    def _decrypt_credentials(self, encrypted_data: str) -> Dict:
        """Decrypt credentials"""
        try:
            import base64

            # Reverse the simple obfuscation
            salt = "ai_social_media_agent_salt_2024"
            decoded = base64.b64decode(encrypted_data.encode()).decode()
            credentials_str = decoded[:-len(salt)]

            return json.loads(credentials_str)

        except Exception as e:
            logger.error(f"Error decrypting credentials: {e}")
            return {}

    def delete_user(self, user_id: str) -> bool:
        """
        Delete a user and all associated data

        Args:
            user_id: User identifier

        Returns:
            True if deleted successfully
        """
        if user_id not in self._users:
            return False

        # Remove user data
        del self._users[user_id]

        # Remove credentials
        if user_id in self._credentials:
            del self._credentials[user_id]

        # Remove preferences
        if user_id in self._preferences:
            del self._preferences[user_id]

        self.save_data()
        logger.info(f"Deleted user {user_id}")

        return True

    def cleanup_inactive_users(self, days: int = 90) -> int:
        """
        Remove users inactive for specified number of days

        Args:
            days: Number of days of inactivity

        Returns:
            Number of users removed
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        users_to_remove = []

        for user_id, user_data in self._users.items():
            last_login = user_data.get("last_login")
            if last_login:
                try:
                    login_date = datetime.fromisoformat(last_login)
                    if login_date < cutoff_date:
                        users_to_remove.append(user_id)
                except ValueError:
                    # Invalid date format, consider as inactive
                    users_to_remove.append(user_id)

        # Remove inactive users
        for user_id in users_to_remove:
            self.delete_user(user_id)

        if users_to_remove:
            logger.info(f"Removed {len(users_to_remove)} inactive users")

        return len(users_to_remove)