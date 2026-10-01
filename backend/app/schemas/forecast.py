from pydantic import BaseModel, Field


class ForecastPoint(BaseModel):
    utc_timestamp: str
    actual_load_mw: float | None = None
    predicted_load_mw: float
    temperature_c: float | None = None
    relative_humidity_pct: float | None = None
    wind_speed_kmh: float | None = None


class ForecastResponse(BaseModel):
    model: str
    note: str
    forecast: ForecastPoint
