"""
Database configuration and initialization
"""
import sqlite3
import json
import os
from pathlib import Path
from app.core.config import settings

class DatabaseManager:
    """Manages SQLite database operations"""
    
    def __init__(self):
        self.db_path = settings.data_dir + "/social_media_agent.db"
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Social media credentials table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS social_media_credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    platform TEXT NOT NULL,
                    credentials TEXT NOT NULL,  -- JSON encrypted credentials
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Ad prompts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS ad_prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    prompt_text TEXT NOT NULL,
                    prompt_hash TEXT UNIQUE NOT NULL,
                    platform TEXT NOT NULL,
                    content_type TEXT NOT NULL,  -- 'feed' or 'story'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            # Generated content table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS generated_content (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    prompt_id INTEGER NOT NULL,
                    caption TEXT NOT NULL,
                    image_path TEXT,
                    image_generated BOOLEAN DEFAULT FALSE,
                    platforms TEXT NOT NULL,  -- JSON array of platforms
                    scheduled_time TIMESTAMP,
                    posted_at TIMESTAMP,
                    status TEXT DEFAULT 'pending',  -- 'pending', 'posted', 'failed'
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (prompt_id) REFERENCES ad_prompts (id)
                )
            """)
            
            # Posting history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS posting_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    content_id INTEGER NOT NULL,
                    platform TEXT NOT NULL,
                    post_id TEXT,  -- Platform-specific post ID
                    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'success',
                    error_message TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (content_id) REFERENCES generated_content (id)
                )
            """)
            
            # User preferences table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    preferences TEXT NOT NULL,  -- JSON preferences
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)
            
            conn.commit()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)

# Global database manager instance
db_manager = DatabaseManager()

async def init_db():
    """Initialize database on startup"""
    db_manager.init_database()
    return True