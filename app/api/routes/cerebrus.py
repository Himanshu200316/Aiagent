"""
Cerebrus API Integration Routes
Handles conversational interface for user interaction
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.api.routes.auth import get_current_user
from app.services.cerebrus_integration import CerebrusIntegration
from app.services.credential_manager import credential_manager
from app.services.ai_content_generator import AIContentGenerator
from app.services.storage_manager import storage_manager
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger('cerebrus')

class CerebrusMessage(BaseModel):
    message: str
    context: Optional[Dict[str, Any]] = None

class CerebrusResponse(BaseModel):
    success: bool
    response: str
    intent: str
    action_required: str
    data: Optional[Dict[str, Any]] = None

@router.post("/chat", response_model=CerebrusResponse)
async def chat_with_cerebrus(
    message_data: CerebrusMessage,
    current_user: dict = Depends(get_current_user)
):
    """Main chat endpoint for Cerebrus integration"""
    try:
        user_id = current_user["id"]
        message = message_data.message
        context = message_data.context or {}
        
        # Add user context
        context.update({
            "user_id": user_id,
            "username": current_user["username"],
            "session_type": "social_media_agent"
        })
        
        # Initialize Cerebrus integration
        cerebrus = CerebrusIntegration()
        
        # Handle user input
        result = await cerebrus.handle_user_input(user_id, message, context)
        
        # Close Cerebrus client
        await cerebrus.close()
        
        if result["success"]:
            return CerebrusResponse(
                success=True,
                response=result["response"],
                intent=result.get("intent", "unknown"),
                action_required=result.get("action_required", "none"),
                data=result.get("data")
            )
        else:
            return CerebrusResponse(
                success=False,
                response=f"Sorry, I encountered an error: {result['error']}",
                intent="error",
                action_required="none"
            )
        
    except Exception as e:
        logger.error(f"Cerebrus chat failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Chat service temporarily unavailable"
        )

@router.post("/setup-credentials")
async def setup_credentials_via_cerebrus(
    platform: str,
    credentials: Dict[str, str],
    current_user: dict = Depends(get_current_user)
):
    """Setup credentials through Cerebrus interface"""
    try:
        user_id = current_user["id"]
        
        # Validate credential format
        validation = credential_manager.validate_credential_format(platform, credentials)
        if not validation["valid"]:
            return {
                "success": False,
                "error": validation["error"]
            }
        
        # Store credentials securely
        credential_id = credential_manager.store_credentials(user_id, platform, credentials)
        
        logger.info(f"Credentials set up via Cerebrus for {platform}: {user_id}")
        
        return {
            "success": True,
            "message": f"{platform.title()} credentials have been securely stored and are ready to use!",
            "credential_id": credential_id
        }
        
    except Exception as e:
        logger.error(f"Failed to setup credentials via Cerebrus: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to setup credentials"
        )

@router.post("/generate-content")
async def generate_content_via_cerebrus(
    product_description: str,
    tone: str = "professional",
    target_audience: str = "general",
    platforms: list = ["instagram"],
    generate_image: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """Generate content through Cerebrus interface"""
    try:
        user_id = current_user["id"]
        
        # Generate content
        ai_generator = AIContentGenerator()
        result = await ai_generator.generate_complete_content(
            product_description=product_description,
            tone=tone,
            target_audience=target_audience,
            platforms=platforms,
            generate_image=generate_image
        )
        
        if result["success"]:
            # Store content history
            storage_manager.store_content_history(user_id, result)
            
            # Create user-friendly response
            captions = result.get("captions", {})
            image_info = result.get("image", {})
            
            response_message = f"Great! I've generated content for your '{product_description}' campaign:\n\n"
            
            for platform, caption_data in captions.items():
                response_message += f"📱 **{platform.title()} Caption:**\n{caption_data['caption']}\n\n"
            
            if image_info and image_info.get("success"):
                response_message += f"🖼️ **AI Image Generated:** {image_info['image_path']}\n\n"
            
            response_message += "Would you like me to post this content to your social media accounts?"
            
            return {
                "success": True,
                "message": response_message,
                "content_data": result,
                "action_required": "post_confirmation"
            }
        else:
            return {
                "success": False,
                "error": f"Failed to generate content: {result['error']}"
            }
        
    except Exception as e:
        logger.error(f"Failed to generate content via Cerebrus: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate content"
        )

@router.post("/upload-image")
async def upload_image_via_cerebrus(
    image_path: str,
    current_user: dict = Depends(get_current_user)
):
    """Handle image upload through Cerebrus interface"""
    try:
        user_id = current_user["id"]
        
        # Analyze uploaded image
        ai_generator = AIContentGenerator()
        analysis_result = await ai_generator.analyze_uploaded_image(image_path)
        
        if analysis_result["success"]:
            response_message = f"📸 **Image Analysis Complete!**\n\n{analysis_result['analysis']}\n\n"
            response_message += "Based on this image, I can help you create engaging captions for your social media posts. What would you like to promote with this image?"
            
            return {
                "success": True,
                "message": response_message,
                "image_path": image_path,
                "analysis": analysis_result["analysis"],
                "action_required": "content_creation"
            }
        else:
            return {
                "success": False,
                "error": f"Failed to analyze image: {analysis_result['error']}"
            }
        
    except Exception as e:
        logger.error(f"Failed to handle image upload via Cerebrus: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process image"
        )

@router.get("/status")
async def get_cerebrus_status(current_user: dict = Depends(get_current_user)):
    """Get Cerebrus integration status"""
    try:
        user_id = current_user["id"]
        
        # Get user's setup status
        credentials = credential_manager.list_user_credentials(user_id)
        preferences = storage_manager.get_user_preferences(user_id)
        
        setup_status = {
            "credentials_configured": list(credentials.keys()),
            "schedule_configured": bool(preferences and "schedule" in preferences),
            "ready_to_post": len(credentials) > 0
        }
        
        status_message = "🤖 **Social Media Agent Status:**\n\n"
        
        if setup_status["credentials_configured"]:
            status_message += f"✅ **Connected Platforms:** {', '.join(setup_status['credentials_configured'])}\n"
        else:
            status_message += "❌ **No platforms connected** - Set up your social media credentials first\n"
        
        if setup_status["schedule_configured"]:
            schedule_data = preferences["schedule"]
            status_message += f"⏰ **Auto-posting:** {schedule_data['frequency']} at {schedule_data['post_time']}\n"
        else:
            status_message += "⏰ **Auto-posting:** Not configured\n"
        
        if setup_status["ready_to_post"]:
            status_message += "🚀 **Status:** Ready to create and post content!\n"
        else:
            status_message += "🚀 **Status:** Please complete setup to start posting\n"
        
        return {
            "success": True,
            "message": status_message,
            "status": setup_status
        }
        
    except Exception as e:
        logger.error(f"Failed to get Cerebrus status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get status"
        )

@router.get("/help")
async def get_cerebrus_help():
    """Get help information for Cerebrus interface"""
    help_text = """
    🤖 **Social Media Agent - Cerebrus Interface**
    
    I'm your AI-powered social media assistant! Here's what I can help you with:
    
    **🚀 Getting Started:**
    • "Set up Instagram credentials" - Connect your Instagram account
    • "Set up Twitter credentials" - Connect your Twitter/X account  
    • "Set up LinkedIn credentials" - Connect your LinkedIn account
    
    **📝 Content Creation:**
    • "Create ad for [your product]" - Generate AI content
    • "Upload an image" - Analyze and caption your images
    • "Generate caption for [description]" - Create platform-specific captions
    
    **⏰ Scheduling:**
    • "Set posting schedule" - Configure automatic posting
    • "Enable/disable auto-posting" - Control automated posting
    • "Change posting time" - Modify when content is posted
    
    **📊 Management:**
    • "Show posting history" - View your content history
    • "Check status" - See your account setup status
    • "Help" - Show this help message
    
    **💡 Tips:**
    • Be specific about your product/service when creating content
    • I'll remember your preferences and avoid duplicate content
    • All credentials are encrypted and stored securely
    • Default posting time is 12:00 AM daily (customizable)
    
    Just tell me what you'd like to do!
    """
    
    return {
        "success": True,
        "message": help_text,
        "intent": "help"
    }