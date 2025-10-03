"""
Cerebrus API client for conversational interface.
"""

import httpx
import json
from typing import Dict, Any, Optional
from src.config.settings import settings
from src.models.schemas import UserInteraction, AgentResponse

class CerebrusClient:
    """Client for interacting with Cerebrus API."""
    
    def __init__(self):
        self.api_key = settings.cerebrus_api_key
        self.base_url = settings.cerebrus_base_url
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            },
            timeout=30.0
        )
    
    async def send_message(self, user_id: str, message: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """Send a message to Cerebrus and get agent response."""
        try:
            payload = {
                "user_id": user_id,
                "message": message,
                "context": context or {}
            }
            
            response = await self.client.post("/chat", json=payload)
            response.raise_for_status()
            
            data = response.json()
            return AgentResponse(
                message=data.get("message", ""),
                action_required=data.get("action_required"),
                data=data.get("data"),
                next_steps=data.get("next_steps")
            )
            
        except httpx.HTTPError as e:
            return AgentResponse(
                message=f"Sorry, I encountered an error: {str(e)}",
                action_required="retry"
            )
    
    async def process_user_input(self, interaction: UserInteraction) -> AgentResponse:
        """Process user interaction and return appropriate response."""
        # This is where we'll implement the conversation logic
        # For now, we'll create a simple response based on the message content
        
        message_lower = interaction.message.lower()
        
        if "credentials" in message_lower or "login" in message_lower:
            return AgentResponse(
                message="I can help you set up your social media credentials. Which platform would you like to configure first? (Instagram, Twitter, or LinkedIn)",
                action_required="credentials_setup",
                next_steps=["Select platform", "Provide credentials", "Test connection"]
            )
        
        elif "ad" in message_lower or "post" in message_lower:
            return AgentResponse(
                message="Great! Let's create an ad. Please tell me about your product or service, and I'll help you generate content.",
                action_required="ad_creation",
                next_steps=["Describe product/service", "Choose tone", "Select target audience"]
            )
        
        elif "schedule" in message_lower or "time" in message_lower:
            return AgentResponse(
                message="I can help you configure your posting schedule. Currently set to post daily at 12 AM. Would you like to change this?",
                action_required="schedule_config",
                next_steps=["Set posting time", "Choose platforms", "Enable/disable auto-posting"]
            )
        
        elif "image" in message_lower or "photo" in message_lower:
            return AgentResponse(
                message="I can generate AI images for your ads or help you upload your own. What would you prefer?",
                action_required="image_handling",
                next_steps=["Choose image type", "Provide prompt or upload", "Review generated image"]
            )
        
        else:
            return AgentResponse(
                message="I'm your AI social media advertising assistant! I can help you with:\n• Setting up social media credentials\n• Creating AI-generated ads\n• Scheduling posts\n• Managing images\n\nWhat would you like to do?",
                next_steps=["Set up credentials", "Create an ad", "Configure schedule", "Manage images"]
            )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()