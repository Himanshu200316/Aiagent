"""
Base MCP (Model Context Protocol) module for social media platforms
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import json
import hashlib
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MCPBase(ABC):
    """Base class for MCP social media modules"""
    
    def __init__(self, credentials: Dict[str, Any]):
        self.credentials = credentials
        self.platform_name = self.__class__.__name__.lower()
        self.logger = logging.getLogger(f'mcp.{self.platform_name}')
    
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the platform"""
        pass
    
    @abstractmethod
    async def post_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Post content to the platform"""
        pass
    
    @abstractmethod
    async def upload_image(self, image_path: str, caption: str) -> Dict[str, Any]:
        """Upload image with caption"""
        pass
    
    @abstractmethod
    async def post_story(self, image_path: str, caption: str) -> Dict[str, Any]:
        """Post story content"""
        pass
    
    def generate_content_hash(self, content: str) -> str:
        """Generate hash for content to avoid duplicates"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def log_activity(self, action: str, details: Dict[str, Any]):
        """Log platform activity"""
        self.logger.info(f"{self.platform_name} - {action}: {details}")
    
    def validate_credentials(self) -> bool:
        """Validate required credentials"""
        required_fields = self.get_required_credentials()
        return all(field in self.credentials for field in required_fields)
    
    @abstractmethod
    def get_required_credentials(self) -> List[str]:
        """Get list of required credential fields"""
        pass