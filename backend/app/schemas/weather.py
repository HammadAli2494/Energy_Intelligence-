from pydantic import BaseModel, Field


class WeatherLocation(BaseModel):
    name: str
    latitude: float
    longitude: float


class CurrentWeatherResponse(BaseModel):
    location: WeatherLocation
    source: str = "open-meteo"
    observed_at_utc: str
    temperature_c: float | None = Field(default=None)
    relative_humidity_pct: float | None = Field(default=None)
    wind_speed_kmh: float | None = Field(default=None)
