"""
MCP module for Instagram posting
"""
import requests
import json
from typing import Dict, Any, List
from app.services.mcp_base import MCPBase
from app.core.logging import get_logger

logger = get_logger('instagram')

class MCPInstagram(MCPBase):
    """Instagram MCP implementation"""
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__(credentials)
        self.base_url = "https://graph.instagram.com"
        self.access_token = credentials.get('access_token')
        self.app_id = credentials.get('app_id')
        self.app_secret = credentials.get('app_secret')
    
    def get_required_credentials(self) -> List[str]:
        return ['access_token', 'app_id', 'app_secret']
    
    async def authenticate(self) -> bool:
        """Authenticate with Instagram API"""
        try:
            url = f"{self.base_url}/me"
            params = {'access_token': self.access_token}
            
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                self.log_activity('authentication', {'status': 'success'})
                return True
            else:
                self.log_activity('authentication', {
                    'status': 'failed',
                    'error': response.text
                })
                return False
                
        except Exception as e:
            self.log_activity('authentication', {
                'status': 'error',
                'error': str(e)
            })
            return False
    
    async def post_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Post content to Instagram feed"""
        try:
            caption = content.get('caption', '')
            image_path = content.get('image_path')
            
            if not image_path:
                return {'success': False, 'error': 'No image provided'}
            
            # Step 1: Create media container
            container_id = await self._create_media_container(image_path, caption)
            if not container_id:
                return {'success': False, 'error': 'Failed to create media container'}
            
            # Step 2: Publish the media
            publish_result = await self._publish_media(container_id)
            
            return publish_result
            
        except Exception as e:
            self.log_activity('post_content', {
                'status': 'error',
                'error': str(e)
            })
            return {'success': False, 'error': str(e)}
    
    async def upload_image(self, image_path: str, caption: str) -> Dict[str, Any]:
        """Upload image with caption (alias for post_content)"""
        return await self.post_content({
            'image_path': image_path,
            'caption': caption
        })
    
    async def post_story(self, image_path: str, caption: str) -> Dict[str, Any]:
        """Post Instagram story"""
        try:
            # Create story media container
            url = f"{self.base_url}/{self.app_id}/media"
            
            with open(image_path, 'rb') as image_file:
                files = {'image': image_file}
                data = {
                    'access_token': self.access_token,
                    'media_type': 'STORIES'
                }
                
                response = requests.post(url, files=files, data=data)
                
                if response.status_code == 200:
                    container_id = response.json().get('id')
                    
                    # Publish the story
                    publish_url = f"{self.base_url}/{self.app_id}/media_publish"
                    publish_data = {
                        'creation_id': container_id,
                        'access_token': self.access_token
                    }
                    
                    publish_response = requests.post(publish_url, data=publish_data)
                    
                    if publish_response.status_code == 200:
                        self.log_activity('post_story', {
                            'status': 'success',
                            'story_id': publish_response.json().get('id')
                        })
                        return {
                            'success': True,
                            'story_id': publish_response.json().get('id'),
                            'platform': 'instagram'
                        }
                    else:
                        return {
                            'success': False,
                            'error': f'Failed to publish story: {publish_response.text}'
                        }
                else:
                    return {
                        'success': False,
                        'error': f'Failed to create story container: {response.text}'
                    }
                    
        except Exception as e:
            self.log_activity('post_story', {
                'status': 'error',
                'error': str(e)
            })
            return {'success': False, 'error': str(e)}
    
    async def _create_media_container(self, image_path: str, caption: str) -> str:
        """Create media container for Instagram post"""
        try:
            url = f"{self.base_url}/{self.app_id}/media"
            
            with open(image_path, 'rb') as image_file:
                files = {'image': image_file}
                data = {
                    'access_token': self.access_token,
                    'caption': caption,
                    'media_type': 'IMAGE'
                }
                
                response = requests.post(url, files=files, data=data)
                
                if response.status_code == 200:
                    container_id = response.json().get('id')
                    self.log_activity('create_container', {
                        'status': 'success',
                        'container_id': container_id
                    })
                    return container_id
                else:
                    self.log_activity('create_container', {
                        'status': 'failed',
                        'error': response.text
                    })
                    return None
                    
        except Exception as e:
            self.log_activity('create_container', {
                'status': 'error',
                'error': str(e)
            })
            return None
    
    async def _publish_media(self, container_id: str) -> Dict[str, Any]:
        """Publish media container"""
        try:
            url = f"{self.base_url}/{self.app_id}/media_publish"
            data = {
                'creation_id': container_id,
                'access_token': self.access_token
            }
            
            response = requests.post(url, data=data)
            
            if response.status_code == 200:
                post_id = response.json().get('id')
                self.log_activity('publish_media', {
                    'status': 'success',
                    'post_id': post_id
                })
                return {
                    'success': True,
                    'post_id': post_id,
                    'platform': 'instagram'
                }
            else:
                self.log_activity('publish_media', {
                    'status': 'failed',
                    'error': response.text
                })
                return {
                    'success': False,
                    'error': f'Failed to publish media: {response.text}'
                }
                
        except Exception as e:
            self.log_activity('publish_media', {
                'status': 'error',
                'error': str(e)
            })
            return {'success': False, 'error': str(e)}