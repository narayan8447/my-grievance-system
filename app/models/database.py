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
            # Programmatic index creation
            await cls._create_indexes()
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    @classmethod
    async def _create_indexes(cls):
        """
        Create database indexes programmatically and idempotently.
        Safe to run on every application startup.
        """
        try:
            db_inst = cls.get_database()
            
            # 1. Users Collection Indexes
            users = db_inst["users"]
            # unique user_id for direct O(1) user profile retrieval
            await users.create_index("user_id", unique=True)
            # unique email to prevent registration duplicates and for login queries
            await users.create_index("email", unique=True)
            # unique phone to prevent duplicate phone registration; sparse since phone is optional
            await users.create_index("phone", unique=True, sparse=True)
            # compound index for retrieving specific addressers of a department
            await users.create_index([("role", 1), ("department", 1)])
            
            # 2. Grievances Collection Indexes
            grievances = db_inst["grievances"]
            # unique grievance_id for fast O(1) ticket retrieval and updates
            await grievances.create_index("grievance_id", unique=True)
            # index on user_id to query all grievances submitted by a citizen
            await grievances.create_index("user_id")
            # index on assigned department to query departmental queues for addressers
            await grievances.create_index("assignment.assigned_to_department")
            # index on status to filter grievances on admin and addresser dashboards
            await grievances.create_index("status")
            # index on category for filtering and routing matching
            await grievances.create_index("category")
            # index on priority for dashboard breakdowns and workload sorting
            await grievances.create_index("priority")
            # compound/sorting index on created_at to sort tickets chronologically
            await grievances.create_index([("created_at", -1)])
            # text index on grievance_text for text searches and similarity matches
            await grievances.create_index([("grievance_text", "text")])
            # compound index for RAG queries fetching resolved grievances in same category/department
            await grievances.create_index([
                ("status", 1),
                ("category", 1),
                ("department", 1),
                ("resolved_at", -1)
            ])
            
            # 3. Routing Collection Indexes
            routing = db_inst["routing"]
            # unique index on grievance_id for O(1) assignment lookup
            await routing.create_index("grievance_id", unique=True)
            
            logger.info("Programmatic database indexes checked/created successfully.")
        except Exception as e:
            logger.error(f"Failed to verify/create database indexes programmatically: {e}")
    
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