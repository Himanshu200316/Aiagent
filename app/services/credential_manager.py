"""
Credential Management Service
Handles secure storage and encryption of social media credentials
"""
import json
import os
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
from datetime import datetime
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger('credential_manager')

class CredentialManager:
    """Manages secure storage and encryption of credentials"""
    
    def __init__(self):
        self.master_key = self._get_or_create_master_key()
        self.cipher_suite = Fernet(self.master_key)
    
    def _get_or_create_master_key(self) -> bytes:
        """Get or create master encryption key"""
        try:
            key_file = os.path.join(settings.data_dir, ".master_key")
            
            if os.path.exists(key_file):
                with open(key_file, 'rb') as f:
                    return f.read()
            else:
                # Generate new master key
                key = Fernet.generate_key()
                
                # Ensure data directory exists
                os.makedirs(settings.data_dir, exist_ok=True)
                
                # Save key with restricted permissions
                with open(key_file, 'wb') as f:
                    f.write(key)
                
                # Set restrictive permissions (owner read/write only)
                os.chmod(key_file, 0o600)
                
                logger.info("Generated new master encryption key")
                return key
                
        except Exception as e:
            logger.error(f"Failed to get/create master key: {str(e)}")
            raise
    
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """Encrypt credentials dictionary"""
        try:
            # Convert to JSON string
            credentials_json = json.dumps(credentials)
            
            # Encrypt
            encrypted_data = self.cipher_suite.encrypt(credentials_json.encode())
            
            # Encode as base64 for storage
            encrypted_b64 = base64.b64encode(encrypted_data).decode()
            
            return encrypted_b64
            
        except Exception as e:
            logger.error(f"Failed to encrypt credentials: {str(e)}")
            raise
    
    def decrypt_credentials(self, encrypted_credentials: str) -> Dict[str, Any]:
        """Decrypt credentials"""
        try:
            # Decode from base64
            encrypted_data = base64.b64decode(encrypted_credentials.encode())
            
            # Decrypt
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            
            # Parse JSON
            credentials = json.loads(decrypted_data.decode())
            
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to decrypt credentials: {str(e)}")
            raise
    
    def store_credentials(self, 
                        user_id: int,
                        platform: str,
                        credentials: Dict[str, Any]) -> str:
        """Store encrypted credentials"""
        try:
            # Encrypt credentials
            encrypted_creds = self.encrypt_credentials(credentials)
            
            # Create credential record
            credential_record = {
                'user_id': user_id,
                'platform': platform,
                'encrypted_credentials': encrypted_creds,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Store in database
            from app.core.database import db_manager
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            # Check if credentials already exist
            cursor.execute(
                "SELECT id FROM social_media_credentials WHERE user_id = ? AND platform = ?",
                (user_id, platform)
            )
            
            if cursor.fetchone():
                # Update existing credentials
                cursor.execute(
                    "UPDATE social_media_credentials SET credentials = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND platform = ?",
                    (json.dumps(credential_record), user_id, platform)
                )
            else:
                # Insert new credentials
                cursor.execute(
                    "INSERT INTO social_media_credentials (user_id, platform, credentials) VALUES (?, ?, ?)",
                    (user_id, platform, json.dumps(credential_record))
                )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Credentials stored securely for {platform}: {user_id}")
            return f"credentials_{user_id}_{platform}"
            
        except Exception as e:
            logger.error(f"Failed to store credentials: {str(e)}")
            raise
    
    def retrieve_credentials(self, user_id: int, platform: str) -> Optional[Dict[str, Any]]:
        """Retrieve and decrypt credentials"""
        try:
            from app.core.database import db_manager
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT credentials FROM social_media_credentials WHERE user_id = ? AND platform = ? AND is_active = TRUE",
                (user_id, platform)
            )
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            # Parse credential record
            credential_record = json.loads(row[0])
            
            # Decrypt credentials
            decrypted_creds = self.decrypt_credentials(credential_record['encrypted_credentials'])
            
            return decrypted_creds
            
        except Exception as e:
            logger.error(f"Failed to retrieve credentials: {str(e)}")
            return None
    
    def delete_credentials(self, user_id: int, platform: str) -> bool:
        """Delete credentials (mark as inactive)"""
        try:
            from app.core.database import db_manager
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE social_media_credentials SET is_active = FALSE, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND platform = ?",
                (user_id, platform)
            )
            
            conn.commit()
            conn.close()
            
            logger.info(f"Credentials deleted for {platform}: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete credentials: {str(e)}")
            return False
    
    def list_user_credentials(self, user_id: int) -> Dict[str, Dict[str, Any]]:
        """List all credentials for user (without sensitive data)"""
        try:
            from app.core.database import db_manager
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT platform, credentials, created_at, updated_at FROM social_media_credentials WHERE user_id = ? AND is_active = TRUE",
                (user_id,)
            )
            
            credentials_info = {}
            for row in cursor.fetchall():
                platform = row[0]
                credential_record = json.loads(row[1])
                
                credentials_info[platform] = {
                    'platform': platform,
                    'created_at': credential_record['created_at'],
                    'updated_at': credential_record['updated_at'],
                    'has_credentials': True
                }
            
            conn.close()
            return credentials_info
            
        except Exception as e:
            logger.error(f"Failed to list user credentials: {str(e)}")
            return {}
    
    def validate_credential_format(self, platform: str, credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Validate credential format for platform"""
        try:
            required_fields = {
                'instagram': ['access_token', 'app_id', 'app_secret'],
                'twitter': ['api_key', 'api_secret', 'access_token', 'access_token_secret'],
                'linkedin': ['client_id', 'client_secret', 'access_token']
            }
            
            if platform not in required_fields:
                return {
                    'valid': False,
                    'error': f'Unsupported platform: {platform}'
                }
            
            missing_fields = []
            for field in required_fields[platform]:
                if field not in credentials or not credentials[field]:
                    missing_fields.append(field)
            
            if missing_fields:
                return {
                    'valid': False,
                    'error': f'Missing required fields: {", ".join(missing_fields)}'
                }
            
            return {
                'valid': True,
                'message': 'Credentials format is valid'
            }
            
        except Exception as e:
            logger.error(f"Failed to validate credential format: {str(e)}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def rotate_master_key(self) -> bool:
        """Rotate master encryption key (requires re-encryption of all credentials)"""
        try:
            # This is a complex operation that would require:
            # 1. Generate new master key
            # 2. Decrypt all existing credentials with old key
            # 3. Re-encrypt with new key
            # 4. Update all credential records
            
            logger.warning("Master key rotation is not implemented yet")
            return False
            
        except Exception as e:
            logger.error(f"Failed to rotate master key: {str(e)}")
            return False
    
    def backup_credentials(self, user_id: int) -> str:
        """Create encrypted backup of user credentials"""
        try:
            credentials_info = self.list_user_credentials(user_id)
            
            backup_data = {
                'user_id': user_id,
                'platforms': credentials_info,
                'backup_created_at': datetime.now().isoformat(),
                'backup_version': '1.0'
            }
            
            # Encrypt backup
            encrypted_backup = self.encrypt_credentials(backup_data)
            
            # Save backup file
            backup_filename = f"credentials_backup_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.enc"
            backup_path = os.path.join(settings.data_dir, "backups", backup_filename)
            
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            
            with open(backup_path, 'w') as f:
                f.write(encrypted_backup)
            
            logger.info(f"Credentials backup created: {backup_filename}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to backup credentials: {str(e)}")
            raise

# Global credential manager instance
credential_manager = CredentialManager()