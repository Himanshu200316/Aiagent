"""
Pydantic schemas for data validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class Platform(str, Enum):
    """Supported social media platforms."""
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"

class PostType(str, Enum):
    """Types of posts."""
    FEED = "feed"
    STORY = "story"

class Tone(str, Enum):
    """Content tone options."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"
    PLAYFUL = "playful"

class CredentialsRequest(BaseModel):
    """Request to store social media credentials."""
    platform: Platform
    credentials: Dict[str, Any]
    user_id: Optional[str] = None

class AdRequirements(BaseModel):
    """Requirements for generating an ad."""
    product_description: str
    tone: Tone = Tone.PROFESSIONAL
    target_audience: str
    call_to_action: Optional[str] = None
    hashtags: Optional[List[str]] = None
    platforms: List[Platform] = [Platform.INSTAGRAM, Platform.TWITTER, Platform.LINKEDIN]

class ImageRequest(BaseModel):
    """Request for image generation or upload."""
    type: str = Field(..., description="'generate' for AI generation, 'upload' for custom image")
    prompt: Optional[str] = None
    image_data: Optional[str] = None  # Base64 encoded image
    style: Optional[str] = None

class GeneratedContent(BaseModel):
    """Generated ad content."""
    caption: str
    image_url: Optional[str] = None
    image_prompt: Optional[str] = None
    platforms: List[Platform]
    created_at: datetime = Field(default_factory=datetime.now)

class PostingSchedule(BaseModel):
    """Posting schedule configuration."""
    enabled: bool = True
    time: str = "00:00"  # HH:MM format
    timezone: str = "UTC"
    platforms: List[Platform] = [Platform.INSTAGRAM, Platform.TWITTER, Platform.LINKEDIN]

class PostHistory(BaseModel):
    """Record of posted content."""
    id: str
    content: GeneratedContent
    platforms_posted: List[Platform]
    posted_at: datetime
    success: bool
    error_message: Optional[str] = None

class UserInteraction(BaseModel):
    """User interaction via Cerebrus API."""
    user_id: str
    message: str
    context: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class AgentResponse(BaseModel):
    """Response from the agent."""
    message: str
    action_required: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    next_steps: Optional[List[str]] = None