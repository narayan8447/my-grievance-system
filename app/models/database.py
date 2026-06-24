"""MongoDB database connection and operations"""
from __future__ import annotations
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager"""
    
    client: Optional[AsyncIOMotorClient] = None
    
    @classmethod
    async def connect_db(cls):
        """Connect to MongoDB"""
        try:
            cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
            # Test connection
            await cls.client.admin.command('ping')
            logger.info(f"Connected to MongoDB at {settings.MONGODB_URL}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def close_db(cls):
        """Close MongoDB connection"""
        if cls.client:
            cls.client.close()
            logger.info("Closed MongoDB connection")
    
    @classmethod
    def get_database(cls):
        """Get database instance"""
        if cls.client is None:
            raise Exception("Database not connected")
        return cls.client[settings.DATABASE_NAME]
    
    @classmethod
    def get_collection(cls, collection_name: str):
        """Get collection from database"""
        db = cls.get_database()
        return db[collection_name]


# Database instance
db = Database()