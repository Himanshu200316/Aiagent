#!/usr/bin/env python3
"""
Cerebrus API - Conversational interface for the AI Social Media Advertising Agent
"""

import os
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class UserInput(BaseModel):
    """User input model"""
    message: str = Field(..., description="User's message or request")
    user_id: Optional[str] = Field(None, description="User identifier")
    platform: Optional[str] = Field(None, description="Target platform")
    context: Optional[Dict] = Field(None, description="Additional context")

class AdGenerationRequest(BaseModel):
    """Ad generation request model"""
    product_description: str = Field(..., description="Description of product/service")
    platforms: List[str] = Field(default=["instagram", "twitter", "linkedin"], description="Target platforms")
    tone: str = Field(default="professional", description="Caption tone")
    target_audience: str = Field(default="general", description="Target audience")
    custom_keywords: Optional[List[str]] = Field(None, description="Custom keywords for hashtags")
    image_style: str = Field(default="realistic", description="Image generation style")
    post_type: str = Field(default="feed_post", description="Type of post")
    use_custom_image: bool = Field(default=False, description="Use uploaded image instead of AI generation")

class CredentialsRequest(BaseModel):
    """Credentials storage request model"""
    platform: str = Field(..., description="Social media platform")
    credentials: Dict[str, Any] = Field(..., description="Platform credentials")

