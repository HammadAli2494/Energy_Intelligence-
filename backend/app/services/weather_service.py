"""Open-Meteo weather client.

All external weather HTTP calls stay in this module. There is no API key.
Coordinates and base URLs come from environment settings, not the frontend.
"""

from __future__ import annotations

import logging
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import httpx
import pandas as pd

from app.core.config import settings

logger = logging.getLogger(__name__)
logging.getLogger("httpx").setLevel(logging.WARNING)

HOURLY_VARIABLES = "temperature_2m,relative_humidity_2m,wind_speed_10m"
CURRENT_VARIABLES = "temperature_2m,relative_humidity_2m,wind_speed_10m"

_current_cache: dict | None = None
_current_cache_expires_at: datetime | None = None


class WeatherServiceError(Exception):
    """Raised when Open-Meteo cannot be used. Safe to show a generic API message."""


def clear_weather_cache() -> None:
    global _current_cache, _current_cache_expires_at
    _current_cache = None
    _current_cache_expires_at = None


def _get_json(url: str, params: dict) -> dict:
    timeout = httpx.Timeout(settings.weather_timeout_seconds)
    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.get(url, params=params)
    except httpx.TimeoutException as exc:
        logger.error("Weather API timeout.")
        raise WeatherServiceError("The weather service timed out.") from exc
    except httpx.RequestError as exc:
        logger.error("Weather API connection failure.")
        raise WeatherServiceError("The weather service is unavailable.") from exc

    if response.status_code != 200:
        logger.error("Weather API status %s.", response.status_code)
        raise WeatherServiceError("The weather service returned an invalid response.")

    try:
        payload = response.json()
    except ValueError as exc:
        logger.error("Weather API returned non-JSON.")
        raise WeatherServiceError("The weather service returned an invalid response.") from exc

    if not isinstance(payload, dict) or payload.get("error"):
        logger.error("Weather API returned an error payload.")
        raise WeatherServiceError("The weather service returned an invalid response.")
    return payload


def fetch_current_weather() -> dict:
    """Current Madrid weather. Cached briefly so refresh does not hammer Open-Meteo."""
    global _current_cache, _current_cache_expires_at

    now = datetime.now(timezone.utc)
    if (
        _current_cache is not None
        and _current_cache_expires_at is not None
        and now < _current_cache_expires_at
    ):
        return _current_cache

    url = f"{settings.weather_api_base_url.rstrip('/')}/forecast"
    payload = _get_json(
        url,
        {
            "latitude": settings.weather_latitude,
            "longitude": settings.weather_longitude,
            "current": CURRENT_VARIABLES,
            "timezone": "UTC",
        },
    )
    current = payload.get("current")
    if not isinstance(current, dict):
        raise WeatherServiceError("The weather service returned an invalid response.")

    result = {
        "location": {
            "name": settings.weather_location_name,
            "latitude": settings.weather_latitude,
            "longitude": settings.weather_longitude,
        },
        "source": "open-meteo",
        "observed_at_utc": str(current.get("time") or now.strftime("%Y-%m-%dT%H:%M")),
        "temperature_c": current.get("temperature_2m"),
        "relative_humidity_pct": current.get("relative_humidity_2m"),
        "wind_speed_kmh": current.get("wind_speed_10m"),
    }
    _current_cache = result
    _current_cache_expires_at = now + timedelta(seconds=settings.weather_current_cache_seconds)
    return result


def _year_windows(start: date, end: date):
    year = start.year
    while year <= end.year:
        window_start = max(start, date(year, 1, 1))
        window_end = min(end, date(year, 12, 31))
        yield window_start, window_end
        year += 1


def _archive_to_frame(payload: dict) -> pd.DataFrame:
    hourly = payload.get("hourly")
    if not isinstance(hourly, dict) or "time" not in hourly:
        raise WeatherServiceError("The weather service returned an invalid response.")

    frame = pd.DataFrame(
        {
            "utc_timestamp": pd.to_datetime(hourly["time"], utc=True),
            "temperature_c": hourly.get("temperature_2m"),
            "relative_humidity_pct": hourly.get("relative_humidity_2m"),
            "wind_speed_kmh": hourly.get("wind_speed_10m"),
        }
    )
    return frame.drop_duplicates(subset=["utc_timestamp"]).sort_values("utc_timestamp")


def _fetch_archive_window(start: date, end: date) -> pd.DataFrame:
    url = f"{settings.weather_archive_api_base_url.rstrip('/')}/archive"
    payload = _get_json(
        url,
        {
            "latitude": settings.weather_latitude,
            "longitude": settings.weather_longitude,
            "start_date": start.isoformat(),
            "end_date": end.isoformat(),
            "hourly": HOURLY_VARIABLES,
            "timezone": "UTC",
        },
    )
    return _archive_to_frame(payload)


def fetch_historical_hourly(
    start: date,
    end: date,
    cache_path: str | Path | None = None,
    force: bool = False,
) -> pd.DataFrame:
    """Hourly Madrid weather. Uses a CSV cache so the same years are not re-downloaded."""
    if end < start:
        raise ValueError("Weather end date must be on or after the start date.")

    cache_file = Path(cache_path) if cache_path else None
    if cache_file and cache_file.exists() and not force:
        cached = pd.read_csv(cache_file, parse_dates=["utc_timestamp"])
        cached["utc_timestamp"] = pd.to_datetime(cached["utc_timestamp"], utc=True)
        logger.info("Loaded cached weather from %s", cache_file.name)
        start_ts = pd.Timestamp(start, tz="UTC")
        end_ts = pd.Timestamp(end, tz="UTC") + pd.Timedelta(hours=23)
        return cached[(cached["utc_timestamp"] >= start_ts) & (cached["utc_timestamp"] <= end_ts)]

    frames = []
    windows = list(_year_windows(start, end))
    for index, (window_start, window_end) in enumerate(windows):
        logger.info("Requesting Open-Meteo archive %s to %s", window_start, window_end)
        frames.append(_fetch_archive_window(window_start, window_end))
        if index < len(windows) - 1:
            time.sleep(0.25)

    weather = (
        pd.concat(frames, ignore_index=True)
        .drop_duplicates(subset=["utc_timestamp"])
        .sort_values("utc_timestamp")
        .reset_index(drop=True)
    )

    if cache_file:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        weather.to_csv(cache_file, index=False)
        logger.info("Saved weather cache to %s", cache_file)

    return weather
