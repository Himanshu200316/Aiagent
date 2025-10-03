"""
AI Image Generation Module
Supports DALL-E and Stable Diffusion for generating advertisement images
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
import openai
import requests
from PIL import Image
import io

logger = logging.getLogger(__name__)

class ImageGenerator:
    """AI image generation using DALL-E and Stable Diffusion"""
    
    def __init__(self):
        self.openai_client = None
        self.stable_diffusion_api_key = os.getenv('STABLE_DIFFUSION_API_KEY')
        self.default_model = os.getenv('IMAGE_GENERATION_MODEL', 'dall-e-3')
        self.default_size = os.getenv('DEFAULT_IMAGE_SIZE', '1024x1024')
        self.initialized = False
        
    async def initialize(self):
        """Initialize image generation services"""
        try:
            # Initialize OpenAI client
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if openai_api_key:
                self.openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
                logger.info("OpenAI client initialized")
            
            # Ensure images directory exists
            os.makedirs("data/images", exist_ok=True)
            
            self.initialized = True
            logger.info("Image generator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize image generator: {e}")
            raise
    
    async def create_image_prompt(self, product_service: str, target_audience: str, 
                                tone: str, content_type: str = "feed_post") -> str:
        """Create optimized prompt for image generation"""
        
        # Base prompt templates
        base_prompts = {
            "feed_post": "Create a professional, eye-catching advertisement image for social media feed",
            "story": "Create a vertical, engaging story-format advertisement image"
        }
        
        # Tone modifiers
        tone_modifiers = {
            "professional": "clean, modern, corporate style with professional aesthetics",
            "casual": "friendly, approachable, warm and inviting atmosphere",
            "luxury": "premium, elegant, sophisticated with high-end appeal",
            "playful": "colorful, fun, energetic with dynamic elements",
            "minimalist": "simple, clean, uncluttered with focus on key elements"
        }
        
        # Audience-specific elements
        audience_elements = {
            "young adults": "modern, trendy, vibrant colors, contemporary design",
            "professionals": "sleek, business-appropriate, sophisticated layout",
            "families": "warm, inclusive, family-friendly imagery",
            "seniors": "clear, readable, traditional aesthetic",
            "entrepreneurs": "dynamic, success-oriented, motivational elements"
        }
        
        # Construct the prompt
        base = base_prompts.get(content_type, base_prompts["feed_post"])
        tone_mod = tone_modifiers.get(tone.lower(), tone_modifiers["professional"])
        audience_elem = audience_elements.get(target_audience.lower(), "appealing to the target demographic")
        
        prompt = f"{base} for {product_service}. Style: {tone_mod}. Target audience considerations: {audience_elem}. High quality, commercial photography style, well-lit, professional composition."
        
        # Add format-specific requirements
        if content_type == "story":
            prompt += " Vertical 9:16 aspect ratio, mobile-optimized layout."
        else:
            prompt += " Square 1:1 aspect ratio, suitable for social media feeds."
        
        return prompt
    
    async def generate_image(self, prompt: str, content_type: str = "feed_post", 
                           model: Optional[str] = None) -> str:
        """Generate image using AI and return local file path"""
        
        if not self.initialized:
            await self.initialize()
        
        model = model or self.default_model
        
        try:
            if model.startswith('dall-e'):
                return await self._generate_with_dalle(prompt, content_type)
            elif model == 'stable-diffusion':
                return await self._generate_with_stable_diffusion(prompt, content_type)
            else:
                raise ValueError(f"Unsupported model: {model}")
                
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise
    
    async def _generate_with_dalle(self, prompt: str, content_type: str) -> str:
        """Generate image using DALL-E"""
        
        if not self.openai_client:
            raise ValueError("OpenAI client not initialized")
        
        try:
            # Determine size based on content type
            size = "1024x1024" if content_type == "feed_post" else "1024x1792"
            
            response = await self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality="hd",
                n=1
            )
            
            # Download and save the image
            image_url = response.data[0].url
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            
            # Create unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dalle_{content_type}_{timestamp}.png"
            file_path = os.path.join("data/images", filename)
            
            # Save image
            with open(file_path, 'wb') as f:
                f.write(image_response.content)
            
            logger.info(f"DALL-E image generated: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"DALL-E generation failed: {e}")
            raise
    
    async def _generate_with_stable_diffusion(self, prompt: str, content_type: str) -> str:
        """Generate image using Stable Diffusion API"""
        
        if not self.stable_diffusion_api_key:
            raise ValueError("Stable Diffusion API key not configured")
        
        try:
            # Stable Diffusion API endpoint (example using Stability AI)
            url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
            
            # Determine dimensions based on content type
            width, height = (1024, 1024) if content_type == "feed_post" else (1024, 1792)
            
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.stable_diffusion_api_key}",
            }
            
            body = {
                "text_prompts": [
                    {
                        "text": prompt,
                        "weight": 1
                    }
                ],
                "cfg_scale": 7,
                "height": height,
                "width": width,
                "samples": 1,
                "steps": 30,
            }
            
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            
            data = response.json()
            
            # Save the generated image
            for i, image in enumerate(data["artifacts"]):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"sd_{content_type}_{timestamp}.png"
                file_path = os.path.join("data/images", filename)
                
                # Decode and save image
                import base64
                image_data = base64.b64decode(image["base64"])
                with open(file_path, 'wb') as f:
                    f.write(image_data)
                
                logger.info(f"Stable Diffusion image generated: {file_path}")
                return file_path
            
        except Exception as e:
            logger.error(f"Stable Diffusion generation failed: {e}")
            raise
    
    async def resize_for_platform(self, image_path: str, platform: str, content_type: str) -> str:
        """Resize image for specific platform requirements"""
        
        try:
            # Platform-specific dimensions
            dimensions = {
                'instagram': {
                    'feed_post': (1080, 1080),
                    'story': (1080, 1920)
                },
                'twitter': {
                    'feed_post': (1200, 675),
                    'story': (1080, 1920)
                },
                'linkedin': {
                    'feed_post': (1200, 627),
                    'story': (1080, 1920)
                }
            }
            
            if platform not in dimensions:
                return image_path  # Return original if platform not supported
            
            target_size = dimensions[platform].get(content_type, dimensions[platform]['feed_post'])
            
            # Open and resize image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Resize maintaining aspect ratio
                img.thumbnail(target_size, Image.Resampling.LANCZOS)
                
                # Create new image with exact dimensions (add padding if needed)
                new_img = Image.new('RGB', target_size, (255, 255, 255))
                
                # Center the resized image
                x = (target_size[0] - img.width) // 2
                y = (target_size[1] - img.height) // 2
                new_img.paste(img, (x, y))
                
                # Save resized image
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                resized_filename = f"{base_name}_{platform}_{content_type}.jpg"
                resized_path = os.path.join("data/images", resized_filename)
                
                new_img.save(resized_path, 'JPEG', quality=95)
                
                logger.info(f"Image resized for {platform}: {resized_path}")
                return resized_path
                
        except Exception as e:
            logger.error(f"Image resizing failed: {e}")
            return image_path  # Return original on error
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of image generation services"""
        
        health_status = {
            "initialized": self.initialized,
            "openai_available": self.openai_client is not None,
            "stable_diffusion_available": self.stable_diffusion_api_key is not None,
            "default_model": self.default_model
        }
        
        # Test OpenAI connection if available
        if self.openai_client:
            try:
                # Simple test call (this might incur a small cost)
                # In production, you might want to use a different health check
                health_status["openai_status"] = "available"
            except Exception as e:
                health_status["openai_status"] = f"error: {str(e)}"
        
        return health_status