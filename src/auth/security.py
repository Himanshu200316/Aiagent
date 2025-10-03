"""
Security and Authentication Module
Handles user authentication and secure credential storage
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from cryptography.fernet import Fernet
import base64

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT settings
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Encryption for credentials
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # Generate a key for development (in production, use a secure key)
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    logger.warning("Using generated encryption key. Set ENCRYPTION_KEY in production!")

fernet = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)

class SecurityManager:
    """Handles authentication and credential encryption"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def encrypt_credentials(credentials: Dict[str, Any]) -> str:
        """Encrypt social media credentials"""
        try:
            import json
            credentials_json = json.dumps(credentials)
            encrypted_data = fernet.encrypt(credentials_json.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt credentials: {e}")
            raise
    
    @staticmethod
    def decrypt_credentials(encrypted_credentials: str) -> Dict[str, Any]:
        """Decrypt social media credentials"""
        try:
            import json
            encrypted_data = base64.b64decode(encrypted_credentials.encode())
            decrypted_data = fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {e}")
            raise
    
    @staticmethod
    def validate_social_credentials(platform: str, credentials: Dict[str, Any]) -> bool:
        """Validate social media credentials format"""
        required_fields = {
            'instagram': ['username', 'password'],
            'twitter': ['api_key', 'api_secret', 'access_token', 'access_token_secret'],
            'linkedin': ['access_token']
        }
        
        if platform not in required_fields:
            return False
        
        required = required_fields[platform]
        return all(field in credentials and credentials[field] for field in required)

class CredentialManager:
    """Manages secure storage and retrieval of social media credentials"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.security = SecurityManager()
    
    async def store_credentials(self, user_id: str, platform: str, 
                              credentials: Dict[str, Any]) -> bool:
        """Store encrypted credentials for a user and platform"""
        try:
            # Validate credentials format
            if not self.security.validate_social_credentials(platform, credentials):
                logger.error(f"Invalid credentials format for {platform}")
                return False
            
            # Encrypt credentials
            encrypted_creds = self.security.encrypt_credentials(credentials)
            
            # Store in database (placeholder - would use actual database)
            # This would integrate with your user management system
            await self._store_encrypted_credentials(user_id, platform, encrypted_creds)
            
            logger.info(f"Credentials stored for user {user_id} on {platform}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store credentials: {e}")
            return False
    
    async def get_credentials(self, user_id: str, platform: str) -> Optional[Dict[str, Any]]:
        """Retrieve and decrypt credentials for a user and platform"""
        try:
            # Get encrypted credentials from database
            encrypted_creds = await self._get_encrypted_credentials(user_id, platform)
            
            if not encrypted_creds:
                return None
            
            # Decrypt credentials
            credentials = self.security.decrypt_credentials(encrypted_creds)
            
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to get credentials: {e}")
            return None
    
    async def update_credentials(self, user_id: str, platform: str, 
                               credentials: Dict[str, Any]) -> bool:
        """Update existing credentials"""
        return await self.store_credentials(user_id, platform, credentials)
    
    async def delete_credentials(self, user_id: str, platform: str) -> bool:
        """Delete credentials for a user and platform"""
        try:
            await self._delete_encrypted_credentials(user_id, platform)
            logger.info(f"Credentials deleted for user {user_id} on {platform}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete credentials: {e}")
            return False
    
    async def list_user_platforms(self, user_id: str) -> List[str]:
        """List platforms for which user has stored credentials"""
        try:
            return await self._get_user_platforms(user_id)
        except Exception as e:
            logger.error(f"Failed to list user platforms: {e}")
            return []
    
    # Database integration methods (placeholder implementations)
    async def _store_encrypted_credentials(self, user_id: str, platform: str, encrypted_creds: str):
        """Store encrypted credentials in database"""
        # This would integrate with your actual database
        # For now, store in a simple file-based system
        import os
        import json
        
        creds_dir = "data/credentials"
        os.makedirs(creds_dir, exist_ok=True)
        
        user_file = os.path.join(creds_dir, f"{user_id}.json")
        
        # Load existing credentials
        user_creds = {}
        if os.path.exists(user_file):
            with open(user_file, 'r') as f:
                user_creds = json.load(f)
        
        # Update with new credentials
        user_creds[platform] = {
            'encrypted_data': encrypted_creds,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Save back to file
        with open(user_file, 'w') as f:
            json.dump(user_creds, f, indent=2)
    
    async def _get_encrypted_credentials(self, user_id: str, platform: str) -> Optional[str]:
        """Get encrypted credentials from database"""
        import os
        import json
        
        user_file = os.path.join("data/credentials", f"{user_id}.json")
        
        if not os.path.exists(user_file):
            return None
        
        with open(user_file, 'r') as f:
            user_creds = json.load(f)
        
        platform_data = user_creds.get(platform)
        if platform_data:
            return platform_data.get('encrypted_data')
        
        return None
    
    async def _delete_encrypted_credentials(self, user_id: str, platform: str):
        """Delete encrypted credentials from database"""
        import os
        import json
        
        user_file = os.path.join("data/credentials", f"{user_id}.json")
        
        if not os.path.exists(user_file):
            return
        
        with open(user_file, 'r') as f:
            user_creds = json.load(f)
        
        if platform in user_creds:
            del user_creds[platform]
            
            # Save back to file
            with open(user_file, 'w') as f:
                json.dump(user_creds, f, indent=2)
    
    async def _get_user_platforms(self, user_id: str) -> List[str]:
        """Get list of platforms for user"""
        import os
        import json
        
        user_file = os.path.join("data/credentials", f"{user_id}.json")
        
        if not os.path.exists(user_file):
            return []
        
        with open(user_file, 'r') as f:
            user_creds = json.load(f)
        
        return list(user_creds.keys())