"""
MCP module for Twitter/X posting
"""
import tweepy
import json
from typing import Dict, Any, List
from app.services.mcp_base import MCPBase
from app.core.logging import get_logger

logger = get_logger('twitter')

class MCPTwitter(MCPBase):
    """Twitter/X MCP implementation"""
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__(credentials)
        self.api_key = credentials.get('api_key')
        self.api_secret = credentials.get('api_secret')
        self.access_token = credentials.get('access_token')
        self.access_token_secret = credentials.get('access_token_secret')
        self.bearer_token = credentials.get('bearer_token')
        
        # Initialize Tweepy client
        self.client = None
        self._initialize_client()
    
    def get_required_credentials(self) -> List[str]:
        return ['api_key', 'api_secret', 'access_token', 'access_token_secret']
    
    def _initialize_client(self):
        """Initialize Tweepy client"""
        try:
            # Initialize OAuth 1.0a User Context
            auth = tweepy.OAuth1UserHandler(
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_token_secret
            )
            
            self.client = tweepy.API(auth, wait_on_rate_limit=True)
            
        except Exception as e:
            self.log_activity('client_initialization', {
                'status': 'error',
                'error': str(e)
            })
    
    async def authenticate(self) -> bool:
        """Authenticate with Twitter API"""
        try:
            if not self.client:
                return False
            
            # Test authentication by getting user info
            user = self.client.verify_credentials()
            
            if user:
                self.log_activity('authentication', {
                    'status': 'success',
                    'username': user.screen_name
                })
                return True
            else:
                self.log_activity('authentication', {
                    'status': 'failed',
                    'error': 'Could not verify credentials'
                })
                return False
                
        except Exception as e:
            self.log_activity('authentication', {
                'status': 'error',
                'error': str(e)
            })
            return False
    
    async def post_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Post content to Twitter"""
        try:
            caption = content.get('caption', '')
            image_path = content.get('image_path')
            
            if not self.client:
                return {'success': False, 'error': 'Twitter client not initialized'}
            
            if image_path:
                # Post with image
                media = self.client.media_upload(image_path)
                tweet = self.client.update_status(
                    status=caption,
                    media_ids=[media.media_id]
                )
            else:
                # Post text only
                tweet = self.client.update_status(status=caption)
            
            self.log_activity('post_content', {
                'status': 'success',
                'tweet_id': tweet.id_str,
                'text': tweet.text[:100] + '...' if len(tweet.text) > 100 else tweet.text
            })
            
            return {
                'success': True,
                'tweet_id': tweet.id_str,
                'platform': 'twitter',
                'text': tweet.text
            }
            
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
        """Post Twitter story (Fleets) - Note: Twitter removed Fleets in 2021"""
        # Twitter removed Fleets/Stories feature
        return {
            'success': False,
            'error': 'Twitter Stories (Fleets) feature was removed by Twitter'
        }
    
    async def post_thread(self, tweets: List[str]) -> Dict[str, Any]:
        """Post a thread of tweets"""
        try:
            if not self.client:
                return {'success': False, 'error': 'Twitter client not initialized'}
            
            thread_ids = []
            previous_tweet_id = None
            
            for i, tweet_text in enumerate(tweets):
                if i == 0:
                    # First tweet
                    tweet = self.client.update_status(status=tweet_text)
                else:
                    # Reply to previous tweet
                    tweet = self.client.update_status(
                        status=tweet_text,
                        in_reply_to_status_id=previous_tweet_id
                    )
                
                thread_ids.append(tweet.id_str)
                previous_tweet_id = tweet.id_str
            
            self.log_activity('post_thread', {
                'status': 'success',
                'thread_ids': thread_ids,
                'tweet_count': len(tweets)
            })
            
            return {
                'success': True,
                'thread_ids': thread_ids,
                'platform': 'twitter',
                'tweet_count': len(tweets)
            }
            
        except Exception as e:
            self.log_activity('post_thread', {
                'status': 'error',
                'error': str(e)
            })
            return {'success': False, 'error': str(e)}