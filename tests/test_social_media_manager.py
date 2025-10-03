"""
Tests for the social media manager.
"""

import pytest
import json
import os
from unittest.mock import Mock, patch, mock_open
from src.mcp.social_media_manager import SocialMediaManager
from src.models.schemas import Platform, GeneratedContent, PostType

class TestSocialMediaManager:
    """Test cases for SocialMediaManager."""
    
    @pytest.fixture
    def social_media_manager(self):
        """Create a SocialMediaManager instance for testing."""
        return SocialMediaManager()
    
    @pytest.fixture
    def sample_content(self):
        """Sample generated content for testing."""
        return GeneratedContent(
            caption="Check out our amazing product! #amazing #product",
            image_url="/path/to/image.png",
            image_prompt="A beautiful product image",
            platforms=[Platform.INSTAGRAM, Platform.TWITTER]
        )
    
    @pytest.fixture
    def sample_credentials(self):
        """Sample credentials for testing."""
        return {
            "access_token": "test_access_token",
            "user_id": "test_user_id"
        }
    
    @pytest.mark.asyncio
    async def test_store_credentials(self, social_media_manager, sample_credentials):
        """Test storing credentials."""
        with patch.object(social_media_manager, '_test_credentials') as mock_test:
            mock_test.return_value = True
            
            with patch('builtins.open', mock_open()) as mock_file:
                result = await social_media_manager.store_credentials(
                    Platform.INSTAGRAM, 
                    sample_credentials
                )
                
                assert result is True
                mock_file.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_post_content(self, social_media_manager, sample_content):
        """Test posting content to social media."""
        with patch.object(social_media_manager, '_load_credentials') as mock_load, \
             patch.object(social_media_manager.clients[Platform.INSTAGRAM], 'post_content') as mock_post, \
             patch.object(social_media_manager, '_log_post') as mock_log:
            
            mock_load.return_value = {"access_token": "test_token"}
            mock_post.return_value = {"success": True, "post_id": "12345"}
            
            result = await social_media_manager.post_content(
                Platform.INSTAGRAM, 
                sample_content, 
                PostType.FEED
            )
            
            assert result["success"] is True
            assert result["post_id"] == "12345"
            mock_log.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_post_content_no_credentials(self, social_media_manager, sample_content):
        """Test posting content without credentials."""
        with patch.object(social_media_manager, '_load_credentials') as mock_load:
            mock_load.return_value = None
            
            result = await social_media_manager.post_content(
                Platform.INSTAGRAM, 
                sample_content, 
                PostType.FEED
            )
            
            assert result["success"] is False
            assert "No credentials found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_get_posting_stats(self, social_media_manager):
        """Test getting posting statistics."""
        # Create mock log file
        mock_log_data = [
            '{"platform": "instagram", "success": true, "timestamp": "2024-01-01T00:00:00"}',
            '{"platform": "twitter", "success": false, "timestamp": "2024-01-01T00:00:00"}',
            '{"platform": "instagram", "success": true, "timestamp": "2024-01-01T00:00:00"}'
        ]
        
        with patch('builtins.open', mock_open(read_data='\n'.join(mock_log_data))):
            stats = await social_media_manager.get_posting_stats()
            
            assert stats["total_posts"] == 3
            assert stats["successful_posts"] == 2
            assert stats["failed_posts"] == 1
            assert stats["platforms"]["instagram"]["successful"] == 2
            assert stats["platforms"]["twitter"]["failed"] == 1
    
    def test_encrypt_decrypt_credentials(self, social_media_manager, sample_credentials):
        """Test credential encryption and decryption."""
        encrypted = social_media_manager._encrypt_credentials(sample_credentials)
        decrypted = social_media_manager._decrypt_credentials(encrypted)
        
        assert decrypted == sample_credentials
        assert encrypted != json.dumps(sample_credentials)  # Should be encoded