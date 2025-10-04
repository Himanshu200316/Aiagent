"""
AI Caption Generation Module
Generates engaging captions for social media advertisements
"""

import asyncio
import logging
import os
from typing import Dict, Any, List, Optional
import openai
import anthropic

logger = logging.getLogger(__name__)

class CaptionGenerator:
    """AI caption generation using OpenAI and Anthropic"""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.initialized = False
        
        # Platform-specific constraints
        self.platform_limits = {
            'instagram': {'max_length': 2200, 'hashtag_limit': 30},
            'twitter': {'max_length': 280, 'hashtag_limit': 2},
            'linkedin': {'max_length': 3000, 'hashtag_limit': 5}
        }
        
    async def initialize(self):
        """Initialize caption generation services"""
        try:
            # Initialize OpenAI client
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if openai_api_key:
                self.openai_client = openai.AsyncOpenAI(api_key=openai_api_key)
                logger.info("OpenAI client initialized for captions")
            
            # Initialize Anthropic client
            anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
            if anthropic_api_key:
                self.anthropic_client = anthropic.AsyncAnthropic(api_key=anthropic_api_key)
                logger.info("Anthropic client initialized for captions")
            
            if not self.openai_client and not self.anthropic_client:
                raise ValueError("No AI service available for caption generation")
            
            self.initialized = True
            logger.info("Caption generator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize caption generator: {e}")
            raise
    
    async def generate_caption(self, product_service: str, target_audience: str, 
                             tone: str, platforms: List[str], content_type: str = "feed_post",
                             additional_context: Optional[str] = None) -> str:
        """Generate caption for social media advertisement"""
        
        if not self.initialized:
            await self.initialize()
        
        try:
            # Create platform-specific prompt
            prompt = self._create_caption_prompt(
                product_service, target_audience, tone, platforms, content_type, additional_context
            )
            
            # Generate caption using available AI service
            if self.openai_client:
                caption = await self._generate_with_openai(prompt, platforms)
            elif self.anthropic_client:
                caption = await self._generate_with_anthropic(prompt, platforms)
            else:
                raise ValueError("No AI service available")
            
            # Post-process caption for platforms
            caption = self._optimize_for_platforms(caption, platforms)
            
            logger.info("Caption generated successfully")
            return caption
            
        except Exception as e:
            logger.error(f"Caption generation failed: {e}")
            raise
    
    def _create_caption_prompt(self, product_service: str, target_audience: str, 
                              tone: str, platforms: List[str], content_type: str,
                              additional_context: Optional[str] = None) -> str:
        """Create optimized prompt for caption generation"""
        
        platform_str = ", ".join(platforms)
        
        # Get the most restrictive character limit
        min_limit = min([self.platform_limits[p]['max_length'] for p in platforms 
                        if p in self.platform_limits], default=280)
        
        prompt = f"""Create an engaging {tone} social media advertisement caption for {content_type}.

Product/Service: {product_service}
Target Audience: {target_audience}
Platforms: {platform_str}
Tone: {tone}
Character Limit: {min_limit} characters maximum

Requirements:
1. Hook the audience in the first line
2. Clearly communicate the value proposition
3. Include a strong call-to-action
4. Use appropriate hashtags for the platforms
5. Match the {tone} tone throughout
6. Be authentic and engaging
7. Optimize for {platform_str} best practices

"""
        
        if content_type == "story":
            prompt += "8. Make it suitable for vertical story format with urgency\n"
        
        if additional_context:
            prompt += f"Additional Context: {additional_context}\n"
        
        # Platform-specific guidelines
        if 'instagram' in platforms:
            prompt += "Instagram: Use relevant hashtags, encourage engagement, visual storytelling\n"
        if 'twitter' in platforms:
            prompt += "Twitter: Be concise, use trending topics if relevant, encourage retweets\n"
        if 'linkedin' in platforms:
            prompt += "LinkedIn: Professional tone, industry insights, business value focus\n"
        
        prompt += "\nGenerate only the caption text, no additional commentary."
        
        return prompt
    
    async def _generate_with_openai(self, prompt: str, platforms: List[str]) -> str:
        """Generate caption using OpenAI GPT"""
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an expert social media marketing copywriter specializing in creating engaging advertisement captions that drive conversions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI caption generation failed: {e}")
            raise
    
    async def _generate_with_anthropic(self, prompt: str, platforms: List[str]) -> str:
        """Generate caption using Anthropic Claude"""
        
        try:
            response = await self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=500,
                temperature=0.7,
                system="You are an expert social media marketing copywriter specializing in creating engaging advertisement captions that drive conversions.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Anthropic caption generation failed: {e}")
            raise
    
    def _optimize_for_platforms(self, caption: str, platforms: List[str]) -> str:
        """Optimize caption for specific platforms"""
        
        # Get the most restrictive character limit
        min_limit = min([self.platform_limits[p]['max_length'] for p in platforms 
                        if p in self.platform_limits], default=280)
        
        # Truncate if necessary
        if len(caption) > min_limit:
            # Try to truncate at sentence boundary
            sentences = caption.split('. ')
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence + '. ') <= min_limit - 10:  # Leave room for ellipsis
                    truncated += sentence + '. '
                else:
                    break
            
            if truncated:
                caption = truncated.rstrip('. ') + '...'
            else:
                caption = caption[:min_limit-3] + '...'
        
        return caption
    
    async def generate_variation(self, original_caption: str, variation_number: int) -> str:
        """Generate a variation of an existing caption"""
        
        if not self.initialized:
            await self.initialize()
        
        try:
            prompt = f"""Create a variation of this social media advertisement caption:

Original Caption: {original_caption}

Requirements:
1. Keep the same core message and value proposition
2. Change the wording, structure, and approach
3. Maintain the same tone and style
4. Keep similar length
5. Make it feel fresh and different while staying on-brand
6. This is variation #{variation_number}

Generate only the new caption text, no additional commentary."""
            
            if self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": "You are an expert copywriter creating variations of successful social media captions."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300,
                    temperature=0.8  # Higher temperature for more variation
                )
                return response.choices[0].message.content.strip()
            
            elif self.anthropic_client:
                response = await self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=300,
                    temperature=0.8,
                    system="You are an expert copywriter creating variations of successful social media captions.",
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Caption variation generation failed: {e}")
            raise
    
    async def generate_hashtags(self, product_service: str, target_audience: str, 
                              platforms: List[str]) -> Dict[str, List[str]]:
        """Generate platform-specific hashtags"""
        
        if not self.initialized:
            await self.initialize()
        
        hashtags = {}
        
        for platform in platforms:
            if platform not in self.platform_limits:
                continue
                
            limit = self.platform_limits[platform]['hashtag_limit']
            
            prompt = f"""Generate {limit} relevant hashtags for {platform} for this advertisement:

Product/Service: {product_service}
Target Audience: {target_audience}
Platform: {platform}

Requirements:
1. Mix of popular and niche hashtags
2. Relevant to the product/service
3. Appropriate for the target audience
4. Follow {platform} best practices
5. Include branded and generic hashtags

Return only the hashtags, one per line, with # symbol."""
            
            try:
                if self.openai_client:
                    response = await self.openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": f"You are a social media hashtag expert for {platform}."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=200,
                        temperature=0.5
                    )
                    
                    hashtag_text = response.choices[0].message.content.strip()
                    platform_hashtags = [tag.strip() for tag in hashtag_text.split('\n') if tag.strip().startswith('#')]
                    hashtags[platform] = platform_hashtags[:limit]
                
            except Exception as e:
                logger.error(f"Hashtag generation failed for {platform}: {e}")
                hashtags[platform] = []
        
        return hashtags
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of caption generation services"""
        
        health_status = {
            "initialized": self.initialized,
            "openai_available": self.openai_client is not None,
            "anthropic_available": self.anthropic_client is not None
        }
        
        # Test connections if available
        if self.openai_client:
            try:
                # Simple test - this might incur a small cost
                health_status["openai_status"] = "available"
            except Exception as e:
                health_status["openai_status"] = f"error: {str(e)}"
        
        if self.anthropic_client:
            try:
                health_status["anthropic_status"] = "available"
            except Exception as e:
                health_status["anthropic_status"] = f"error: {str(e)}"
        
        return health_status