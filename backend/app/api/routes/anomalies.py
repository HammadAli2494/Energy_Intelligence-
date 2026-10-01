from fastapi import APIRouter, HTTPException, Query

from app.api.dependencies import loaded_data
from app.services.anomaly_service import get_anomaly, list_anomalies

router = APIRouter(tags=["anomalies"])


@router.get("/anomalies")
def read_anomalies(
    severity: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    if severity is not None and severity not in {"medium", "high"}:
        raise HTTPException(status_code=400, detail="severity must be medium or high.")
    data = loaded_data()
    return list_anomalies(data, severity=severity, limit=limit, offset=offset)


@router.get("/anomalies/{anomaly_id}")
def read_anomaly(anomaly_id: str):
    data = loaded_data()
    item = get_anomaly(data, anomaly_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Anomaly not found.")
    return item
