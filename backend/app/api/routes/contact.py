from fastapi import APIRouter, HTTPException, Request, status

from app.database.mongodb import mongodb_status
from app.schemas.contact import ContactMessage
from app.services.contact_service import allow_contact, sanitize_contact, store_contact

router = APIRouter(tags=["contact"])


@router.post("/contact", status_code=status.HTTP_201_CREATED)
def submit_contact(payload: ContactMessage, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    if not allow_contact(client_ip):
        raise HTTPException(status_code=429, detail="Too many messages. Try again later.")

    if mongodb_status != "connected":
        raise HTTPException(
            status_code=503,
            detail="Message storage is not configured on this server.",
        )

    document = sanitize_contact(payload.model_dump())
    try:
        store_contact(document)
    except RuntimeError:
        raise HTTPException(
            status_code=503,
            detail="Message storage is not configured on this server.",
        ) from None

    return {"status": "stored"}
