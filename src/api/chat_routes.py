"""
Chat API Routes
FastAPI routes for conversational interactions via Cerebrus
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from datetime import datetime

from .cerebrus_handler import CerebrusHandler
from ai_generation.content_generator import ContentGenerator, ContentRequest
from storage.data_manager import DataManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    user_id: str
    attachments: Optional[List[Dict]] = None

class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    stage: str
    next_steps: Optional[List[str]] = None
    action: Optional[str] = None
    campaign_data: Optional[Dict[str, Any]] = None

class ConversationStart(BaseModel):
    user_id: str
    conversation_type: str = "ad_setup"

# Global instances (would be dependency injected in production)
cerebrus_handler = CerebrusHandler()
content_generator = ContentGenerator()
data_manager = DataManager()

@router.post("/start", response_model=ChatResponse)
async def start_conversation(request: ConversationStart):
    """Start a new conversation with the AI agent"""
    try:
        result = await cerebrus_handler.start_conversation(
            user_id=request.user_id,
            conversation_type=request.conversation_type
        )
        
        return ChatResponse(
            message=result['message'],
            conversation_id=result['conversation_id'],
            stage=result['stage'],
            next_steps=result.get('next_steps')
        )
        
    except Exception as e:
        logger.error(f"Failed to start conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to start conversation")

@router.post("/message", response_model=ChatResponse)
async def send_message(request: ChatMessage):
    """Send a message in an ongoing conversation"""
    try:
        if not request.conversation_id:
            raise HTTPException(status_code=400, detail="Conversation ID required")
        
        result = await cerebrus_handler.process_user_message(
            conversation_id=request.conversation_id,
            user_message=request.message,
            attachments=request.attachments
        )
        
        if 'error' in result:
            if result.get('action') == 'restart_conversation':
                raise HTTPException(status_code=404, detail="Conversation not found")
            else:
                raise HTTPException(status_code=400, detail=result['error'])
        
        # Handle special actions
        response = ChatResponse(
            message=result['message'],
            conversation_id=request.conversation_id,
            stage=result.get('stage', 'unknown'),
            next_steps=result.get('next_steps'),
            action=result.get('action'),
            campaign_data=result.get('campaign_data')
        )
        
        # If the conversation is complete and ready for content generation
        if result.get('action') == 'start_content_generation':
            # Trigger content generation in the background
            import asyncio
            asyncio.create_task(_generate_first_content(
                request.conversation_id,
                result.get('campaign_data', {})
            ))
        
        # If user requested test content
        elif result.get('action') == 'generate_test_content':
            asyncio.create_task(_generate_test_content(
                request.conversation_id,
                result.get('campaign_data', {})
            ))
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process message: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")

@router.post("/upload")
async def upload_file(
    conversation_id: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload a file (image) for use in ad generation"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Only image files are allowed")
        
        # Save uploaded file
        import os
        upload_dir = "data/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, f"{conversation_id}_{file.filename}")
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {
            "message": f"Image '{file.filename}' uploaded successfully!",
            "file_path": file_path,
            "file_size": len(content),
            "content_type": file.content_type
        }
        
    except Exception as e:
        logger.error(f"File upload failed: {e}")
        raise HTTPException(status_code=500, detail="File upload failed")

@router.get("/conversation/{conversation_id}")
async def get_conversation_state(conversation_id: str):
    """Get current state of a conversation"""
    try:
        state = await cerebrus_handler.get_conversation_state(conversation_id)
        
        if not state:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "conversation_id": conversation_id,
            "stage": state.get('stage'),
            "collected_data": state.get('collected_data', {}),
            "created_at": state.get('created_at'),
            "last_activity": state.get('last_activity')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation state: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation state")

@router.delete("/conversation/{conversation_id}")
async def end_conversation(conversation_id: str):
    """End a conversation and clean up"""
    try:
        state = await cerebrus_handler.get_conversation_state(conversation_id)
        
        if not state:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Remove from active conversations
        if conversation_id in cerebrus_handler.conversation_states:
            del cerebrus_handler.conversation_states[conversation_id]
        
        return {"message": "Conversation ended successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to end conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to end conversation")

@router.get("/conversations/active")
async def get_active_conversations():
    """Get list of active conversations"""
    try:
        conversations = []
        
        for conv_id, state in cerebrus_handler.conversation_states.items():
            conversations.append({
                "conversation_id": conv_id,
                "user_id": state.get('user_id'),
                "stage": state.get('stage'),
                "type": state.get('type'),
                "created_at": state.get('created_at'),
                "last_activity": state.get('last_activity')
            })
        
        return {"conversations": conversations, "count": len(conversations)}
        
    except Exception as e:
        logger.error(f"Failed to get active conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active conversations")

# Background tasks
async def _generate_first_content(conversation_id: str, campaign_data: Dict[str, Any]):
    """Generate the first piece of content for a new campaign"""
    try:
        # Create campaign in database
        campaign_id = await data_manager.create_campaign(campaign_data)
        
        # Create content request
        request = ContentRequest(
            product_service_description=campaign_data.get('product_service_description', ''),
            target_audience=campaign_data.get('target_audience', ''),
            tone=campaign_data.get('tone', 'professional'),
            platforms=campaign_data.get('platforms', ['instagram']),
            content_type='feed_post'
        )
        
        # Generate content
        content = await content_generator.generate_content(request)
        
        logger.info(f"First content generated for conversation {conversation_id}")
        
        # Here you could send a notification back to the user
        # or update the conversation with the generated content
        
    except Exception as e:
        logger.error(f"Failed to generate first content: {e}")

async def _generate_test_content(conversation_id: str, campaign_data: Dict[str, Any]):
    """Generate test content for user review"""
    try:
        request = ContentRequest(
            product_service_description=campaign_data.get('product_service_description', ''),
            target_audience=campaign_data.get('target_audience', ''),
            tone=campaign_data.get('tone', 'professional'),
            platforms=campaign_data.get('platforms', ['instagram']),
            content_type='feed_post',
            additional_context='TEST CONTENT - NOT FOR POSTING'
        )
        
        content = await content_generator.generate_content(request)
        
        logger.info(f"Test content generated for conversation {conversation_id}")
        
        # In a real implementation, you'd send this back to the user
        # through the conversation system
        
    except Exception as e:
        logger.error(f"Failed to generate test content: {e}")