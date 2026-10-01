from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.services import weather_service
from app.services.weather_service import WeatherServiceError, fetch_current_weather

client = TestClient(app)


CURRENT_PAYLOAD = {
    "current": {
        "time": "2026-09-20T07:00",
        "temperature_2m": 21.4,
        "relative_humidity_2m": 48,
        "wind_speed_10m": 9.2,
    }
}


def setup_function() -> None:
    weather_service.clear_weather_cache()


def test_current_weather_parses_open_meteo_payload() -> None:
    with patch("app.services.weather_service._get_json", return_value=CURRENT_PAYLOAD):
        result = fetch_current_weather()

    assert result["temperature_c"] == 21.4
    assert result["relative_humidity_pct"] == 48
    assert result["wind_speed_kmh"] == 9.2
    assert result["location"]["name"] == "Madrid"
    assert result["source"] == "open-meteo"


def test_current_weather_uses_cache_on_second_call() -> None:
    with patch(
        "app.services.weather_service._get_json",
        return_value=CURRENT_PAYLOAD,
    ) as mocked:
        first = fetch_current_weather()
        second = fetch_current_weather()

    assert first == second
    assert mocked.call_count == 1


def test_timeout_becomes_weather_service_error() -> None:
    with patch("app.services.weather_service.httpx.Client") as mocked_client:
        mocked_client.return_value.__enter__.return_value.get.side_effect = (
            httpx.TimeoutException("timed out")
        )
        try:
            weather_service._get_json("https://example.invalid", {})
        except WeatherServiceError as exc:
            assert "timed out" in str(exc).lower()
            return
        raise AssertionError("Expected WeatherServiceError")


def test_historical_payload_becomes_hourly_table() -> None:
    payload = {
        "hourly": {
            "time": ["2018-06-01T00:00", "2018-06-01T01:00"],
            "temperature_2m": [22.0, 21.5],
            "relative_humidity_2m": [40, 42],
            "wind_speed_10m": [8.0, 9.0],
        }
    }
    frame = weather_service._archive_to_frame(payload)
    assert list(frame.columns) == [
        "utc_timestamp",
        "temperature_c",
        "relative_humidity_pct",
        "wind_speed_kmh",
    ]
    assert len(frame) == 2
    assert frame["temperature_c"].iloc[0] == 22.0


def test_weather_endpoint_returns_current_conditions() -> None:
    with patch(
        "app.api.routes.weather.fetch_current_weather",
        return_value={
            "location": {"name": "Madrid", "latitude": 40.4168, "longitude": -3.7038},
            "source": "open-meteo",
            "observed_at_utc": "2026-09-20T07:00",
            "temperature_c": 21.4,
            "relative_humidity_pct": 48,
            "wind_speed_kmh": 9.2,
        },
    ):
        response = client.get("/api/v1/weather")

    assert response.status_code == 200
    payload = response.json()
    assert payload["temperature_c"] == 21.4
    assert payload["location"]["name"] == "Madrid"


def test_weather_endpoint_hides_upstream_failure() -> None:
    with patch(
        "app.api.routes.weather.fetch_current_weather",
        side_effect=WeatherServiceError("The weather service timed out."),
    ):
        response = client.get("/api/v1/weather")

    assert response.status_code == 503
    assert response.json()["detail"] == "Weather data is temporarily unavailable."
