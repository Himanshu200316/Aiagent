"""
Cerebrus API Handler
Manages conversational interactions with users for social media ad generation
"""

import asyncio
import logging
import os
from typing import Dict, Any, List, Optional
import httpx
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class CerebrusHandler:
    """Handler for Cerebrus API interactions"""
    
    def __init__(self):
        self.api_key = os.getenv('CEREBRUS_API_KEY')
        self.base_url = os.getenv('CEREBRUS_BASE_URL', 'https://api.cerebrus.ai/v1')
        self.client = None
        self.conversation_states = {}  # Store conversation states
        
    async def initialize(self):
        """Initialize Cerebrus API client"""
        if not self.api_key:
            raise ValueError("CEREBRUS_API_KEY not configured")
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            },
            timeout=30.0
        )
        
        logger.info("Cerebrus API handler initialized")
    
    async def start_conversation(self, user_id: str, conversation_type: str = "ad_setup") -> Dict[str, Any]:
        """Start a new conversation with a user"""
        try:
            if not self.client:
                await self.initialize()
            
            # Initialize conversation state
            conversation_id = f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            self.conversation_states[conversation_id] = {
                'user_id': user_id,
                'type': conversation_type,
                'stage': 'welcome',
                'collected_data': {},
                'created_at': datetime.now(),
                'last_activity': datetime.now()
            }
            
            # Send welcome message based on conversation type
            welcome_message = self._get_welcome_message(conversation_type)
            
            response = await self._send_message(conversation_id, welcome_message, is_system=True)
            
            return {
                'conversation_id': conversation_id,
                'message': response.get('message'),
                'next_steps': response.get('next_steps', []),
                'stage': 'welcome'
            }
            
        except Exception as e:
            logger.error(f"Failed to start conversation: {e}")
            raise
    
    async def process_user_message(self, conversation_id: str, user_message: str, 
                                 attachments: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Process user message and return appropriate response"""
        try:
            if conversation_id not in self.conversation_states:
                return {
                    'error': 'Conversation not found',
                    'action': 'restart_conversation'
                }
            
            state = self.conversation_states[conversation_id]
            state['last_activity'] = datetime.now()
            
            # Process message based on current stage
            if state['stage'] == 'welcome':
                return await self._handle_welcome_stage(conversation_id, user_message)
            elif state['stage'] == 'credentials':
                return await self._handle_credentials_stage(conversation_id, user_message)
            elif state['stage'] == 'product_info':
                return await self._handle_product_info_stage(conversation_id, user_message)
            elif state['stage'] == 'audience_tone':
                return await self._handle_audience_tone_stage(conversation_id, user_message)
            elif state['stage'] == 'platforms':
                return await self._handle_platforms_stage(conversation_id, user_message)
            elif state['stage'] == 'images':
                return await self._handle_images_stage(conversation_id, user_message, attachments)
            elif state['stage'] == 'schedule':
                return await self._handle_schedule_stage(conversation_id, user_message)
            elif state['stage'] == 'review':
                return await self._handle_review_stage(conversation_id, user_message)
            else:
                return await self._handle_general_query(conversation_id, user_message)
                
        except Exception as e:
            logger.error(f"Failed to process user message: {e}")
            return {
                'error': 'Failed to process message',
                'message': 'I encountered an error processing your message. Please try again.'
            }
    
    def _get_welcome_message(self, conversation_type: str) -> str:
        """Get welcome message based on conversation type"""
        messages = {
            'ad_setup': """🚀 Welcome to your AI Social Media Ad Agent!

I'm here to help you create and automatically post engaging advertisements across Instagram, X (Twitter), and LinkedIn.

To get started, I'll need to gather some information from you:
1. Your social media account credentials
2. Details about your product/service
3. Your target audience and preferred tone
4. Platform preferences
5. Image preferences (AI-generated or your own uploads)
6. Posting schedule

Let's begin! Would you like to start setting up your first ad campaign?""",
            
            'content_generation': """🎨 Let's create some amazing content!

I can help you generate both images and captions for your social media ads. 

What would you like to create today?
- A complete ad (image + caption)
- Just a caption for your existing image
- Just an AI-generated image
- Multiple variations of existing content

What sounds good to you?""",
            
            'account_management': """⚙️ Account Management

I can help you with:
- Adding or updating social media credentials
- Managing your posting schedule
- Reviewing your posting history
- Updating campaign settings

What would you like to manage today?"""
        }
        
        return messages.get(conversation_type, messages['ad_setup'])
    
    async def _handle_welcome_stage(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """Handle welcome stage interaction"""
        state = self.conversation_states[conversation_id]
        
        if any(word in user_message.lower() for word in ['yes', 'start', 'begin', 'setup', 'create']):
            state['stage'] = 'credentials'
            return {
                'message': """Great! Let's start by setting up your social media accounts.

🔐 **Account Credentials Setup**

For security, I need access to your social media accounts. Please provide credentials for the platforms you want to use:

**Instagram:**
- Username and Password (or App Password)

**X (Twitter):**
- API Key, API Secret, Access Token, Access Token Secret, Bearer Token

**LinkedIn:**
- Access Token (from LinkedIn Developer Portal)

Which platform would you like to set up first? Or if you prefer, you can say "skip credentials" and we'll set them up later.""",
                'stage': 'credentials',
                'next_steps': ['Provide Instagram credentials', 'Provide Twitter credentials', 'Provide LinkedIn credentials', 'Skip for now']
            }
        else:
            return {
                'message': """I understand you might have questions! I'm here to help you create automated social media advertisements.

Here's what I can do for you:
- Generate AI-powered images and captions
- Post automatically to Instagram, X, and LinkedIn
- Ensure no duplicate content
- Schedule posts (default: daily at 12 AM)
- Handle both feed posts and Instagram stories

Would you like to start setting up your ad campaign, or do you have specific questions about how this works?""",
                'stage': 'welcome',
                'next_steps': ['Start setup', 'Ask questions', 'Learn more']
            }
    
    async def _handle_credentials_stage(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """Handle credentials setup stage"""
        state = self.conversation_states[conversation_id]
        
        if 'skip' in user_message.lower():
            state['stage'] = 'product_info'
            return {
                'message': """No problem! We can set up credentials later.

📝 **Product/Service Information**

Now, tell me about what you're advertising:

1. **What product or service are you promoting?**
   (Be as detailed as possible - this helps me create better ads)

2. **What makes it special or unique?**

3. **What's the main benefit for customers?**

Please share these details so I can create compelling advertisements for you!""",
                'stage': 'product_info',
                'next_steps': ['Describe your product/service']
            }
        
        # Parse credentials (in a real implementation, you'd want secure handling)
        if 'instagram' in user_message.lower():
            # Extract Instagram credentials
            state['collected_data']['instagram_setup'] = True
            return {
                'message': """✅ Instagram credentials noted! 

What's next?
- Set up Twitter/X credentials
- Set up LinkedIn credentials  
- Move on to product information

What would you prefer?""",
                'stage': 'credentials'
            }
        elif 'twitter' in user_message.lower() or 'x.com' in user_message.lower():
            state['collected_data']['twitter_setup'] = True
            return {
                'message': """✅ Twitter/X credentials noted!

What's next?
- Set up Instagram credentials
- Set up LinkedIn credentials
- Move on to product information

What would you prefer?""",
                'stage': 'credentials'
            }
        elif 'linkedin' in user_message.lower():
            state['collected_data']['linkedin_setup'] = True
            return {
                'message': """✅ LinkedIn credentials noted!

What's next?
- Set up Instagram credentials
- Set up Twitter/X credentials
- Move on to product information

What would you prefer?""",
                'stage': 'credentials'
            }
        elif any(word in user_message.lower() for word in ['done', 'next', 'continue', 'product']):
            state['stage'] = 'product_info'
            return {
                'message': """Perfect! Now let's talk about your product or service.

📝 **Product/Service Information**

Please tell me:

1. **What are you advertising?** (product, service, brand, etc.)
2. **What makes it special?** (unique features, benefits)
3. **What problem does it solve?** (customer pain points)
4. **Any specific details I should highlight?** (price, availability, features)

The more details you provide, the better I can tailor your advertisements!""",
                'stage': 'product_info'
            }
        else:
            return {
                'message': """I'm ready to help you set up your credentials securely. 

Please let me know:
- Which platform you'd like to set up (Instagram, Twitter/X, or LinkedIn)
- Or say "skip" if you want to set up credentials later
- Or say "next" to move on to product information

What would you prefer?""",
                'stage': 'credentials'
            }
    
    async def _handle_product_info_stage(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """Handle product information collection"""
        state = self.conversation_states[conversation_id]
        state['collected_data']['product_service_description'] = user_message
        state['stage'] = 'audience_tone'
        
        return {
            'message': f"""Excellent! I've got great information about your offering.

🎯 **Target Audience & Tone**

Now let's define your target audience and messaging tone:

**Target Audience:**
Who are you trying to reach? For example:
- Young professionals (25-35)
- Small business owners
- Fitness enthusiasts
- Parents with young children
- Tech-savvy millennials

**Tone & Style:**
How do you want to sound? Choose from:
- Professional & Authoritative
- Casual & Friendly  
- Luxury & Sophisticated
- Playful & Energetic
- Minimalist & Clean

Please tell me about your target audience and preferred tone!""",
            'stage': 'audience_tone',
            'next_steps': ['Describe target audience', 'Choose tone/style']
        }
    
    async def _handle_audience_tone_stage(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """Handle audience and tone selection"""
        state = self.conversation_states[conversation_id]
        
        # Parse audience and tone from message
        message_lower = user_message.lower()
        
        # Extract tone
        tone_keywords = {
            'professional': ['professional', 'authoritative', 'business', 'corporate'],
            'casual': ['casual', 'friendly', 'approachable', 'relaxed'],
            'luxury': ['luxury', 'sophisticated', 'premium', 'elegant'],
            'playful': ['playful', 'energetic', 'fun', 'vibrant'],
            'minimalist': ['minimalist', 'clean', 'simple', 'minimal']
        }
        
        detected_tone = 'professional'  # default
        for tone, keywords in tone_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_tone = tone
                break
        
        state['collected_data']['target_audience'] = user_message
        state['collected_data']['tone'] = detected_tone
        state['stage'] = 'platforms'
        
        return {
            'message': f"""Perfect! I've captured your audience and tone preferences.

📱 **Platform Selection**

Which social media platforms would you like to post to?

✅ **Available Platforms:**
- **Instagram** (Feed posts + Stories)
- **X (Twitter)** (Tweets with images)
- **LinkedIn** (Professional posts)

You can choose:
- All platforms (recommended for maximum reach)
- Specific platforms only
- Start with one and add more later

Which platforms interest you?""",
            'stage': 'platforms',
            'next_steps': ['Choose all platforms', 'Select specific platforms', 'Instagram only', 'Twitter only', 'LinkedIn only']
        }
    
    async def _handle_platforms_stage(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """Handle platform selection"""
        state = self.conversation_states[conversation_id]
        message_lower = user_message.lower()
        
        platforms = []
        if 'instagram' in message_lower or 'insta' in message_lower:
            platforms.append('instagram')
        if 'twitter' in message_lower or 'x.com' in message_lower or ' x ' in message_lower:
            platforms.append('twitter')
        if 'linkedin' in message_lower:
            platforms.append('linkedin')
        if 'all' in message_lower:
            platforms = ['instagram', 'twitter', 'linkedin']
        
        if not platforms:
            platforms = ['instagram', 'twitter', 'linkedin']  # default to all
        
        state['collected_data']['platforms'] = platforms
        state['stage'] = 'images'
        
        platform_names = ', '.join(platforms).title()
        
        return {
            'message': f"""Great choice! I'll create content for: {platform_names}

🖼️ **Image Preferences**

For your advertisements, I can:

**Option 1: AI-Generated Images**
- I'll create custom images using DALL-E or Stable Diffusion
- Perfectly tailored to your product and audience
- Professional, eye-catching designs

**Option 2: Your Own Images**
- Upload your existing product photos, logos, or graphics
- I'll optimize them for each platform
- You can also use them as inspiration for AI generation

**Option 3: Combination**
- Mix of AI-generated and your uploaded images
- Best of both worlds

What's your preference for images?""",
            'stage': 'images',
            'next_steps': ['AI-generated images', 'Upload my own images', 'Combination approach']
        }
    
    async def _handle_images_stage(self, conversation_id: str, user_message: str, 
                                 attachments: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Handle image preferences and uploads"""
        state = self.conversation_states[conversation_id]
        message_lower = user_message.lower()
        
        image_preference = 'ai_generated'  # default
        if 'upload' in message_lower or 'own' in message_lower or 'my' in message_lower:
            image_preference = 'user_uploaded'
        elif 'combination' in message_lower or 'both' in message_lower or 'mix' in message_lower:
            image_preference = 'combination'
        
        state['collected_data']['image_preference'] = image_preference
        
        # Handle attachments if provided
        if attachments:
            state['collected_data']['uploaded_images'] = attachments
        
        state['stage'] = 'schedule'
        
        return {
            'message': f"""Perfect! I've noted your image preferences.

⏰ **Posting Schedule**

By default, I'll post your ads daily at 12:00 AM (midnight) in your timezone.

You can customize this:
- **Frequency:** Daily, every other day, weekly, etc.
- **Time:** Any time that works best for your audience
- **Timezone:** Your local timezone or target audience timezone

Current default: **Daily at 12:00 AM UTC**

Would you like to:
- Keep the default schedule
- Customize your posting times
- Set up multiple posting times per day

What works best for you?""",
            'stage': 'schedule',
            'next_steps': ['Keep default schedule', 'Customize schedule', 'Multiple posts per day']
        }
    
    async def _handle_schedule_stage(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """Handle posting schedule setup"""
        state = self.conversation_states[conversation_id]
        message_lower = user_message.lower()
        
        if 'default' in message_lower or 'keep' in message_lower:
            schedule = {'frequency': 'daily', 'time': '00:00', 'timezone': 'UTC'}
        elif 'customize' in message_lower:
            schedule = {'frequency': 'custom', 'time': 'user_defined', 'timezone': 'user_defined'}
        else:
            schedule = {'frequency': 'daily', 'time': '00:00', 'timezone': 'UTC'}
        
        state['collected_data']['schedule'] = schedule
        state['stage'] = 'review'
        
        # Prepare summary
        summary = self._generate_setup_summary(state['collected_data'])
        
        return {
            'message': f"""🎉 **Setup Complete! Here's your configuration:**

{summary}

Everything looks good? I can:
- **Start generating content** and begin posting
- **Make changes** to any of these settings
- **Generate a test post** first to see how it looks
- **Set up additional campaigns** with different settings

What would you like to do next?""",
            'stage': 'review',
            'next_steps': ['Start generating content', 'Make changes', 'Generate test post', 'Create another campaign']
        }
    
    async def _handle_review_stage(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """Handle final review and confirmation"""
        state = self.conversation_states[conversation_id]
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['start', 'begin', 'generate', 'go']):
            # Mark conversation as complete and ready for content generation
            state['stage'] = 'completed'
            state['status'] = 'ready_for_generation'
            
            return {
                'message': """🚀 **Launching your AI Social Media Ad Agent!**

I'm now ready to:
1. Generate your first advertisement (image + caption)
2. Schedule it for posting across your selected platforms
3. Continue creating unique content daily
4. Track all posting activity

Your first ad should be ready within the next few minutes. I'll ensure every piece of content is unique and tailored to your specifications.

You can always chat with me to:
- Check on posting status
- Modify settings
- Generate additional content
- Review performance

Welcome to automated social media advertising! 🎯""",
                'stage': 'completed',
                'action': 'start_content_generation',
                'campaign_data': state['collected_data']
            }
        elif any(word in message_lower for word in ['test', 'preview', 'sample']):
            return {
                'message': """🧪 **Generating Test Content...**

I'll create a sample advertisement based on your settings. This won't be posted automatically - you'll get to review it first.

Give me a moment to generate:
- A custom image based on your product description
- An engaging caption optimized for your target audience
- Platform-specific formatting

Test content coming up shortly!""",
                'stage': 'review',
                'action': 'generate_test_content',
                'campaign_data': state['collected_data']
            }
        elif any(word in message_lower for word in ['change', 'modify', 'edit', 'update']):
            return {
                'message': """✏️ **What would you like to change?**

I can help you modify:
- Product/service description
- Target audience or tone
- Platform selection
- Image preferences
- Posting schedule
- Account credentials

Just tell me what you'd like to update!""",
                'stage': 'review'
            }
        else:
            return {
                'message': """I'm ready to help! You can:

- Say **"start"** to begin generating and posting content
- Say **"test"** to create a sample post first
- Say **"change [setting]"** to modify any configuration
- Ask me questions about how anything works

What would you like to do?""",
                'stage': 'review'
            }
    
    async def _handle_general_query(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """Handle general queries and ongoing conversation"""
        # This would integrate with Cerebrus API for general conversation
        return {
            'message': """I'm here to help with your social media advertising needs!

You can ask me about:
- Checking your posting status
- Generating new content
- Modifying your campaigns
- Reviewing posting history
- Setting up additional accounts

What would you like to know or do?""",
            'next_steps': ['Check status', 'Generate content', 'Modify settings', 'View history']
        }
    
    def _generate_setup_summary(self, data: Dict[str, Any]) -> str:
        """Generate a summary of the user's setup"""
        summary_parts = []
        
        if 'product_service_description' in data:
            summary_parts.append(f"📦 **Product/Service:** {data['product_service_description'][:100]}...")
        
        if 'target_audience' in data:
            summary_parts.append(f"🎯 **Target Audience:** {data['target_audience']}")
        
        if 'tone' in data:
            summary_parts.append(f"🎨 **Tone:** {data['tone'].title()}")
        
        if 'platforms' in data:
            platforms = ', '.join([p.title() for p in data['platforms']])
            summary_parts.append(f"📱 **Platforms:** {platforms}")
        
        if 'image_preference' in data:
            img_pref = data['image_preference'].replace('_', ' ').title()
            summary_parts.append(f"🖼️ **Images:** {img_pref}")
        
        if 'schedule' in data:
            schedule = data['schedule']
            summary_parts.append(f"⏰ **Schedule:** {schedule.get('frequency', 'Daily')} at {schedule.get('time', '00:00')}")
        
        return '\n'.join(summary_parts)
    
    async def _send_message(self, conversation_id: str, message: str, is_system: bool = False) -> Dict[str, Any]:
        """Send message through Cerebrus API (placeholder for actual API integration)"""
        # In a real implementation, this would call the Cerebrus API
        # For now, we'll return a structured response
        return {
            'message': message,
            'conversation_id': conversation_id,
            'timestamp': datetime.now().isoformat(),
            'is_system': is_system
        }
    
    async def get_conversation_state(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get current conversation state"""
        return self.conversation_states.get(conversation_id)
    
    async def cleanup_old_conversations(self, hours: int = 24):
        """Clean up old inactive conversations"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        to_remove = []
        for conv_id, state in self.conversation_states.items():
            if state['last_activity'] < cutoff_time:
                to_remove.append(conv_id)
        
        for conv_id in to_remove:
            del self.conversation_states[conv_id]
        
        logger.info(f"Cleaned up {len(to_remove)} old conversations")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of Cerebrus handler"""
        return {
            'api_configured': self.api_key is not None,
            'client_initialized': self.client is not None,
            'active_conversations': len(self.conversation_states),
            'base_url': self.base_url
        }