"""
AI-Powered Social Media Ad Agent
Main application entry point
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from api.cerebrus_handler import CerebrusHandler
from scheduler.post_scheduler import PostScheduler
from storage.data_manager import DataManager
from ai_generation.content_generator import ContentGenerator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
data_manager = DataManager()
content_generator = ContentGenerator()
post_scheduler = PostScheduler()
cerebrus_handler = CerebrusHandler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting AI Social Media Ad Agent...")
    
    # Initialize components
    await data_manager.initialize()
    await content_generator.initialize()
    await post_scheduler.start()
    
    logger.info("Application started successfully")
    yield
    
    # Cleanup
    logger.info("Shutting down...")
    await post_scheduler.stop()
    logger.info("Application shutdown complete")

app = FastAPI(
    title="AI Social Media Ad Agent",
    description="Automated social media advertisement generation and posting",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI Social Media Ad Agent is running"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "components": {
            "data_manager": await data_manager.health_check(),
            "content_generator": await content_generator.health_check(),
            "scheduler": await post_scheduler.health_check()
        }
    }

# Include API routers
from api.chat_routes import router as chat_router
from api.content_routes import router as content_router
from api.auth_routes import router as auth_router
from api.posting_routes import router as posting_router

app.include_router(chat_router, prefix="/api/chat", tags=["chat"])
app.include_router(content_router, prefix="/api/content", tags=["content"])
app.include_router(auth_router, prefix="/api/auth", tags=["authentication"])
app.include_router(posting_router, prefix="/api/posting", tags=["posting"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )