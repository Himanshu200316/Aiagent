#!/usr/bin/env python3
"""
AI-Powered Social Media Advertising Agent
Main application entry point that orchestrates all components.
"""

import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager

from cerebrus_api import CerebrusAPI
from prompt_manager import PromptManager
from image_generator import ImageGenerator
from caption_generator import CaptionGenerator
from social_media_manager import SocialMediaManager
from scheduler import PostingScheduler
from user_manager import UserManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global instances
prompt_manager = None
image_generator = None
caption_generator = None
social_media_manager = None
posting_scheduler = None
user_manager = None
cerebrus_api = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global prompt_manager, image_generator, caption_generator
    global social_media_manager, posting_scheduler, user_manager, cerebrus_api

    logger.info("Starting AI-Powered Social Media Advertising Agent...")

    # Initialize data directories
    data_dirs = ['/app/data/prompts', '/app/data/images', '/app/data/users', '/app/logs']
    for dir_path in data_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    # Initialize core components
    prompt_manager = PromptManager('/app/data/prompts')
    image_generator = ImageGenerator()
    caption_generator = CaptionGenerator()
    user_manager = UserManager('/app/data/users')

    # Initialize social media manager (requires user credentials)
    social_media_manager = SocialMediaManager(user_manager)

    # Initialize scheduler for daily posting
    posting_scheduler = PostingScheduler(social_media_manager, prompt_manager)
    posting_scheduler.start_daily_scheduler(hour=0, minute=0)  # 12:00 AM

    # Initialize Cerebrus API
    cerebrus_api = CerebrusAPI(
        prompt_manager=prompt_manager,
        image_generator=image_generator,
        caption_generator=caption_generator,
        social_media_manager=social_media_manager,
        user_manager=user_manager,
        posting_scheduler=posting_scheduler
    )

    logger.info("All components initialized successfully")

    yield

    logger.info("Shutting down application...")

# Create FastAPI application
app = FastAPI(
    title="AI Social Media Advertising Agent",
    description="Automated social media advertising with AI-generated content",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "AI-Powered Social Media Advertising Agent",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "prompt_manager": prompt_manager is not None,
            "image_generator": image_generator is not None,
            "caption_generator": caption_generator is not None,
            "social_media_manager": social_media_manager is not None,
            "posting_scheduler": posting_scheduler is not None,
            "cerebrus_api": cerebrus_api is not None
        }
    }

# Include Cerebrus API routes
app.include_router(cerebrus_api.router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )