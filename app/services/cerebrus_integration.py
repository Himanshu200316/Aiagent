"""
Cerebrus API Integration Service
Handles conversational interface for user interaction
"""
import httpx
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger('cerebrus_integration')

class CerebrusIntegration:
    """Cerebrus API integration for conversational interface"""
    
    def __init__(self):
        self.api_key = settings.cerebrus_api_key
        self.api_url = settings.cerebrus_api_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def send_message(self, 
                          user_id: str,
                          message: str,
                          context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send message to Cerebrus API"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'user_id': user_id,
                'message': message,
                'context': context or {},
                'timestamp': datetime.now().isoformat()
            }
            
            response = await self.client.post(
                f"{self.api_url}/chat",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Cerebrus response for user {user_id}: {result.get('response', '')[:100]}...")
                return {
                    'success': True,
                    'response': result.get('response', ''),
                    'intent': result.get('intent', 'unknown'),
                    'entities': result.get('entities', {}),
                    'confidence': result.get('confidence', 0.0)
                }
            else:
                logger.error(f"Cerebrus API error: {response.status_code} - {response.text}")
                return {
                    'success': False,
                    'error': f'Cerebrus API error: {response.status_code}'
                }
                
        except Exception as e:
            logger.error(f"Failed to send message to Cerebrus: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def handle_user_input(self, 
                              user_id: str,
                              user_input: str,
                              session_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user input and determine appropriate response"""
        try:
            # Analyze user input with Cerebrus
            cerebrus_response = await self.send_message(user_id, user_input, session_context)
            
            if not cerebrus_response['success']:
                return cerebrus_response
            
            intent = cerebrus_response.get('intent', 'unknown')
            entities = cerebrus_response.get('entities', {})
            
            # Route based on intent
            if intent == 'setup_credentials':
                return await self._handle_credential_setup(user_id, entities, session_context)
            elif intent == 'create_ad_content':
                return await self._handle_content_creation(user_id, entities, session_context)
            elif intent == 'upload_image':
                return await self._handle_image_upload(user_id, entities, session_context)
            elif intent == 'schedule_posting':
                return await self._handle_scheduling(user_id, entities, session_context)
            elif intent == 'view_history':
                return await self._handle_history_request(user_id, entities, session_context)
            elif intent == 'help':
                return await self._handle_help_request(user_id, session_context)
            else:
                return {
                    'success': True,
                    'response': cerebrus_response['response'],
                    'intent': intent,
                    'action_required': 'clarification'
                }
                
        except Exception as e:
            logger.error(f"Failed to handle user input: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _handle_credential_setup(self, 
                                     user_id: str,
                                     entities: Dict[str, Any],
                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle social media credential setup"""
        platform = entities.get('platform', 'unknown')
        
        if platform == 'instagram':
            return {
                'success': True,
                'response': "I'll help you set up Instagram credentials. Please provide:\n1. Instagram Access Token\n2. App ID\n3. App Secret\n\nYou can get these from the Instagram Basic Display API.",
                'intent': 'setup_credentials',
                'action_required': 'credential_input',
                'platform': 'instagram',
                'required_fields': ['access_token', 'app_id', 'app_secret']
            }
        elif platform == 'twitter':
            return {
                'success': True,
                'response': "I'll help you set up Twitter/X credentials. Please provide:\n1. API Key\n2. API Secret\n3. Access Token\n4. Access Token Secret\n\nYou can get these from the Twitter Developer Portal.",
                'intent': 'setup_credentials',
                'action_required': 'credential_input',
                'platform': 'twitter',
                'required_fields': ['api_key', 'api_secret', 'access_token', 'access_token_secret']
            }
        elif platform == 'linkedin':
            return {
                'success': True,
                'response': "I'll help you set up LinkedIn credentials. Please provide:\n1. Client ID\n2. Client Secret\n3. Access Token\n\nYou can get these from the LinkedIn Developer Portal.",
                'intent': 'setup_credentials',
                'action_required': 'credential_input',
                'platform': 'linkedin',
                'required_fields': ['client_id', 'client_secret', 'access_token']
            }
        else:
            return {
                'success': True,
                'response': "Which social media platform would you like to set up? I support Instagram, Twitter/X, and LinkedIn.",
                'intent': 'setup_credentials',
                'action_required': 'platform_selection'
            }
    
    async def _handle_content_creation(self, 
                                     user_id: str,
                                     entities: Dict[str, Any],
                                     context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ad content creation request"""
        product_description = entities.get('product_description', '')
        tone = entities.get('tone', 'professional')
        target_audience = entities.get('target_audience', 'general')
        platforms = entities.get('platforms', ['instagram'])
        
        if not product_description:
            return {
                'success': True,
                'response': "I'd be happy to help create ad content! Please tell me:\n1. What product or service are you promoting?\n2. What tone should I use? (professional, casual, humorous, etc.)\n3. Who is your target audience?\n4. Which platforms should I create content for?",
                'intent': 'create_ad_content',
                'action_required': 'content_details'
            }
        
        return {
            'success': True,
            'response': f"Perfect! I'll create ad content for '{product_description}' with a {tone} tone for {target_audience} audience on {', '.join(platforms)}. Should I also generate an AI image to go with the captions?",
            'intent': 'create_ad_content',
            'action_required': 'content_generation',
            'product_description': product_description,
            'tone': tone,
            'target_audience': target_audience,
            'platforms': platforms
        }
    
    async def _handle_image_upload(self, 
                                 user_id: str,
                                 entities: Dict[str, Any],
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle image upload request"""
        return {
            'success': True,
            'response': "I can help you upload an image! Please provide the image file. I'll analyze it and suggest captions and hashtags that work well with your content.",
            'intent': 'upload_image',
            'action_required': 'file_upload',
            'accepted_formats': ['jpg', 'jpeg', 'png', 'gif']
        }
    
    async def _handle_scheduling(self, 
                               user_id: str,
                               entities: Dict[str, Any],
                               context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle posting schedule setup"""
        time = entities.get('time', '12:00 AM')
        frequency = entities.get('frequency', 'daily')
        
        return {
            'success': True,
            'response': f"I'll set up your posting schedule for {frequency} at {time}. The default is daily at 12:00 AM. Would you like to customize this?",
            'intent': 'schedule_posting',
            'action_required': 'schedule_confirmation',
            'time': time,
            'frequency': frequency
        }
    
    async def _handle_history_request(self, 
                                   user_id: str,
                                   entities: Dict[str, Any],
                                   context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle posting history request"""
        return {
            'success': True,
            'response': "I'll show you your posting history. This includes all generated content, posting schedules, and performance metrics.",
            'intent': 'view_history',
            'action_required': 'history_display'
        }
    
    async def _handle_help_request(self, 
                                 user_id: str,
                                 context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle help request"""
        help_text = """
        I'm your AI Social Media Advertising Agent! Here's what I can help you with:

        🚀 **Core Features:**
        • Generate AI-powered ad content (images + captions)
        • Post automatically to Instagram, Twitter/X, and LinkedIn
        • Schedule daily posts at 12 AM (customizable)
        • Support both feed posts and Instagram stories
        • Track posting history to avoid duplicates

        📝 **Getting Started:**
        1. Set up your social media credentials
        2. Tell me about your product/service
        3. I'll generate content and post automatically

        💬 **Commands:**
        • "Set up Instagram credentials"
        • "Create ad for [product description]"
        • "Upload an image"
        • "Change posting schedule"
        • "Show posting history"

        Just tell me what you'd like to do!
        """
        
        return {
            'success': True,
            'response': help_text,
            'intent': 'help',
            'action_required': 'none'
        }
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()