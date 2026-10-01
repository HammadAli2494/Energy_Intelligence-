import logging

from fastapi import APIRouter, HTTPException

from app.schemas.weather import CurrentWeatherResponse
from app.services.weather_service import WeatherServiceError, fetch_current_weather

logger = logging.getLogger(__name__)

router = APIRouter(tags=["weather"])


@router.get("/weather", response_model=CurrentWeatherResponse)
def get_weather() -> CurrentWeatherResponse:
    """Return current Madrid weather from Open-Meteo."""
    try:
        payload = fetch_current_weather()
    except WeatherServiceError:
        logger.error("Weather request failed.")
        raise HTTPException(
            status_code=503,
            detail="Weather data is temporarily unavailable.",
        ) from None

    return CurrentWeatherResponse.model_validate(payload)
