"""
Main application entry point for the AI Social Media Advertising Agent.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os
from dotenv import load_dotenv

from src.api.routes import router as api_router
from src.scheduler.posting_scheduler import PostingScheduler
from src.storage.database import init_database
from src.ai.content_generator import ContentGenerator

# Load environment variables
load_dotenv()

# Global scheduler instance
scheduler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global scheduler
    
    # Startup
    print("🚀 Starting AI Social Media Advertising Agent...")
    
    # Initialize database
    await init_database()
    
    # Initialize content generator
    content_generator = ContentGenerator()
    await content_generator.initialize()
    
    # Start posting scheduler
    scheduler = PostingScheduler()
    await scheduler.start()
    
    print("✅ Agent started successfully!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down agent...")
    if scheduler:
        await scheduler.stop()
    print("✅ Agent shutdown complete")

# Create FastAPI application
app = FastAPI(
    title="AI Social Media Advertising Agent",
    description="Automated social media advertising with AI-generated content",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Social Media Advertising Agent",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "scheduler_running": scheduler is not None and scheduler.is_running if scheduler else False
    }

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENVIRONMENT") == "development"
    )