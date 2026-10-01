"""Create indexes and seed computed forecast/anomaly rows.

Requires MONGODB_URI in backend/.env.

Usage:

    python scripts/seed_database.py
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.core.config import settings  # noqa: E402
from app.database.mongodb import close_mongo_connection, connect_to_mongo, get_database  # noqa: E402
from app.services.app_data import app_data  # noqa: E402
from app.services.persistence import seed_analytics_store  # noqa: E402

logger = logging.getLogger(__name__)


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
    connect_to_mongo()
    if get_database() is None:
        logger.error("Set MONGODB_URI in backend/.env before seeding.")
        return 1

    app_data.load()
    if not app_data.ready:
        logger.error("Could not load model artifacts: %s", app_data.error)
        close_mongo_connection()
        return 1

    seed_analytics_store(app_data)
    logger.info("Seeded database %s.", settings.db_name)
    close_mongo_connection()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