class CerebrusAPI:
    """Conversational API interface for the social media agent"""

    def __init__(self, prompt_manager, image_generator, caption_generator,
                 social_media_manager, user_manager, posting_scheduler):
        self.prompt_manager = prompt_manager
        self.image_generator = image_generator
        self.caption_generator = caption_generator
        self.social_media_manager = social_media_manager
        self.user_manager = user_manager
        self.posting_scheduler = posting_scheduler

        self.router = APIRouter()
        self._setup_routes()

        # Conversation state tracking
        self.conversations = {}

    def _setup_routes(self):
        """Set up API routes"""

        @self.router.post("/chat")
        async def chat_endpoint(user_input: UserInput):
            """Main chat endpoint for conversational interaction"""
            try:
                response = await self.process_message(
                    user_input.message,
                    user_input.user_id,
                    user_input.platform,
                    user_input.context
                )
                return {"response": response}
            except Exception as e:
                logger.error(f"Chat endpoint error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.post("/generate-ad")
        async def generate_ad_endpoint(request: AdGenerationRequest, background_tasks: BackgroundTasks):
            """Generate and post advertisements"""
            try:
                result = await self.generate_advertisement(request, background_tasks)
                return result
            except Exception as e:
                logger.error(f"Ad generation error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.post("/upload-credentials")
        async def upload_credentials_endpoint(request: CredentialsRequest):
            """Store user credentials for social media platforms"""
            try:
                if not request.user_id:
                    raise HTTPException(status_code=400, detail="User ID required")

                success = self.user_manager.store_credentials(
                    request.user_id,
                    request.platform,
                    request.credentials
                )

                if success:
                    return {"message": f"Credentials stored for {request.platform}"}
                else:
                    raise HTTPException(status_code=500, detail="Failed to store credentials")

            except Exception as e:
                logger.error(f"Credentials upload error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.post("/upload-image")
        async def upload_image_endpoint(file: UploadFile = File(...)):
            """Upload custom image for posting"""
            try:
                if not file.filename:
                    raise HTTPException(status_code=400, detail="No file provided")

                # Save uploaded image
                image_path = await self.image_generator.upload_image(file.file)

                if image_path:
                    return {
                        "message": "Image uploaded successfully",
                        "image_path": image_path,
                        "image_info": self.image_generator.get_image_info(image_path)
                    }
                else:
                    raise HTTPException(status_code=500, detail="Failed to save image")

            except Exception as e:
                logger.error(f"Image upload error: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/status")
        async def status_endpoint():
            """Get system status and statistics"""
            return {
                "system_status": "online",
                "timestamp": datetime.now().isoformat(),
                "components": {
                    "prompt_manager": self.prompt_manager.get_prompt_stats(),
                    "scheduler": self.posting_scheduler.get_scheduler_status(),
                    "posting_stats": self.posting_scheduler.get_posting_stats()
                },
                "supported_platforms": self.social_media_manager.list_supported_platforms()
            }

    async def process_message(self, message: str, user_id: str = None,
                            platform: str = None, context: Dict = None) -> str:
        """
        Process user message and return appropriate response

        Args:
            message: User's input message
            user_id: User identifier
            platform: Target platform
            context: Additional context

        Returns:
            AI response message
        """
        try:
            message_lower = message.lower()

            # Handle different types of user requests
            if any(word in message_lower for word in ["hello", "hi", "start", "help"]):
                return await self._handle_greeting(user_id)

            elif any(word in message_lower for word in ["generate", "create", "make ad", "advertisement"]):
                return await self._handle_ad_generation_request(message, user_id)

            elif any(word in message_lower for word in ["credentials", "login", "connect", "account"]):
                return await self._handle_credentials_request(message, user_id)

            elif any(word in message_lower for word in ["image", "upload", "picture"]):
                return await self._handle_image_request(message, user_id)

            elif any(word in message_lower for word in ["schedule", "post", "when", "frequency"]):
                return await self._handle_scheduling_request(message, user_id)

            elif any(word in message_lower for word in ["status", "stats", "statistics"]):
                return await self._handle_status_request(user_id)

            else:
                return await self._handle_general_request(message, user_id)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "I apologize, but I encountered an error processing your request. Please try again or contact support."

    async def _handle_greeting(self, user_id: str = None) -> str:
        """Handle greeting and introduction"""
        if user_id:
            user = self.user_manager._users.get(user_id)
            if user:
                return f"""Hello {user.get('name', 'there')}! 👋

I'm your AI Social Media Advertising Agent. I can help you:

🚀 Generate and post advertisements on Instagram, X, and LinkedIn
🎨 Create AI-generated images or use your uploaded images
📅 Schedule daily posts at 12:00 AM automatically
⚙️ Manage your account credentials and preferences

What would you like to do today?"""

        return """Hello! 👋

I'm your AI Social Media Advertising Agent, powered by advanced AI to help you create and manage social media advertisements.

Here's what I can do for you:

🎯 Generate engaging ad content with AI images and captions
📱 Post to Instagram, X (Twitter), and LinkedIn automatically
⏰ Schedule daily posts at 12:00 AM
🖼️ Use AI-generated or your uploaded images
🔐 Securely manage your social media credentials

To get started, please provide your email address so I can create or access your account."""

    async def _handle_ad_generation_request(self, message: str, user_id: str) -> str:
        """Handle ad generation requests"""
        return """Great! Let's create an advertisement for you.

I need some information to generate the perfect ad:

1. **Product/Service Description**: What are you advertising?
2. **Target Platforms**: Instagram, X (Twitter), LinkedIn, or all?
3. **Tone**: Professional, casual, or exciting?
4. **Target Audience**: Business professionals, consumers, or general?
5. **Image Style**: Realistic, artistic, cartoon, minimalist, etc.
6. **Custom Image**: Do you want to upload your own image?

Please provide these details, or I can use intelligent defaults to get started quickly!

For example: "Create an ad for my coffee shop, target Instagram and LinkedIn, professional tone, for coffee lovers, realistic style" """

    async def _handle_credentials_request(self, message: str, user_id: str) -> str:
        """Handle credentials setup requests"""
        if not user_id:
            return """I need to know who you are first. Please provide your email address so I can create or access your account.

Once I have your account set up, I can help you securely store your social media credentials for automated posting."""

        return """Perfect! Let's set up your social media credentials for automated posting.

I can help you connect to:
📸 **Instagram** - For visual storytelling and reach
🐦 **X (Twitter)** - For quick updates and engagement
💼 **LinkedIn** - For professional networking and B2B

Please provide your credentials for each platform you'd like to use. I support:
- Username/Email + Password
- API keys (for advanced users)
- Session tokens (for existing sessions)

Your credentials are encrypted and stored securely. I only use them for posting on your behalf.

Which platform would you like to set up first?"""

    async def _handle_image_request(self, message: str, user_id: str) -> str:
        """Handle image-related requests"""
        return """Excellent! I can help you with images for your advertisements.

You have two options:

🎨 **AI-Generated Images**:
- I can create unique images using advanced AI models
- Styles available: realistic, artistic, cartoon, minimalist, vintage, modern
- Based on your product description and preferences

📸 **Upload Your Own Images**:
- Upload custom images for inspiration or direct use
- I can process and optimize them for social media
- Perfect for branded content or specific visuals

I support common formats: JPG, PNG, and can handle various sizes.

Would you like me to generate an AI image for your ad, or do you have an image you'd like to upload?"""

    async def _handle_scheduling_request(self, message: str, user_id: str) -> str:
        """Handle scheduling and posting requests"""
        return """Perfect! I can help you set up automated posting.

📅 **Default Schedule**: Daily at 12:00 AM
⚙️ **Customizable Options**:
- Posting frequency (daily, every other day, weekly)
- Specific posting times
- Platform selection per post
- Content themes and variations

🔄 **Current Status**:
- Scheduler is active and running
- Next posting: Tomorrow at 12:00 AM
- Platforms configured: Based on your credentials

I can also trigger immediate posts for testing or special announcements.

Would you like to:
1. Change your posting schedule?
2. Trigger an immediate post?
3. Check posting statistics?
4. Configure platform-specific settings?"""

    async def _handle_status_request(self, user_id: str) -> str:
        """Handle status and statistics requests"""
        try:
            stats = self.posting_scheduler.get_posting_stats()
            prompt_stats = self.prompt_manager.get_prompt_stats()

            return f"""📊 **System Status & Statistics**

✅ **System Health**: Online and operational

📈 **Posting Statistics**:
• Total Posts: {stats.get('total_posts', 0)}
• Success Rate: {stats.get('success_rate', 0)}%
• Last Post: {stats.get('last_post', 'Never')}

🎯 **Prompt Management**:
• Total Prompts: {prompt_stats.get('total_prompts', 0)}
• Used Prompts: {prompt_stats.get('used_prompts', 0)}
• Available for Use: {prompt_stats.get('unused_prompts', 0)}

🔧 **Active Components**:
• Daily Scheduler: {'✅ Running' if self.posting_scheduler.is_running else '❌ Stopped'}
• Image Generator: Ready
• Caption Generator: Ready
• Social Media Manager: Ready

Next automated posting: {self.posting_scheduler._get_next_post_time() or 'Not scheduled'}

Everything looks good! Is there anything specific you'd like me to help you with?"""

        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return "I apologize, but I couldn't retrieve the system status right now. Please try again in a moment."

    async def _handle_general_request(self, message: str, user_id: str) -> str:
        """Handle general or unclear requests"""
        return """I'm here to help you with your social media advertising needs!

I can assist you with:

🎯 **Ad Generation**
- Create engaging content with AI images and captions
- Post to Instagram, X, and LinkedIn automatically

🔐 **Account Management**
- Securely store your social media credentials
- Manage posting preferences and schedules

🎨 **Content Creation**
- Generate AI images or use your uploaded images
- Create platform-optimized captions

📅 **Automated Posting**
- Daily posts at 12:00 AM (customizable)
- Immediate posting for special announcements

Could you please be more specific about what you'd like to do? For example:
- "Help me set up my Instagram account"
- "Create an ad for my new product"
- "Show me my posting statistics"
- "Change my posting schedule" """

    async def generate_advertisement(self, request: AdGenerationRequest, background_tasks: BackgroundTasks) -> Dict:
        """
        Generate and post advertisements based on request

        Args:
            request: Ad generation request
            background_tasks: FastAPI background tasks

        Returns:
            Generation results
        """
        try:
            # Generate image if not using custom image
            image_path = None
            if not request.use_custom_image:
                image_path = await self.image_generator.generate_image(
                    prompt=request.product_description,
                    style=request.image_style,
                    service="stable_diffusion"  # Could be made configurable
                )
            else:
                # Use uploaded image (would need to be stored from previous upload)
                # For now, use a placeholder
                image_path = "/app/data/images/placeholder.png"

            if not image_path:
                return {
                    "success": False,
                    "error": "Failed to generate or locate image"
                }

            # Generate caption
            caption = self.caption_generator.generate_caption(
                product_description=request.product_description,
                platform=request.platforms[0] if request.platforms else "instagram",
                tone=request.tone,
                target_audience=request.target_audience,
                custom_keywords=request.custom_keywords
            )

            # Create prompt entry to avoid repetition
            prompt_data = {
                "product_description": request.product_description,
                "tone": request.tone,
                "target_audience": request.target_audience,
                "image_style": request.image_style,
                "platforms": request.platforms
            }

            for platform in request.platforms:
                self.prompt_manager.add_prompt(prompt_data, platform, request.post_type)

            # Post to all requested platforms
            posting_results = await self.social_media_manager.post_to_all_platforms(
                image_path=image_path,
                caption=caption,
                platforms=request.platforms,
                post_type=request.post_type
            )

            # Schedule for future if this is part of daily posting
            if request.post_type == "feed_post":
                background_tasks.add_task(
                    self._schedule_future_posts,
                    request,
                    image_path,
                    caption
                )

            return {
                "success": True,
                "message": "Advertisement generated and posted successfully",
                "image_path": image_path,
                "caption": caption,
                "posting_results": posting_results,
                "prompt_id": list(set([
                    self.prompt_manager._generate_prompt_hash(prompt_data)
                ]))[0]  # Get one of the prompt IDs
            }

        except Exception as e:
            logger.error(f"Error in ad generation: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def _schedule_future_posts(self, request: AdGenerationRequest, image_path: str, caption: str):
        """Schedule future posts based on the generated content"""
        try:
            # This would integrate with the scheduler to ensure variety
            # For now, just log the intention
            logger.info(f"Scheduled future posts for request: {request.product_description[:50]}...")

            # Mark prompts as used to avoid immediate repetition
            prompt_data = {
                "product_description": request.product_description,
                "tone": request.tone,
                "target_audience": request.target_audience,
                "image_style": request.image_style,
                "platforms": request.platforms
            }

            for platform in request.platforms:
                prompt_id = self.prompt_manager._generate_prompt_hash(prompt_data)
                self.prompt_manager.mark_prompt_used(prompt_id, platform)

        except Exception as e:
            logger.error(f"Error scheduling future posts: {e}")

    def create_user_session(self, email: str) -> str:
        """Create a user session"""
        user_id = self.user_manager.create_user(email)
        return user_id

    def get_user_info(self, user_id: str) -> Dict:
        """Get user information"""
        if user_id in self.user_manager._users:
            user = self.user_manager._users[user_id]
            return {
                "id": user_id,
                "email": user.get("email"),
                "name": user.get("name"),
                "preferences": self.user_manager.get_user_preferences(user_id),
                "configured_platforms": self.user_manager._get_configured_platforms(user_id)
            }
        return {}