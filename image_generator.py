#!/usr/bin/env python3
"""
Image Generator - Handles AI image generation and custom image uploads
"""

import os
import logging
import requests
import base64
from pathlib import Path
from typing import Optional, Dict, Tuple
from PIL import Image
import io
import uuid
import aiofiles

logger = logging.getLogger(__name__)

class ImageGenerator:
    """Handles AI image generation and image processing"""

    def __init__(self):
        self.images_dir = Path("/app/data/images")
        self.images_dir.mkdir(parents=True, exist_ok=True)

        # Supported AI image generation services
        self.services = {
            "stable_diffusion": self._generate_stable_diffusion,
            "dalle": self._generate_dalle
        }

        # OpenAI API key for DALL·E (if available)
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

    async def generate_image(
        self,
        prompt: str,
        style: str = "realistic",
        service: str = "stable_diffusion",
        size: Tuple[int, int] = (1024, 1024)
    ) -> Optional[str]:
        """
        Generate an AI image based on the prompt

        Args:
            prompt: Text description for image generation
            style: Image style (realistic, artistic, cartoon, etc.)
            service: AI service to use (stable_diffusion, dalle)
            size: Image dimensions (width, height)

        Returns:
            Path to generated image or None if generation fails
        """
        try:
            # Enhance prompt based on style
            enhanced_prompt = self._enhance_prompt(prompt, style)

            # Generate image using specified service
            if service in self.services:
                image_path = await self.services[service](enhanced_prompt, size)
                if image_path:
                    logger.info(f"Generated image: {image_path}")
                    return str(image_path)
            else:
                logger.error(f"Unsupported image generation service: {service}")
                return None

        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return None

    def _enhance_prompt(self, base_prompt: str, style: str) -> str:
        """Enhance the base prompt with style-specific instructions"""
        style_prompts = {
            "realistic": "highly detailed, photorealistic, professional photography",
            "artistic": "artistic, creative, visually appealing, high quality",
            "cartoon": "cartoon style, animated, colorful, fun",
            "minimalist": "minimalist, clean, simple, modern",
            "vintage": "vintage style, retro, classic, nostalgic",
            "modern": "modern, contemporary, sleek, cutting-edge"
        }

        style_enhancement = style_prompts.get(style.lower(), style_prompts["realistic"])

        # Combine base prompt with style enhancement
        enhanced = f"{base_prompt}, {style_enhancement}, high quality, detailed"

        return enhanced

    async def _generate_stable_diffusion(self, prompt: str, size: Tuple[int, int]) -> Optional[Path]:
        """Generate image using Stable Diffusion (local or API)"""
        try:
            # For this implementation, we'll use a Stable Diffusion API
            # You can replace this with your preferred Stable Diffusion setup

            # Example using Stability AI API (requires API key)
            stability_api_key = os.getenv("STABILITY_API_KEY")

            if not stability_api_key:
                logger.warning("Stability API key not found, using mock generation")
                return await self._generate_mock_image(prompt, size)

            # API call to Stability AI
            response = requests.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-v1-6/text-to-image",
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {stability_api_key}"
                },
                json={
                    "text_prompts": [
                        {
                            "text": prompt,
                            "weight": 1
                        }
                    ],
                    "cfg_scale": 7,
                    "width": size[0],
                    "height": size[1],
                    "samples": 1,
                    "steps": 20,
                    "style_preset": "enhance"
                }
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("artifacts"):
                    # Save the generated image
                    image_data = base64.b64decode(data["artifacts"][0]["base64"])
                    image_path = self._save_image(image_data, prompt)
                    return image_path
            else:
                logger.error(f"Stable Diffusion API error: {response.status_code} - {response.text}")
                return await self._generate_mock_image(prompt, size)

        except Exception as e:
            logger.error(f"Error in Stable Diffusion generation: {e}")
            return await self._generate_mock_image(prompt, size)

    async def _generate_dalle(self, prompt: str, size: Tuple[int, int]) -> Optional[Path]:
        """Generate image using DALL·E"""
        try:
            if not self.openai_api_key:
                logger.warning("OpenAI API key not found, using mock generation")
                return await self._generate_mock_image(prompt, size)

            # OpenAI DALL·E API call
            response = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "dall-e-3",
                    "prompt": prompt,
                    "n": 1,
                    "size": f"{size[0]}x{size[1]}"
                }
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("data"):
                    # Download and save the image
                    image_url = data["data"][0]["url"]
                    image_response = requests.get(image_url)

                    if image_response.status_code == 200:
                        image_path = self._save_image(image_response.content, prompt)
                        return image_path
            else:
                logger.error(f"DALL·E API error: {response.status_code} - {response.text}")
                return await self._generate_mock_image(prompt, size)

        except Exception as e:
            logger.error(f"Error in DALL·E generation: {e}")
            return await self._generate_mock_image(prompt, size)

    async def _generate_mock_image(self, prompt: str, size: Tuple[int, int]) -> Path:
        """Generate a mock/placeholder image for testing"""
        try:
            # Create a simple gradient image as placeholder
            from PIL import ImageDraw

            img = Image.new('RGB', size, color='lightblue')
            draw = ImageDraw.Draw(img)

            # Add some text
            try:
                # Try to use a nice font, fall back to default
                font_size = min(size) // 20
                draw.text((size[0]//2, size[1]//2), "AI Generated",
                         fill='white', anchor='mm')
            except:
                pass

            # Save the image
            image_path = self._save_image_from_pil(img, prompt)
            logger.info(f"Generated mock image: {image_path}")
            return image_path

        except Exception as e:
            logger.error(f"Error generating mock image: {e}")
            return None

    def _save_image(self, image_data: bytes, prompt: str) -> Path:
        """Save image data to file"""
        # Generate unique filename
        filename = f"{uuid.uuid4()}.png"
        filepath = self.images_dir / filename

        # Save image
        with open(filepath, 'wb') as f:
            f.write(image_data)

        logger.info(f"Saved image to: {filepath}")
        return filepath

    def _save_image_from_pil(self, image: Image.Image, prompt: str) -> Path:
        """Save PIL image to file"""
        # Generate unique filename
        filename = f"{uuid.uuid4()}.png"
        filepath = self.images_dir / filename

        # Save image
        image.save(filepath, 'PNG')

        logger.info(f"Saved PIL image to: {filepath}")
        return filepath

    async def upload_image(self, image_file) -> Optional[str]:
        """
        Upload and save a custom image

        Args:
            image_file: File object or path to image

        Returns:
            Path to saved image or None if upload fails
        """
        try:
            if hasattr(image_file, 'read'):
                # File-like object
                image_data = await image_file.read()
            else:
                # File path
                async with aiofiles.open(image_file, 'rb') as f:
                    image_data = await f.read()

            # Validate image
            try:
                img = Image.open(io.BytesIO(image_data))
                img.verify()
            except Exception:
                logger.error("Invalid image file")
                return None

            # Generate unique filename
            filename = f"uploaded_{uuid.uuid4()}.png"
            filepath = self.images_dir / filename

            # Save image
            async with aiofiles.open(filepath, 'wb') as f:
                await f.write(image_data)

            logger.info(f"Uploaded image saved to: {filepath}")
            return str(filepath)

        except Exception as e:
            logger.error(f"Error uploading image: {e}")
            return None

    def get_image_info(self, image_path: str) -> Optional[Dict]:
        """Get information about an image"""
        try:
            if not os.path.exists(image_path):
                return None

            img = Image.open(image_path)
            return {
                "path": image_path,
                "size": img.size,
                "format": img.format,
                "mode": img.mode
            }
        except Exception as e:
            logger.error(f"Error getting image info: {e}")
            return None

    def list_images(self, limit: int = 50) -> List[Dict]:
        """List available images"""
        images = []

        try:
            image_files = list(self.images_dir.glob("*.png")) + list(self.images_dir.glob("*.jpg"))
            image_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            for img_file in image_files[:limit]:
                info = self.get_image_info(str(img_file))
                if info:
                    images.append(info)

        except Exception as e:
            logger.error(f"Error listing images: {e}")

        return images