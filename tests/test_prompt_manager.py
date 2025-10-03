"""
Tests for the prompt manager.
"""

import pytest
import json
import os
from unittest.mock import patch, mock_open
from src.storage.prompt_manager import PromptManager

class TestPromptManager:
    """Test cases for PromptManager."""
    
    @pytest.fixture
    def prompt_manager(self):
        """Create a PromptManager instance for testing."""
        with patch('os.makedirs'):
            return PromptManager()
    
    @pytest.mark.asyncio
    async def test_store_prompt(self, prompt_manager):
        """Test storing a prompt."""
        mock_data = {
            "prompts": [],
            "metadata": {
                "created_at": "2024-01-01T00:00:00",
                "total_prompts": 0
            }
        }
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.load', return_value=mock_data) as mock_load, \
                 patch('json.dump') as mock_dump:
                
                result = await prompt_manager.store_prompt(
                    "Amazing smartphone",
                    "professional",
                    "tech enthusiasts",
                    "Check out our amazing smartphone!"
                )
                
                assert result is True
                mock_dump.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_check_duplicate(self, prompt_manager):
        """Test checking for duplicate prompts."""
        mock_data = {
            "prompts": [
                {
                    "hash": "abc123",
                    "product_description": "Amazing smartphone",
                    "tone": "professional",
                    "target_audience": "tech enthusiasts"
                }
            ]
        }
        
        with patch('builtins.open', mock_open()):
            with patch('json.load', return_value=mock_data):
                # Test with same prompt (should be duplicate)
                is_duplicate = await prompt_manager.check_duplicate(
                    "Amazing smartphone",
                    "professional", 
                    "tech enthusiasts"
                )
                assert is_duplicate is True
                
                # Test with different prompt (should not be duplicate)
                is_duplicate = await prompt_manager.check_duplicate(
                    "Different product",
                    "casual",
                    "general audience"
                )
                assert is_duplicate is False
    
    @pytest.mark.asyncio
    async def test_get_prompt_suggestions(self, prompt_manager):
        """Test getting prompt suggestions."""
        mock_data = {
            "prompts": [
                {
                    "product_description": "Amazing smartphone with AI",
                    "tone": "professional",
                    "target_audience": "tech enthusiasts",
                    "created_at": "2024-01-01T00:00:00"
                },
                {
                    "product_description": "Beautiful smartphone case",
                    "tone": "casual",
                    "target_audience": "general audience",
                    "created_at": "2024-01-01T00:00:00"
                }
            ]
        }
        
        with patch('builtins.open', mock_open()):
            with patch('json.load', return_value=mock_data):
                suggestions = await prompt_manager.get_prompt_suggestions("smartphone")
                
                assert len(suggestions) > 0
                assert suggestions[0]["product_description"] == "Amazing smartphone with AI"
                assert "similarity" in suggestions[0]
    
    @pytest.mark.asyncio
    async def test_log_posting(self, prompt_manager):
        """Test logging posting activity."""
        with patch('builtins.open', mock_open()) as mock_file:
            await prompt_manager.log_posting(
                "abc123",
                ["instagram", "twitter"],
                True,
                None
            )
            
            mock_file.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_posting_history(self, prompt_manager):
        """Test getting posting history."""
        mock_log_data = [
            '{"timestamp": "2024-01-01T00:00:00", "platforms": ["instagram"]}',
            '{"timestamp": "2024-01-02T00:00:00", "platforms": ["twitter"]}'
        ]
        
        with patch('builtins.open', mock_open(read_data='\n'.join(mock_log_data))):
            history = await prompt_manager.get_posting_history(10)
            
            assert len(history) == 2
            assert history[0]["platforms"] == ["instagram"]
            assert history[1]["platforms"] == ["twitter"]
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, prompt_manager):
        """Test getting statistics."""
        mock_prompts_data = {
            "prompts": [
                {"tone": "professional", "used_count": 5},
                {"tone": "casual", "used_count": 3},
                {"tone": "professional", "used_count": 2}
            ]
        }
        
        mock_history_data = [
            '{"success": true, "platforms": ["instagram"]}',
            '{"success": false, "platforms": ["twitter"]}',
            '{"success": true, "platforms": ["linkedin"]}'
        ]
        
        with patch.object(prompt_manager, 'get_posting_history', return_value=[
            {"success": True, "platforms": ["instagram"]},
            {"success": False, "platforms": ["twitter"]},
            {"success": True, "platforms": ["linkedin"]}
        ]):
            with patch('builtins.open', mock_open()):
                with patch('json.load', return_value=mock_prompts_data):
                    stats = await prompt_manager.get_statistics()
                    
                    assert stats["total_prompts"] == 3
                    assert stats["total_postings"] == 3
                    assert stats["successful_postings"] == 2
                    assert stats["failed_postings"] == 1
                    assert stats["most_used_tone"] == "professional"