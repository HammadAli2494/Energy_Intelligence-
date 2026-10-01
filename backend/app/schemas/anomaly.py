from pydantic import BaseModel


class AnomalyRecord(BaseModel):
    id: str
    utc_timestamp: str
    actual_load_mw: float
    predicted_load_mw: float
    residual_mw: float
    abs_residual_mw: float
    severity: str
    note: str = (
        "Unusual consumption relative to the forecast. This is not proof of equipment failure."
    )


class AnomalyListResponse(BaseModel):
    rule: str
    valid_mae_mw: float
    medium_threshold_mw: float
    high_threshold_mw: float
    total: int
    items: list[AnomalyRecord]
