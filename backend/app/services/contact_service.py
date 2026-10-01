from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timezone

from app.database.mongodb import get_database

logger = logging.getLogger(__name__)

_recent_posts: dict[str, deque[float]] = defaultdict(deque)


def allow_contact(ip: str, limit: int = 5, window_seconds: int = 60) -> bool:
    now = time.time()
    queue = _recent_posts[ip]
    while queue and now - queue[0] > window_seconds:
        queue.popleft()
    if len(queue) >= limit:
        return False
    queue.append(now)
    return True


def sanitize_contact(payload: dict) -> dict:
    return {
        "name": payload["name"].strip()[:100],
        "email": payload["email"].strip()[:254],
        "subject": payload["subject"].strip()[:150],
        "message": payload["message"].strip()[:2000],
        "created_at": datetime.now(timezone.utc),
    }


def store_contact(document: dict) -> None:
    database = get_database()
    if database is None:
        raise RuntimeError("MongoDB is not configured.")
    database["contact_messages"].insert_one(document)
    logger.info("Stored a contact message.")
