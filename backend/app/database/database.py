"""
MongoDB configuration and connection management for Jan Nidhi Spotter Backend.

Uses Motor (asyncio driver for MongoDB) for fully non-blocking asynchronous operations.
The MONGODB_URI is loaded from environment variables.
"""

import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ReturnDocument

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

MONGODB_URI = os.getenv("MONGODB_URI") or os.getenv("DATABASE_URL")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "jan_nidhi_db")

# Global Motor client and db instance
_client: AsyncIOMotorClient = None
_db = None


def get_client() -> AsyncIOMotorClient:
    """Get or create singleton MongoDB AsyncIOMotorClient."""
    global _client
    if _client is None:
        uri = os.getenv("MONGODB_URI") or os.getenv("DATABASE_URL")
        if not uri:
            uri = "mongodb://localhost:27017"
        _client = AsyncIOMotorClient(uri)
    return _client


def get_database():
    """Get the active MongoDB database instance."""
    global _db
    if _db is None:
        client = get_client()
        _db = client[MONGODB_DB_NAME]
    return _db


def get_users_collection():
    """Return the users collection."""
    return get_database()["users"]


def get_verifications_collection():
    """Return the citizen_verifications collection."""
    return get_database()["citizen_verifications"]


async def get_next_sequence(sequence_name: str) -> int:
    """Generate an auto-incrementing integer sequence for relational compatibility."""
    db = get_database()
    counters = db["counters"]
    doc = await counters.find_one_and_update(
        {"_id": sequence_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    return int(doc["seq"])


async def init_db():
    """Initialize collections, indexes, and initial configuration."""
    db = get_database()
    users = db["users"]
    verifications = db["citizen_verifications"]

    # Ensure unique index on email
    await users.create_index("email", unique=True)

    # Ensure indexes on verifications
    await verifications.create_index("id", unique=True)
    await verifications.create_index("user_id")
    await verifications.create_index("review_status")
    await verifications.create_index("created_at")
    await verifications.create_index("work_id")
