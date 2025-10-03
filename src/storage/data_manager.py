"""
Data Management System
Handles storage and retrieval of prompts, content, and posting history
"""

import asyncio
import logging
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import sqlite3
import aiosqlite
from dataclasses import asdict

logger = logging.getLogger(__name__)

class DataManager:
    """File-based and database storage manager"""
    
    def __init__(self):
        self.db_path = "data/social_media_agent.db"
        self.json_storage_path = "data/prompts"
        self.initialized = False
        
    async def initialize(self):
        """Initialize storage system"""
        try:
            # Ensure directories exist
            os.makedirs("data", exist_ok=True)
            os.makedirs(self.json_storage_path, exist_ok=True)
            os.makedirs("data/images", exist_ok=True)
            os.makedirs("data/history", exist_ok=True)
            
            # Initialize SQLite database
            await self._init_database()
            
            self.initialized = True
            logger.info("Data manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize data manager: {e}")
            raise
    
    async def _init_database(self):
        """Initialize SQLite database with required tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Create tables
            await db.execute('''
                CREATE TABLE IF NOT EXISTS content (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt_hash TEXT UNIQUE NOT NULL,
                    original_prompt TEXT NOT NULL,
                    generated_caption TEXT NOT NULL,
                    image_path TEXT,
                    image_generation_prompt TEXT,
                    content_type TEXT DEFAULT 'feed_post',
                    platforms TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    campaign_id TEXT
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_id INTEGER,
                    platform TEXT NOT NULL,
                    platform_post_id TEXT,
                    post_url TEXT,
                    posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'success',
                    error_message TEXT,
                    FOREIGN KEY (content_id) REFERENCES content (id)
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS campaigns (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    target_audience TEXT,
                    tone TEXT,
                    product_service_description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS posting_schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id TEXT,
                    platform TEXT NOT NULL,
                    post_time TEXT NOT NULL DEFAULT '00:00',
                    timezone TEXT DEFAULT 'UTC',
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
                )
            ''')
            
            # Create indexes
            await db.execute('CREATE INDEX IF NOT EXISTS idx_content_prompt_hash ON content(prompt_hash)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_posts_platform_posted_at ON posts(platform, posted_at)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_campaigns_active ON campaigns(is_active)')
            
            await db.commit()
    
    async def store_content(self, content, prompt_data: Dict[str, Any]) -> int:
        """Store generated content in database"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    INSERT INTO content (
                        prompt_hash, original_prompt, generated_caption, 
                        image_path, image_generation_prompt, content_type, 
                        platforms, campaign_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    content.prompt_hash,
                    json.dumps(prompt_data),
                    content.caption,
                    content.image_path,
                    content.image_generation_prompt,
                    content.content_type,
                    json.dumps(content.platforms),
                    getattr(content, 'campaign_id', None)
                ))
                
                content_id = cursor.lastrowid
                await db.commit()
                
                # Also store as JSON file for backup
                await self._store_content_json(content, prompt_data)
                
                logger.info(f"Content stored with ID: {content_id}")
                return content_id
                
        except Exception as e:
            logger.error(f"Failed to store content: {e}")
            raise
    
    async def _store_content_json(self, content, prompt_data: Dict[str, Any]):
        """Store content as JSON file for backup"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"content_{content.prompt_hash[:8]}_{timestamp}.json"
            file_path = os.path.join(self.json_storage_path, filename)
            
            content_data = {
                'prompt_hash': content.prompt_hash,
                'prompt_data': prompt_data,
                'caption': content.caption,
                'image_path': content.image_path,
                'image_generation_prompt': content.image_generation_prompt,
                'content_type': content.content_type,
                'platforms': content.platforms,
                'created_at': content.created_at.isoformat()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(content_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"Failed to store JSON backup: {e}")
    
    async def prompt_exists(self, prompt_hash: str) -> bool:
        """Check if a prompt hash already exists"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    'SELECT 1 FROM content WHERE prompt_hash = ? LIMIT 1',
                    (prompt_hash,)
                )
                result = await cursor.fetchone()
                return result is not None
                
        except Exception as e:
            logger.error(f"Failed to check prompt existence: {e}")
            return False
    
    async def get_content_by_hash(self, prompt_hash: str) -> Optional[Dict[str, Any]]:
        """Get content by prompt hash"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    SELECT * FROM content WHERE prompt_hash = ?
                ''', (prompt_hash,))
                
                row = await cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                return None
                
        except Exception as e:
            logger.error(f"Failed to get content by hash: {e}")
            return None
    
    async def store_post_result(self, content_id: int, platform: str, post_result) -> int:
        """Store posting result"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute('''
                    INSERT INTO posts (
                        content_id, platform, platform_post_id, post_url, 
                        status, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    content_id,
                    platform,
                    post_result.platform_post_id,
                    post_result.post_url,
                    'success' if post_result.success else 'failed',
                    post_result.error_message
                ))
                
                post_id = cursor.lastrowid
                await db.commit()
                
                logger.info(f"Post result stored with ID: {post_id}")
                return post_id
                
        except Exception as e:
            logger.error(f"Failed to store post result: {e}")
            raise
    
    async def get_posting_history(self, platform: Optional[str] = None, 
                                 days: int = 30) -> List[Dict[str, Any]]:
        """Get posting history"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                query = '''
                    SELECT p.*, c.generated_caption, c.image_path, c.content_type
                    FROM posts p
                    JOIN content c ON p.content_id = c.id
                    WHERE p.posted_at >= datetime('now', '-{} days')
                '''.format(days)
                
                params = []
                if platform:
                    query += ' AND p.platform = ?'
                    params.append(platform)
                
                query += ' ORDER BY p.posted_at DESC'
                
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get posting history: {e}")
            return []
    
    async def create_campaign(self, campaign_data: Dict[str, Any]) -> str:
        """Create a new campaign"""
        try:
            import uuid
            campaign_id = str(uuid.uuid4())
            
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    INSERT INTO campaigns (
                        id, name, description, target_audience, tone, 
                        product_service_description, user_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    campaign_id,
                    campaign_data.get('name'),
                    campaign_data.get('description'),
                    campaign_data.get('target_audience'),
                    campaign_data.get('tone'),
                    campaign_data.get('product_service_description'),
                    campaign_data.get('user_id')
                ))
                
                await db.commit()
                
                logger.info(f"Campaign created with ID: {campaign_id}")
                return campaign_id
                
        except Exception as e:
            logger.error(f"Failed to create campaign: {e}")
            raise
    
    async def get_campaigns(self, user_id: Optional[str] = None, 
                           active_only: bool = True) -> List[Dict[str, Any]]:
        """Get campaigns"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                query = 'SELECT * FROM campaigns WHERE 1=1'
                params = []
                
                if user_id:
                    query += ' AND user_id = ?'
                    params.append(user_id)
                
                if active_only:
                    query += ' AND is_active = 1'
                
                query += ' ORDER BY created_at DESC'
                
                cursor = await db.execute(query, params)
                rows = await cursor.fetchall()
                
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to get campaigns: {e}")
            return []
    
    async def cleanup_old_data(self, days: int = 30):
        """Clean up old data"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            async with aiosqlite.connect(self.db_path) as db:
                # Delete old posts
                await db.execute('''
                    DELETE FROM posts WHERE posted_at < ?
                ''', (cutoff_date,))
                
                # Delete old content without associated posts
                await db.execute('''
                    DELETE FROM content 
                    WHERE created_at < ? 
                    AND id NOT IN (SELECT DISTINCT content_id FROM posts WHERE content_id IS NOT NULL)
                ''', (cutoff_date,))
                
                await db.commit()
                
            # Clean up old JSON files
            for filename in os.listdir(self.json_storage_path):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.json_storage_path, filename)
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    if file_time < cutoff_date:
                        os.remove(file_path)
            
            logger.info(f"Cleaned up data older than {days} days")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                stats = {}
                
                # Content stats
                cursor = await db.execute('SELECT COUNT(*) FROM content')
                stats['total_content'] = (await cursor.fetchone())[0]
                
                # Posts stats
                cursor = await db.execute('SELECT COUNT(*) FROM posts')
                stats['total_posts'] = (await cursor.fetchone())[0]
                
                # Success rate
                cursor = await db.execute("SELECT COUNT(*) FROM posts WHERE status = 'success'")
                successful_posts = (await cursor.fetchone())[0]
                stats['success_rate'] = (successful_posts / stats['total_posts'] * 100) if stats['total_posts'] > 0 else 0
                
                # Platform breakdown
                cursor = await db.execute('SELECT platform, COUNT(*) FROM posts GROUP BY platform')
                platform_stats = await cursor.fetchall()
                stats['posts_by_platform'] = dict(platform_stats)
                
                # Campaigns stats
                cursor = await db.execute('SELECT COUNT(*) FROM campaigns WHERE is_active = 1')
                stats['active_campaigns'] = (await cursor.fetchone())[0]
                
                return stats
                
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check health of storage system"""
        try:
            health_status = {
                "initialized": self.initialized,
                "database_accessible": False,
                "json_storage_accessible": False
            }
            
            # Test database connection
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute('SELECT 1')
                health_status["database_accessible"] = True
            except Exception as e:
                health_status["database_error"] = str(e)
            
            # Test JSON storage
            try:
                test_file = os.path.join(self.json_storage_path, "health_check.json")
                with open(test_file, 'w') as f:
                    json.dump({"test": True}, f)
                os.remove(test_file)
                health_status["json_storage_accessible"] = True
            except Exception as e:
                health_status["json_storage_error"] = str(e)
            
            # Get basic stats
            if health_status["database_accessible"]:
                health_status["stats"] = await self.get_stats()
            
            return health_status
            
        except Exception as e:
            return {"error": str(e), "status": "unhealthy"}