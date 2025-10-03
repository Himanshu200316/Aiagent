"""
Main FastAPI application for the Social Media Advertising Agent
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uvicorn
import asyncio
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.api.routes import auth, social_media, content_generation, scheduling, cerebrus
from app.services.scheduler import start_scheduler
from app.core.logging import setup_logging

# Setup logging
setup_logging()

security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    await init_db()
    await start_scheduler()
    yield
    # Shutdown
    # Cleanup tasks if needed

app = FastAPI(
    title="Social Media Advertising Agent",
    description="AI-powered agent for automated social media advertising",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(social_media.router, prefix="/api/social-media", tags=["Social Media"])
app.include_router(content_generation.router, prefix="/api/content", tags=["Content Generation"])
app.include_router(scheduling.router, prefix="/api/scheduling", tags=["Scheduling"])
app.include_router(cerebrus.router, prefix="/api/cerebrus", tags=["Cerebrus Integration"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Social Media Advertising Agent API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": "2024-01-01T00:00:00Z"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )