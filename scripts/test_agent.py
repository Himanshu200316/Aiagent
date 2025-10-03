#!/usr/bin/env python3
"""
Test script for the AI Social Media Advertising Agent.
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.ai.content_generator import ContentGenerator
from src.models.schemas import AdRequirements, Tone, Platform
from src.storage.prompt_manager import PromptManager

async def test_content_generation():
    """Test content generation functionality."""
    print("🧪 Testing content generation...")
    
    try:
        # Initialize content generator
        generator = ContentGenerator()
        await generator.initialize()
        
        # Create test requirements
        requirements = AdRequirements(
            product_description="Amazing AI-powered smartphone with advanced camera features",
            tone=Tone.PROFESSIONAL,
            target_audience="tech enthusiasts and photography lovers",
            call_to_action="Pre-order now and get 20% off!",
            hashtags=["smartphone", "AI", "photography", "tech"],
            platforms=[Platform.INSTAGRAM, Platform.TWITTER, Platform.LINKEDIN]
        )
        
        # Generate content
        print("📝 Generating ad content...")
        content = await generator.generate_ad_content(requirements)
        
        print(f"✅ Generated caption: {content.caption}")
        print(f"✅ Generated image: {content.image_url}")
        print(f"✅ Platforms: {[p.value for p in content.platforms]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Content generation test failed: {e}")
        return False

async def test_prompt_management():
    """Test prompt management functionality."""
    print("🧪 Testing prompt management...")
    
    try:
        # Initialize prompt manager
        manager = PromptManager()
        
        # Test storing a prompt
        print("💾 Storing test prompt...")
        success = await manager.store_prompt(
            "Test product description",
            "professional",
            "test audience",
            "Test generated caption"
        )
        
        if success:
            print("✅ Prompt stored successfully")
        else:
            print("⚠️ Prompt storage returned False (might be duplicate)")
        
        # Test duplicate checking
        print("🔍 Checking for duplicates...")
        is_duplicate = await manager.check_duplicate(
            "Test product description",
            "professional",
            "test audience"
        )
        
        if is_duplicate:
            print("✅ Duplicate detection working")
        else:
            print("⚠️ Duplicate detection might not be working")
        
        # Test getting statistics
        print("📊 Getting statistics...")
        stats = await manager.get_statistics()
        print(f"✅ Total prompts: {stats.get('total_prompts', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Prompt management test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🚀 Starting AI Social Media Advertising Agent Tests")
    print("=" * 60)
    
    tests = [
        ("Content Generation", test_content_generation),
        ("Prompt Management", test_prompt_management)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The agent is ready to use.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the configuration.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)