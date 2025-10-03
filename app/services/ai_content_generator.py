"""
AI Content Generation Service
Handles both image generation and caption creation
"""
import openai
import requests
import json
import hashlib
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from PIL import Image
import io
from diffusers import StableDiffusionPipeline
import torch
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger('ai_content_generator')

class AIContentGenerator:
    """AI-powered content generation service"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.openai_api_key)
        self.sd_pipeline = None
        self._initialize_stable_diffusion()
    
    def _initialize_stable_diffusion(self):
        """Initialize Stable Diffusion pipeline"""
        try:
            if torch.cuda.is_available():
                device = "cuda"
                torch_dtype = torch.float16
            else:
                device = "cpu"
                torch_dtype = torch.float32
            
            self.sd_pipeline = StableDiffusionPipeline.from_pretrained(
                settings.stable_diffusion_model,
                torch_dtype=torch_dtype,
                safety_checker=None,
                requires_safety_checker=False
            ).to(device)
            
            logger.info(f"Stable Diffusion initialized on {device}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Stable Diffusion: {str(e)}")
            self.sd_pipeline = None
    
    async def generate_caption(self, 
                             product_description: str,
                             tone: str = "professional",
                             target_audience: str = "general",
                             platform: str = "instagram",
                             max_length: int = 200) -> Dict[str, Any]:
        """Generate AI-powered caption"""
        try:
            prompt = self._build_caption_prompt(
                product_description, tone, target_audience, platform, max_length
            )
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional social media marketing expert who creates engaging, platform-specific captions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_length,
                temperature=0.7
            )
            
            caption = response.choices[0].message.content.strip()
            caption_hash = self._generate_content_hash(caption)
            
            logger.info(f"Generated caption for {platform}: {caption[:50]}...")
            
            return {
                'success': True,
                'caption': caption,
                'caption_hash': caption_hash,
                'platform': platform,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate caption: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def generate_image(self, 
                           prompt: str,
                           style: str = "professional",
                           size: tuple = (1024, 1024),
                           quality: int = 95) -> Dict[str, Any]:
        """Generate AI image using Stable Diffusion"""
        try:
            if not self.sd_pipeline:
                return {
                    'success': False,
                    'error': 'Stable Diffusion not initialized'
                }
            
            # Enhance prompt with style
            enhanced_prompt = self._enhance_image_prompt(prompt, style)
            
            # Generate image
            image = self.sd_pipeline(
                prompt=enhanced_prompt,
                height=size[1],
                width=size[0],
                num_inference_steps=50,
                guidance_scale=7.5
            ).images[0]
            
            # Save image
            image_path = await self._save_generated_image(image, prompt)
            
            logger.info(f"Generated image: {image_path}")
            
            return {
                'success': True,
                'image_path': image_path,
                'prompt': enhanced_prompt,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate image: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def generate_complete_content(self,
                                      product_description: str,
                                      tone: str = "professional",
                                      target_audience: str = "general",
                                      platforms: List[str] = ["instagram"],
                                      generate_image: bool = True,
                                      image_style: str = "professional") -> Dict[str, Any]:
        """Generate complete content (image + captions for all platforms)"""
        try:
            results = {
                'success': True,
                'content_id': self._generate_content_id(),
                'generated_at': datetime.now().isoformat(),
                'image': None,
                'captions': {}
            }
            
            # Generate image if requested
            if generate_image:
                image_result = await self.generate_image(
                    prompt=product_description,
                    style=image_style
                )
                
                if image_result['success']:
                    results['image'] = image_result
                else:
                    logger.warning(f"Image generation failed: {image_result['error']}")
            
            # Generate captions for each platform
            for platform in platforms:
                caption_result = await self.generate_caption(
                    product_description=product_description,
                    tone=tone,
                    target_audience=target_audience,
                    platform=platform
                )
                
                if caption_result['success']:
                    results['captions'][platform] = caption_result
                else:
                    logger.warning(f"Caption generation failed for {platform}: {caption_result['error']}")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to generate complete content: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _build_caption_prompt(self, 
                            product_description: str,
                            tone: str,
                            target_audience: str,
                            platform: str,
                            max_length: int) -> str:
        """Build prompt for caption generation"""
        
        platform_specifics = {
            'instagram': 'Instagram (visual, hashtag-friendly, engaging)',
            'twitter': 'Twitter/X (concise, trending topics, conversational)',
            'linkedin': 'LinkedIn (professional, business-focused, informative)'
        }
        
        tone_descriptions = {
            'professional': 'professional and business-like',
            'casual': 'casual and friendly',
            'humorous': 'humorous and entertaining',
            'inspirational': 'inspirational and motivational',
            'educational': 'educational and informative'
        }
        
        platform_desc = platform_specifics.get(platform, platform)
        tone_desc = tone_descriptions.get(tone, tone)
        
        prompt = f"""
        Create a {tone_desc} social media caption for {platform_desc}.
        
        Product/Service: {product_description}
        Target Audience: {target_audience}
        Platform: {platform_desc}
        Tone: {tone_desc}
        Max Length: {max_length} characters
        
        Requirements:
        - Platform-appropriate format and style
        - Engaging and compelling
        - Include relevant hashtags if appropriate for the platform
        - Match the specified tone
        - Appeal to the target audience
        - Stay within character limit
        
        Generate the caption now:
        """
        
        return prompt
    
    def _enhance_image_prompt(self, prompt: str, style: str) -> str:
        """Enhance image prompt with style modifiers"""
        
        style_modifiers = {
            'professional': 'professional photography, clean, modern, high quality, commercial',
            'casual': 'casual, friendly, approachable, natural lighting',
            'luxury': 'luxury, premium, elegant, sophisticated, high-end',
            'minimalist': 'minimalist, clean, simple, modern, white background',
            'vibrant': 'vibrant colors, energetic, dynamic, colorful',
            'artistic': 'artistic, creative, unique, stylized, artistic photography'
        }
        
        modifier = style_modifiers.get(style, 'professional photography, high quality')
        
        return f"{prompt}, {modifier}, 8k resolution, detailed, sharp focus"
    
    async def _save_generated_image(self, image: Image.Image, prompt: str) -> str:
        """Save generated image to file system"""
        try:
            # Create filename from prompt hash
            prompt_hash = self._generate_content_hash(prompt)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_{timestamp}_{prompt_hash[:8]}.png"
            
            # Ensure images directory exists
            os.makedirs(settings.images_dir, exist_ok=True)
            
            # Save image
            image_path = os.path.join(settings.images_dir, filename)
            image.save(image_path, "PNG", quality=settings.image_quality)
            
            return image_path
            
        except Exception as e:
            logger.error(f"Failed to save generated image: {str(e)}")
            raise
    
    def _generate_content_hash(self, content: str) -> str:
        """Generate hash for content"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def _generate_content_id(self) -> str:
        """Generate unique content ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]
        return f"content_{timestamp}_{random_suffix}"
    
    async def analyze_uploaded_image(self, image_path: str) -> Dict[str, Any]:
        """Analyze uploaded image and suggest captions"""
        try:
            # Use OpenAI Vision API to analyze image
            with open(image_path, 'rb') as image_file:
                response = self.openai_client.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Analyze this image and provide: 1) A brief description, 2) Suggested caption themes, 3) Recommended hashtags, 4) Target audience suggestions"
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_file.read().encode('base64')}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=500
                )
            
            analysis = response.choices[0].message.content
            
            return {
                'success': True,
                'analysis': analysis,
                'image_path': image_path
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze uploaded image: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }