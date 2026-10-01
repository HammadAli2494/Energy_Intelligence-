from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Loads configuration from environment variables and backend/.env."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mongodb_uri: str = ""
    mongodb_db_name: str = "energy_intelligence"
    database_name: str = ""
    frontend_url: str = "http://localhost:5173"
    environment: str = "development"
    weather_api_base_url: str = "https://api.open-meteo.com/v1"
    weather_archive_api_base_url: str = "https://archive-api.open-meteo.com/v1"
    weather_latitude: float = 40.4168
    weather_longitude: float = -3.7038
    weather_location_name: str = "Madrid"
    weather_timeout_seconds: float = 20.0
    weather_current_cache_seconds: int = 600

    @property
    def db_name(self) -> str:
        name = (self.database_name or self.mongodb_db_name).strip()
        return name or "energy_intelligence"

    @property
    def project_root(self) -> Path:
        return BACKEND_DIR.parent

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.frontend_url.split(",")
            if origin.strip()
        ]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


settings = Settings()
