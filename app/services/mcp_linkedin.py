"""
MCP module for LinkedIn posting
"""
import requests
import json
from typing import Dict, Any, List
from app.services.mcp_base import MCPBase
from app.core.logging import get_logger

logger = get_logger('linkedin')

class MCPLinkedIn(MCPBase):
    """LinkedIn MCP implementation"""
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__(credentials)
        self.client_id = credentials.get('client_id')
        self.client_secret = credentials.get('client_secret')
        self.access_token = credentials.get('access_token')
        self.base_url = "https://api.linkedin.com/v2"
    
    def get_required_credentials(self) -> List[str]:
        return ['client_id', 'client_secret', 'access_token']
    
    async def authenticate(self) -> bool:
        """Authenticate with LinkedIn API"""
        try:
            url = f"{self.base_url}/people/~"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                self.log_activity('authentication', {
                    'status': 'success',
                    'user_id': user_data.get('id')
                })
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
        """Post content to LinkedIn"""
        try:
            caption = content.get('caption', '')
            image_path = content.get('image_path')
            
            # Get user's profile
            profile_data = await self._get_user_profile()
            if not profile_data:
                return {'success': False, 'error': 'Could not get user profile'}
            
            person_urn = profile_data.get('id')
            
            if image_path:
                # Post with image
                return await self._post_with_image(person_urn, caption, image_path)
            else:
                # Post text only
                return await self._post_text_only(person_urn, caption)
                
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
        """Post LinkedIn story"""
        try:
            # LinkedIn Stories API (if available)
            # Note: LinkedIn Stories API availability may vary
            return await self.post_content({
                'image_path': image_path,
                'caption': caption,
                'content_type': 'story'
            })
            
        except Exception as e:
            self.log_activity('post_story', {
                'status': 'error',
                'error': str(e)
            })
            return {'success': False, 'error': str(e)}
    
    async def _get_user_profile(self) -> Dict[str, Any]:
        """Get user's LinkedIn profile"""
        try:
            url = f"{self.base_url}/people/~"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                self.log_activity('get_profile', {
                    'status': 'failed',
                    'error': response.text
                })
                return None
                
        except Exception as e:
            self.log_activity('get_profile', {
                'status': 'error',
                'error': str(e)
            })
            return None
    
    async def _post_text_only(self, person_urn: str, text: str) -> Dict[str, Any]:
        """Post text-only content to LinkedIn"""
        try:
            url = f"{self.base_url}/ugcPosts"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            
            data = {
                "author": f"urn:li:person:{person_urn}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": text
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 201:
                post_data = response.json()
                self.log_activity('post_text', {
                    'status': 'success',
                    'post_id': post_data.get('id')
                })
                return {
                    'success': True,
                    'post_id': post_data.get('id'),
                    'platform': 'linkedin'
                }
            else:
                self.log_activity('post_text', {
                    'status': 'failed',
                    'error': response.text
                })
                return {
                    'success': False,
                    'error': f'Failed to post: {response.text}'
                }
                
        except Exception as e:
            self.log_activity('post_text', {
                'status': 'error',
                'error': str(e)
            })
            return {'success': False, 'error': str(e)}
    
    async def _post_with_image(self, person_urn: str, text: str, image_path: str) -> Dict[str, Any]:
        """Post content with image to LinkedIn"""
        try:
            # Step 1: Upload image
            image_urn = await self._upload_image_to_linkedin(image_path)
            if not image_urn:
                return {'success': False, 'error': 'Failed to upload image'}
            
            # Step 2: Post with image
            url = f"{self.base_url}/ugcPosts"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json',
                'X-Restli-Protocol-Version': '2.0.0'
            }
            
            data = {
                "author": f"urn:li:person:{person_urn}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": text
                        },
                        "shareMediaCategory": "IMAGE",
                        "media": [
                            {
                                "status": "READY",
                                "description": {
                                    "text": text
                                },
                                "media": image_urn,
                                "title": {
                                    "text": "Image Post"
                                }
                            }
                        ]
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 201:
                post_data = response.json()
                self.log_activity('post_with_image', {
                    'status': 'success',
                    'post_id': post_data.get('id')
                })
                return {
                    'success': True,
                    'post_id': post_data.get('id'),
                    'platform': 'linkedin'
                }
            else:
                self.log_activity('post_with_image', {
                    'status': 'failed',
                    'error': response.text
                })
                return {
                    'success': False,
                    'error': f'Failed to post with image: {response.text}'
                }
                
        except Exception as e:
            self.log_activity('post_with_image', {
                'status': 'error',
                'error': str(e)
            })
            return {'success': False, 'error': str(e)}
    
    async def _upload_image_to_linkedin(self, image_path: str) -> str:
        """Upload image to LinkedIn and return URN"""
        try:
            # Step 1: Initialize upload
            url = f"{self.base_url}/assets?action=registerUpload"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            data = {
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner": f"urn:li:person:{await self._get_person_id()}",
                    "serviceRelationships": [
                        {
                            "relationshipType": "OWNER",
                            "identifier": "urn:li:userGeneratedContent"
                        }
                    ]
                }
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 201:
                upload_data = response.json()
                upload_url = upload_data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
                asset_urn = upload_data['value']['asset']
                
                # Step 2: Upload image
                with open(image_path, 'rb') as image_file:
                    upload_response = requests.post(upload_url, files={'file': image_file})
                    
                    if upload_response.status_code == 201:
                        self.log_activity('upload_image', {
                            'status': 'success',
                            'asset_urn': asset_urn
                        })
                        return asset_urn
                    else:
                        self.log_activity('upload_image', {
                            'status': 'failed',
                            'error': upload_response.text
                        })
                        return None
            else:
                self.log_activity('upload_image', {
                    'status': 'failed',
                    'error': response.text
                })
                return None
                
        except Exception as e:
            self.log_activity('upload_image', {
                'status': 'error',
                'error': str(e)
            })
            return None
    
    async def _get_person_id(self) -> str:
        """Get person ID from access token"""
        try:
            url = f"{self.base_url}/people/~"
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                return response.json().get('id')
            else:
                return None
                
        except Exception as e:
            return None