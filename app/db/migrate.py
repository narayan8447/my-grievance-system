"""
Database Migration and Index Initialization Script
Safe to run multiple times. Supported execution: python -m app.db.migrate
"""
import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("migration")


async def create_indexes(db) -> None:
    """Create all required indexes idempotently with detailed logging"""
    logger.info("Initializing index creation...")

    # 1. Users collection indexes
    users = db["users"]
    logger.info("Checking users collection indexes...")
    
    res = await users.create_index("user_id", unique=True)
    logger.info(f"Verified unique index on users(user_id): {res}")
    
    res = await users.create_index("email", unique=True)
    logger.info(f"Verified unique index on users(email): {res}")
    
    res = await users.create_index("phone", unique=True, sparse=True)
    logger.info(f"Verified unique sparse index on users(phone): {res}")
    
    res = await users.create_index([("role", 1), ("department", 1)])
    logger.info(f"Verified compound index on users(role, department): {res}")

    # 2. Grievances collection indexes
    grievances = db["grievances"]
    logger.info("Checking grievances collection indexes...")
    
    res = await grievances.create_index("grievance_id", unique=True)
    logger.info(f"Verified unique index on grievances(grievance_id): {res}")
    
    res = await grievances.create_index("user_id")
    logger.info(f"Verified index on grievances(user_id): {res}")
    
    res = await grievances.create_index("assignment.assigned_to_department")
    logger.info(f"Verified index on grievances(assignment.assigned_to_department): {res}")
    
    res = await grievances.create_index("status")
    logger.info(f"Verified index on grievances(status): {res}")
    
    res = await grievances.create_index([("created_at", -1)])
    logger.info(f"Verified descending sort index on grievances(created_at): {res}")
    
    res = await grievances.create_index([("grievance_text", "text")])
    logger.info(f"Verified text index on grievances(grievance_text): {res}")

    # 3. Routing collection indexes
    routing = db["routing"]
    logger.info("Checking routing collection indexes...")
    
    res = await routing.create_index("grievance_id", unique=True)
    logger.info(f"Verified unique index on routing(grievance_id): {res}")

    logger.info("Index verification and creation completed.")


# Future schema migrations can be registered here as async functions taking the db instance.
# Example:
# async def migration_v2_add_routing_details(db):
#     ...
MIGRATION_STEPS = [
    # (version_number, migration_function)
    (1, create_indexes),
]


async def run_migrations() -> None:
    """Run migrations sequentially and record schema version"""
    logger.info("Connecting to MongoDB for migration check...")
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.DATABASE_NAME]
    
    # Check current schema version
    meta_coll = db["_schema_metadata"]
    version_doc = await meta_coll.find_one({"type": "schema_version"})
    
    current_version = version_doc.get("version", 0) if version_doc else 0
    logger.info(f"Current database schema version: {current_version}")
    
    for version, func in MIGRATION_STEPS:
        if version > current_version:
            logger.info(f"Running migration step {version}: {func.__name__}...")
            try:
                await func(db)
                await meta_coll.update_one(
                    {"type": "schema_version"},
                    {"$set": {"version": version, "updated_at": asyncio.get_event_loop().time()}},
                    upsert=True
                )
                logger.info(f"Migration step {version} applied successfully.")
            except Exception as e:
                logger.error(f"Migration step {version} failed: {e}")
                raise e
        else:
            # Re-run index checks anyway to ensure environment setup is fresh & correct
            if func == create_indexes:
                logger.info("Re-verifying index setup to ensure consistency...")
                await func(db)
            else:
                logger.info(f"Migration step {version} already applied. Skipping.")

    logger.info("All database migration checks completed successfully.")


def main():
    asyncio.run(run_migrations())


if __name__ == "__main__":
    main()
