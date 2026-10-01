from fastapi import APIRouter, HTTPException, Query

from app.api.dependencies import loaded_data
from app.schemas.forecast import ForecastPoint, ForecastResponse
from app.services.forecast_service import (
    history_points,
    latest_feature_row,
    next_hour_forecast,
    recent_forecasts,
)
from app.services.persistence import persist_forecast_point

router = APIRouter(tags=["forecast"])


@router.get("/energy/history")
def energy_history(limit: int = Query(default=168, ge=1, le=500)):
    data = loaded_data()
    return {"items": history_points(data, limit=limit)}


@router.get("/forecast/latest")
def forecast_latest() -> dict:
    data = loaded_data()
    point = latest_feature_row(data)
    return {
        "model": data.metadata["selected_model"],
        "note": "Prediction for the last hour in the historical dataset, not a live grid feed.",
        "forecast": point,
    }


@router.get("/forecasts/recent")
def read_recent_forecasts(limit: int = Query(default=8, ge=1, le=50)):
    data = loaded_data()
    return recent_forecasts(data, limit=limit)


@router.post("/forecast", response_model=ForecastResponse)
def create_forecast() -> ForecastResponse:
    data = loaded_data()
    try:
        point = next_hour_forecast(data)
    except ValueError:
        raise HTTPException(status_code=400, detail="Insufficient historical data for a forecast.") from None
    persist_forecast_point(point, source="inference")
    return ForecastResponse(
        model=data.metadata["selected_model"],
        note=(
            "One-hour-ahead estimate after the last known demand hour. "
            "Not an operational dispatch instruction."
        ),
        forecast=ForecastPoint(
            utc_timestamp=point["utc_timestamp"],
            actual_load_mw=point["actual_load_mw"],
            predicted_load_mw=point["predicted_load_mw"],
            temperature_c=point["temperature_c"],
            relative_humidity_pct=point["relative_humidity_pct"],
            wind_speed_kmh=point["wind_speed_kmh"],
        ),
    )
