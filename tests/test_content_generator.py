"""
Tests for the AI content generator.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from src.ai.content_generator import ContentGenerator
from src.models.schemas import AdRequirements, Tone, Platform

class TestContentGenerator:
    """Test cases for ContentGenerator."""
    
    @pytest.fixture
    def content_generator(self):
        """Create a ContentGenerator instance for testing."""
        return ContentGenerator()
    
    @pytest.fixture
    def sample_requirements(self):
        """Sample ad requirements for testing."""
        return AdRequirements(
            product_description="Amazing new smartphone with AI features",
            tone=Tone.PROFESSIONAL,
            target_audience="tech enthusiasts and professionals",
            call_to_action="Order now and get 20% off!",
            hashtags=["smartphone", "AI", "tech"],
            platforms=[Platform.INSTAGRAM, Platform.TWITTER, Platform.LINKEDIN]
        )
    
    @pytest.mark.asyncio
    async def test_generate_ad_content(self, content_generator, sample_requirements):
        """Test generating complete ad content."""
        with patch.object(content_generator, '_generate_caption') as mock_caption, \
             patch.object(content_generator, 'generate_image') as mock_image:
            
            mock_caption.return_value = "Check out our amazing new smartphone! #smartphone #AI #tech"
            mock_image.return_value = "/path/to/generated/image.png"
            
            result = await content_generator.generate_ad_content(sample_requirements)
            
            assert result.caption is not None
            assert result.image_url is not None
            assert result.platforms == sample_requirements.platforms
            assert result.image_prompt is not None
    
    @pytest.mark.asyncio
    async def test_generate_caption(self, content_generator, sample_requirements):
        """Test caption generation."""
        with patch.object(content_generator.openai_client.chat.completions, 'create') as mock_create:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "Amazing smartphone with AI features! Perfect for tech enthusiasts. Order now and get 20% off!"
            mock_create.return_value = mock_response
            
            caption = await content_generator._generate_caption(sample_requirements)
            
            assert "smartphone" in caption.lower()
            assert "AI" in caption
            assert len(caption) > 0
    
    @pytest.mark.asyncio
    async def test_create_image_prompt(self, content_generator, sample_requirements):
        """Test image prompt creation."""
        prompt = await content_generator._create_image_prompt(sample_requirements)
        
        assert "smartphone" in prompt.lower()
        assert "AI" in prompt
        assert "professional" in prompt.lower()
        assert len(prompt) > 0
    
    @pytest.mark.asyncio
    async def test_generate_image(self, content_generator):
        """Test image generation."""
        with patch.object(content_generator.openai_client.images, 'generate') as mock_generate:
            mock_response = Mock()
            mock_response.data = [Mock()]
            mock_response.data[0].url = "https://example.com/image.png"
            mock_generate.return_value = mock_response
            
            with patch.object(content_generator, '_download_and_save_image') as mock_download:
                mock_download.return_value = "/path/to/saved/image.png"
                
                result = await content_generator.generate_image("test prompt")
                
                assert result == "/path/to/saved/image.png"
    
    @pytest.mark.asyncio
    async def test_process_uploaded_image(self, content_generator):
        """Test processing uploaded images."""
        # Mock image data
        mock_image_data = b"fake_image_data"
        
        with patch('PIL.Image.open') as mock_open, \
             patch('PIL.Image.Image.save') as mock_save:
            
            mock_image = Mock()
            mock_image.size = (800, 600)
            mock_open.return_value = mock_image
            
            result = await content_generator.process_uploaded_image(mock_image_data)
            
            assert result.endswith(".png")
            mock_save.assert_called_once()