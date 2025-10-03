"""
AI-powered content generation for social media ads.
"""

import openai
import base64
import io
import hashlib
from typing import Optional, List
from PIL import Image
import os
from datetime import datetime

from src.config.settings import settings
from src.models.schemas import AdRequirements, GeneratedContent, Platform, Tone

class ContentGenerator:
    """AI content generator for ads."""
    
    def __init__(self):
        self.openai_client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        self.storage_path = settings.storage_path
        
    async def initialize(self):
        """Initialize the content generator."""
        # Ensure storage directories exist
        os.makedirs(f"{self.storage_path}/images", exist_ok=True)
        os.makedirs(f"{self.storage_path}/generated", exist_ok=True)
        
    async def generate_ad_content(self, requirements: AdRequirements) -> GeneratedContent:
        """Generate complete ad content including caption and image."""
        
        # Generate caption
        caption = await self._generate_caption(requirements)
        
        # Generate image
        image_prompt = await self._create_image_prompt(requirements)
        image_url = await self.generate_image(image_prompt)
        
        return GeneratedContent(
            caption=caption,
            image_url=image_url,
            image_prompt=image_prompt,
            platforms=requirements.platforms
        )
    
    async def _generate_caption(self, requirements: AdRequirements) -> str:
        """Generate social media caption based on requirements."""
        
        tone_instructions = {
            Tone.PROFESSIONAL: "Use a professional, business-focused tone",
            Tone.CASUAL: "Use a casual, conversational tone",
            Tone.FRIENDLY: "Use a warm, friendly tone",
            Tone.AUTHORITATIVE: "Use an authoritative, expert tone",
            Tone.PLAYFUL: "Use a playful, fun tone"
        }
        
        prompt = f"""
        Create a compelling social media advertisement caption for the following product/service:
        
        Product/Service: {requirements.product_description}
        Target Audience: {requirements.target_audience}
        Tone: {tone_instructions.get(requirements.tone, 'professional')}
        Call to Action: {requirements.call_to_action or 'Learn more'}
        
        Requirements:
        - Keep it engaging and attention-grabbing
        - Include relevant hashtags (3-5 hashtags)
        - Make it platform-appropriate for Instagram, Twitter, and LinkedIn
        - Include a clear call to action
        - Length: 100-200 characters for Twitter compatibility
        
        Format the response as just the caption text, no additional formatting.
        """
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert social media marketing copywriter."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            caption = response.choices[0].message.content.strip()
            
            # Add hashtags if not present
            if requirements.hashtags:
                hashtag_text = " ".join([f"#{tag}" for tag in requirements.hashtags])
                caption = f"{caption}\n\n{hashtag_text}"
            
            return caption
            
        except Exception as e:
            # Fallback caption if AI generation fails
            return f"Discover {requirements.product_description}! Perfect for {requirements.target_audience}. {requirements.call_to_action or 'Learn more today!'}"
    
    async def _create_image_prompt(self, requirements: AdRequirements) -> str:
        """Create a prompt for image generation."""
        
        prompt = f"""
        Create a professional, eye-catching advertisement image for:
        {requirements.product_description}
        
        Target audience: {requirements.target_audience}
        Style: Modern, clean, professional
        Colors: Vibrant but not overwhelming
        Composition: Centered, balanced, Instagram-friendly square format
        
        The image should be suitable for social media advertising and convey the essence of the product/service.
        """
        
        return prompt.strip()
    
    async def generate_image(self, prompt: str, style: Optional[str] = None) -> str:
        """Generate image using DALL-E."""
        
        try:
            # Add style to prompt if provided
            if style:
                prompt = f"{prompt}, {style} style"
            
            response = await self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            
            image_url = response.data[0].url
            
            # Download and save image locally
            local_path = await self._download_and_save_image(image_url, prompt)
            
            return local_path
            
        except Exception as e:
            print(f"Error generating image: {e}")
            # Return a placeholder or default image
            return await self._get_placeholder_image()
    
    async def _download_and_save_image(self, image_url: str, prompt: str) -> str:
        """Download image from URL and save locally."""
        
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(image_url)
            response.raise_for_status()
            
            # Create filename based on prompt hash
            prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_{timestamp}_{prompt_hash}.png"
            
            # Save image
            image_path = f"{self.storage_path}/images/{filename}"
            with open(image_path, "wb") as f:
                f.write(response.content)
            
            return image_path
    
    async def process_uploaded_image(self, image_data: bytes) -> str:
        """Process uploaded image and save locally."""
        
        try:
            # Validate image
            image = Image.open(io.BytesIO(image_data))
            
            # Resize if too large
            max_size = (1024, 1024)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"uploaded_{timestamp}.png"
            
            # Save image
            image_path = f"{self.storage_path}/images/{filename}"
            image.save(image_path, "PNG")
            
            return image_path
            
        except Exception as e:
            raise Exception(f"Error processing uploaded image: {e}")
    
    async def _get_placeholder_image(self) -> str:
        """Get placeholder image when generation fails."""
        
        # Create a simple placeholder image
        placeholder_path = f"{self.storage_path}/images/placeholder.png"
        
        if not os.path.exists(placeholder_path):
            # Create a simple colored placeholder
            placeholder = Image.new('RGB', (1024, 1024), color='lightblue')
            placeholder.save(placeholder_path)
        
        return placeholder_path