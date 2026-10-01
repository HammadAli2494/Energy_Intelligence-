from fastapi import APIRouter

from app.core.config import settings
from app.database.mongodb import refresh_mongodb_status
from app.services.app_data import app_data

router = APIRouter(tags=["health"])


@router.get("/health")
def get_health() -> dict:
    """Report API, model, and a live MongoDB ping — not a URI-exists check."""
    mongodb = refresh_mongodb_status()
    status = "ok"
    if mongodb == "unavailable" or not app_data.ready:
        status = "degraded"

    return {
        "status": status,
        "service": "energy-intelligence-api",
        "environment": settings.environment,
        "mongodb": mongodb,
        "model_loaded": app_data.ready,
    }
