from __future__ import annotations

from fastapi import HTTPException, status

from app.services.app_data import app_data


def loaded_data():
    if not app_data.ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model or dataset is not available. Train and build features first.",
        )
    return app_data
