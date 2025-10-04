"""
AI Content Generation System
Handles both image and caption generation for social media ads
"""

import asyncio
import logging
import hashlib
import os
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

from .image_generator import ImageGenerator
from .caption_generator import CaptionGenerator
from storage.data_manager import DataManager

logger = logging.getLogger(__name__)

@dataclass
class ContentRequest:
    """Request for content generation"""
    product_service_description: str
    target_audience: str
    tone: str
    platforms: List[str]
    content_type: str = "feed_post"  # 'feed_post' or 'story'
    user_image_path: Optional[str] = None
    additional_context: Optional[str] = None

@dataclass
class GeneratedContent:
    """Generated content result"""
    caption: str
    image_path: Optional[str]
    image_generation_prompt: Optional[str]
    prompt_hash: str
    platforms: List[str]
    content_type: str
    created_at: datetime

class ContentGenerator:
    """Main content generation orchestrator"""
    
    def __init__(self):
        self.image_generator = ImageGenerator()
        self.caption_generator = CaptionGenerator()
        self.data_manager = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize the content generator"""
        try:
            await self.image_generator.initialize()
            await self.caption_generator.initialize()
            self.data_manager = DataManager()
            await self.data_manager.initialize()
            self.initialized = True
            logger.info("Content generator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize content generator: {e}")
            raise
    
    async def generate_content(self, request: ContentRequest) -> GeneratedContent:
        """Generate complete content (caption + image) for social media"""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Create prompt hash for deduplication
            prompt_data = {
                'product_service': request.product_service_description,
                'audience': request.target_audience,
                'tone': request.tone,
                'platforms': sorted(request.platforms),
                'content_type': request.content_type
            }
            prompt_string = json.dumps(prompt_data, sort_keys=True)
            prompt_hash = hashlib.sha256(prompt_string.encode()).hexdigest()
            
            # Check if this prompt has been used before
            if await self.data_manager.prompt_exists(prompt_hash):
                logger.info(f"Prompt already exists: {prompt_hash}")
                # Generate slight variation
                request.additional_context = f"Variation {datetime.now().strftime('%H%M%S')}"
                prompt_string = json.dumps({**prompt_data, 'variation': request.additional_context}, sort_keys=True)
                prompt_hash = hashlib.sha256(prompt_string.encode()).hexdigest()
            
            # Generate caption
            caption = await self.caption_generator.generate_caption(
                product_service=request.product_service_description,
                target_audience=request.target_audience,
                tone=request.tone,
                platforms=request.platforms,
                content_type=request.content_type,
                additional_context=request.additional_context
            )
            
            # Generate or use provided image
            image_path = None
            image_generation_prompt = None
            
            if request.user_image_path:
                # Use user-provided image
                image_path = await self._process_user_image(request.user_image_path)
            else:
                # Generate AI image
                image_generation_prompt = await self.image_generator.create_image_prompt(
                    product_service=request.product_service_description,
                    target_audience=request.target_audience,
                    tone=request.tone,
                    content_type=request.content_type
                )
                
                image_path = await self.image_generator.generate_image(
                    prompt=image_generation_prompt,
                    content_type=request.content_type
                )
            
            # Create content object
            content = GeneratedContent(
                caption=caption,
                image_path=image_path,
                image_generation_prompt=image_generation_prompt,
                prompt_hash=prompt_hash,
                platforms=request.platforms,
                content_type=request.content_type,
                created_at=datetime.now()
            )
            
            # Store content in database
            await self.data_manager.store_content(content, prompt_data)
            
            logger.info(f"Successfully generated content with hash: {prompt_hash}")
            return content
            
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            raise
    
    async def _process_user_image(self, user_image_path: str) -> str:
        """Process and store user-uploaded image"""
        try:
            # Create unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"user_upload_{timestamp}_{os.path.basename(user_image_path)}"
            processed_path = os.path.join("data/images", filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(processed_path), exist_ok=True)
            
            # Copy/process image (could add resizing, format conversion, etc.)
            import shutil
            shutil.copy2(user_image_path, processed_path)
            
            return processed_path
            
        except Exception as e:
            logger.error(f"Failed to process user image: {e}")
            raise
    
    async def generate_variations(self, original_content: GeneratedContent, count: int = 3) -> List[GeneratedContent]:
        """Generate variations of existing content"""
        variations = []
        
        for i in range(count):
            try:
                # Generate caption variation
                variation_caption = await self.caption_generator.generate_variation(
                    original_caption=original_content.caption,
                    variation_number=i + 1
                )
                
                # Create new prompt hash for variation
                variation_data = {
                    'original_hash': original_content.prompt_hash,
                    'variation_number': i + 1,
                    'timestamp': datetime.now().isoformat()
                }
                variation_string = json.dumps(variation_data, sort_keys=True)
                variation_hash = hashlib.sha256(variation_string.encode()).hexdigest()
                
                # Create variation content
                variation = GeneratedContent(
                    caption=variation_caption,
                    image_path=original_content.image_path,  # Reuse same image
                    image_generation_prompt=original_content.image_generation_prompt,
                    prompt_hash=variation_hash,
                    platforms=original_content.platforms,
                    content_type=original_content.content_type,
                    created_at=datetime.now()
                )
                
                variations.append(variation)
                
            except Exception as e:
                logger.error(f"Failed to generate variation {i + 1}: {e}")
                continue
        
        return variations
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of content generation system"""
        try:
            health_status = {
                "initialized": self.initialized,
                "image_generator": await self.image_generator.health_check(),
                "caption_generator": await self.caption_generator.health_check()
            }
            
            if self.data_manager:
                health_status["data_manager"] = await self.data_manager.health_check()
            
            return health_status
            
        except Exception as e:
            return {"error": str(e), "status": "unhealthy"}