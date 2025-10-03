#!/usr/bin/env python3
"""
Caption Generator - Handles AI caption generation for social media posts
"""

import os
import logging
import requests
import json
from typing import Dict, List, Optional, Tuple
import re

logger = logging.getLogger(__name__)

class CaptionGenerator:
    """Generates engaging captions for social media posts"""

    def __init__(self):
        # OpenAI API key for caption generation
        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # Caption templates for different platforms and tones
        self.caption_templates = {
            "instagram": {
                "professional": [
                    "Elevating {topic} with precision and expertise. {hashtags}",
                    "Discover the art of {topic} - where quality meets innovation. {hashtags}",
                    "Professional {topic} solutions that deliver results. {hashtags}",
                    "Experience excellence in {topic}. Your success is our priority. {hashtags}"
                ],
                "casual": [
                    "Just tried this amazing {topic}! You need to check it out! {hashtags}",
                    "Loving how {topic} makes everything better! Who's with me? {hashtags}",
                    "Simple pleasures: great {topic} and good company! {hashtags}",
                    "When {topic} meets perfection - magic happens! ✨ {hashtags}"
                ],
                "exciting": [
                    "🚀 Revolutionizing {topic} - are you ready for the future? {hashtags}",
                    "The {topic} revolution starts NOW! Don't miss out! 🔥 {hashtags}",
                    "Epic {topic} alert! This changes everything! 💥 {hashtags}",
                    "Game-changing {topic} that will blow your mind! 🤯 {hashtags}"
                ]
            },
            "twitter": {
                "professional": [
                    "Excelling in {topic} with proven expertise and results-driven solutions. {hashtags}",
                    "Professional {topic} services that deliver measurable outcomes. {hashtags}",
                    "Setting the standard in {topic} excellence. {hashtags}",
                    "Trusted {topic} partner delivering quality and reliability. {hashtags}"
                ],
                "casual": [
                    "Just discovered this awesome {topic}! Highly recommend! {hashtags}",
                    "Quick {topic} tip: Try this for amazing results! {hashtags}",
                    "Loving my {topic} game lately! What's your go-to? {hashtags}",
                    "Hot take: {topic} is underrated. Change my mind! {hashtags}"
                ],
                "exciting": [
                    "BREAKING: Revolutionary {topic} innovation! 🚀 {hashtags}",
                    "Game-changer alert! {topic} just got EPIC! 🔥 {hashtags}",
                    "The future of {topic} is HERE! Who's ready? 💥 {hashtags}",
                    "Mind-blowing {topic} update! This is HUGE! 🤯 {hashtags}"
                ]
            },
            "linkedin": {
                "professional": [
                    "Advancing {topic} through strategic innovation and industry expertise. {hashtags}",
                    "Professional {topic} solutions driving business growth and success. {hashtags}",
                    "Leading the way in {topic} excellence and thought leadership. {hashtags}",
                    "Strategic {topic} partnerships that deliver sustainable results. {hashtags}"
                ],
                "casual": [
                    "Exploring new horizons in {topic}. Always learning, always growing. {hashtags}",
                    "Quick {topic} insight for today: Focus on what matters most. {hashtags}",
                    "Reflecting on {topic} trends and where we're headed. {hashtags}",
                    "Building better {topic} practices, one step at a time. {hashtags}"
                ],
                "exciting": [
                    "🚀 Disrupting {topic} with groundbreaking innovation! {hashtags}",
                    "Revolutionary {topic} breakthrough announced! Who's ready to lead? {hashtags}",
                    "Game-changing {topic} development! The future is now! 🔥 {hashtags}",
                    "Transformative {topic} solution launching soon! Stay tuned! 💡 {hashtags}"
                ]
            }
        }

        # Hashtag suggestions by category
        self.hashtag_categories = {
            "business": ["#business", "#entrepreneurship", "#success", "#leadership", "#innovation"],
            "technology": ["#technology", "#innovation", "#tech", "#digital", "#future"],
            "lifestyle": ["#lifestyle", "#wellness", "#health", "#fitness", "#motivation"],
            "food": ["#food", "#foodie", "#delicious", "#tasty", "#cooking"],
            "fashion": ["#fashion", "#style", "#outfit", "#trendy", "#ootd"],
            "travel": ["#travel", "#adventure", "#wanderlust", "#explore", "#vacation"],
            "fitness": ["#fitness", "#workout", "#health", "#gym", "#motivation"],
            "art": ["#art", "#creative", "#design", "#artist", "#inspiration"],
            "music": ["#music", "#musician", "#songs", "#playlist", "#concert"],
            "education": ["#education", "#learning", "#knowledge", "#study", "#growth"]
        }

    def generate_caption(
        self,
        product_description: str,
        platform: str,
        tone: str = "professional",
        target_audience: str = "general",
        custom_keywords: List[str] = None,
        max_length: int = 150
    ) -> str:
        """
        Generate a caption for social media post

        Args:
            product_description: Description of product/service
            platform: Target platform (instagram, twitter, linkedin)
            tone: Caption tone (professional, casual, exciting)
            target_audience: Target audience category
            custom_keywords: Custom keywords for hashtags
            max_length: Maximum caption length

        Returns:
            Generated caption string
        """
        try:
            # Extract key topic from product description
            topic = self._extract_topic(product_description)

            # Get appropriate template
            templates = self.caption_templates.get(platform.lower(), {}).get(tone.lower(), [])
            if not templates:
                # Fallback to professional templates
                templates = self.caption_templates.get(platform.lower(), {}).get("professional", [])

            if not templates:
                # Ultimate fallback
                templates = [f"Discover {topic} - quality and excellence in every detail. #quality #excellence"]

            # Select random template
            template = templates[len(templates) % len(templates)]

            # Generate hashtags
            hashtags = self._generate_hashtags(topic, target_audience, custom_keywords)

            # Fill template
            caption = template.format(topic=topic, hashtags=hashtags)

            # Ensure caption doesn't exceed max length
            if len(caption) > max_length:
                caption = caption[:max_length-3] + "..."

            logger.info(f"Generated caption for {platform}: {caption[:50]}...")
            return caption

        except Exception as e:
            logger.error(f"Error generating caption: {e}")
            return f"Discover {product_description[:50]}... {self._generate_hashtags(product_description[:20])}"

    def _extract_topic(self, description: str) -> str:
        """Extract main topic from product description"""
        # Simple keyword extraction - can be enhanced with NLP
        words = re.findall(r'\b\w+\b', description.lower())

        # Common business/product words to prioritize
        priority_words = [
            'solution', 'service', 'product', 'platform', 'tool', 'software',
            'app', 'system', 'technology', 'innovation', 'business'
        ]

        for word in priority_words:
            if word in words:
                return word.title()

        # Return first meaningful word
        meaningful_words = [w for w in words if len(w) > 3][:3]
        return meaningful_words[0].title() if meaningful_words else "Excellence"

    def _generate_hashtags(self, topic: str, audience: str = "general", custom_keywords: List[str] = None) -> str:
        """Generate relevant hashtags"""
        hashtags = set()

        # Add topic-based hashtags
        topic_lower = topic.lower()
        for category, category_hashtags in self.hashtag_categories.items():
            if category in topic_lower or topic_lower in category:
                hashtags.update(category_hashtags[:3])  # Limit to 3 per category
                break

        # Add general business hashtags
        if not hashtags:
            hashtags.update(["#business", "#success", "#innovation"])

        # Add audience-specific hashtags
        if audience.lower() == "business":
            hashtags.update(["#b2b", "#business", "#professional"])
        elif audience.lower() == "consumer":
            hashtags.update(["#lifestyle", "#daily", "#trending"])

        # Add custom keywords as hashtags
        if custom_keywords:
            for keyword in custom_keywords[:3]:  # Limit custom hashtags
                hashtags.add(f"#{keyword.replace(' ', '').lower()}")

        # Format hashtags
        hashtag_list = list(hashtags)[:5]  # Limit total hashtags
        return " ".join(hashtag_list)

    def generate_caption_with_ai(self, product_description: str, platform: str, tone: str) -> Optional[str]:
        """Generate caption using AI (OpenAI GPT)"""
        try:
            if not self.openai_api_key:
                logger.warning("OpenAI API key not found, using template-based generation")
                return self.generate_caption(product_description, platform, tone)

            prompt = f"""
            Create an engaging {tone} caption for {platform} about: {product_description}

            Requirements:
            - Maximum 150 characters
            - Include 2-4 relevant hashtags
            - Make it engaging and action-oriented
            - Match the {tone} tone
            - For {platform} platform style

            Caption:"""

            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 200,
                    "temperature": 0.7
                }
            )

            if response.status_code == 200:
                data = response.json()
                caption = data["choices"][0]["message"]["content"].strip()
                logger.info(f"AI-generated caption: {caption}")
                return caption
            else:
                logger.error(f"OpenAI API error: {response.status_code}")
                return self.generate_caption(product_description, platform, tone)

        except Exception as e:
            logger.error(f"Error in AI caption generation: {e}")
            return self.generate_caption(product_description, platform, tone)

    def generate_story_caption(self, product_description: str, platform: str = "instagram") -> str:
        """Generate a shorter caption suitable for Instagram Stories"""
        try:
            topic = self._extract_topic(product_description)

            # Story-specific templates (shorter, more immediate)
            story_templates = [
                f"✨ {topic} magic! ✨",
                f"Quick {topic} tip! 💡",
                f"Morning {topic} motivation ☀️",
                f"Weekend {topic} vibes 🌟",
                f"Pro {topic} hack! 🔥"
            ]

            template = story_templates[len(story_templates) % len(story_templates)]
            hashtags = self._generate_hashtags(topic)[:3]  # Shorter hashtag list

            caption = f"{template}\n{hashtags}"

            # Ensure very short for stories
            if len(caption) > 100:
                caption = caption[:97] + "..."

            return caption

        except Exception as e:
            logger.error(f"Error generating story caption: {e}")
            return f"✨ Amazing {product_description[:20]}! ✨"