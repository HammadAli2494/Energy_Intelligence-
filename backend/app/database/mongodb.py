import logging

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from app.core.config import settings

logger = logging.getLogger(__name__)

client: MongoClient | None = None
db = None
mongodb_status = "not_configured"


def connect_to_mongo() -> None:
    """Connect if MONGODB_URI is set. The API still starts without MongoDB."""
    global client, db, mongodb_status

    if not settings.mongodb_uri:
        mongodb_status = "not_configured"
        logger.info("MongoDB URI is not set. Skipping database connection.")
        return

    try:
        mongo_client = MongoClient(
            settings.mongodb_uri,
            serverSelectionTimeoutMS=5000,
        )
        mongo_client.admin.command("ping")
        client = mongo_client
        db = mongo_client[settings.db_name]
        mongodb_status = "connected"
        logger.info("Connected to MongoDB database %s.", settings.db_name)
    except PyMongoError:
        client = None
        db = None
        mongodb_status = "unavailable"
        logger.error("Could not connect to MongoDB.")


def refresh_mongodb_status() -> str:
    """Ping Atlas if a URI is set. Never treat a URI alone as connected."""
    global mongodb_status

    if not settings.mongodb_uri:
        mongodb_status = "not_configured"
        return mongodb_status

    if client is None:
        connect_to_mongo()
        return mongodb_status

    try:
        client.admin.command("ping")
        mongodb_status = "connected"
    except PyMongoError:
        mongodb_status = "unavailable"
        logger.error("MongoDB ping failed.")
    return mongodb_status


def close_mongo_connection() -> None:
    global client, db, mongodb_status

    if client is not None:
        client.close()
        logger.info("Closed MongoDB connection.")

    client = None
    db = None
    if mongodb_status == "connected":
        mongodb_status = "not_configured"


def get_database():
    """Return the database object, or None when MongoDB is not available."""
    return db
