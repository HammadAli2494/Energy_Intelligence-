"""Load energy, weather, the trained model, and precomputed residuals once."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pandas as pd

from app.core.config import settings
from app.ml.anomaly_detector import add_residual_anomalies
from app.ml.features import TARGET_COLUMN, load_processed_energy, load_processed_weather
from app.ml.predictor import load_forecast_artifact, predict_forecast

logger = logging.getLogger(__name__)


class AppData:
    def __init__(self) -> None:
        self.ready = False
        self.error = "Model data has not been loaded yet."
        self.energy = pd.DataFrame()
        self.weather = pd.DataFrame()
        self.features = pd.DataFrame()
        self.artifact = None
        self.metadata: dict = {}
        self.valid_mae: float = 0.0

    def load(self) -> None:
        if self.ready:
            return

        root = settings.project_root
        feature_path = root / "data" / "processed" / "spain_hourly_features.csv"
        energy_path = root / "data" / "processed" / "spain_hourly_load.csv"
        weather_path = root / "data" / "processed" / "madrid_hourly_weather.csv"
        model_path = root / "models" / "forecast_model.joblib"
        metadata_path = root / "models" / "model_metadata.json"

        required = {
            "feature table": feature_path,
            "energy series": energy_path,
            "weather cache": weather_path,
            "trained model": model_path,
            "model metadata": metadata_path,
        }
        missing = [name for name, path in required.items() if not path.exists()]
        if missing:
            self.ready = False
            self.error = "Missing required files: " + ", ".join(missing)
            logger.error(self.error)
            return

        self.metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        selected = self.metadata["selected_model"]
        self.valid_mae = float(self.metadata["metrics"][selected]["valid"]["mae"])
        self.artifact = load_forecast_artifact(model_path)
        self.energy = load_processed_energy(energy_path)
        self.weather = load_processed_weather(weather_path)
        self.features = pd.read_csv(feature_path)
        self.features["utc"] = pd.to_datetime(self.features["utc_timestamp"], utc=True)
        self.features["predicted_load_mw"] = predict_forecast(self.artifact, self.features)
        self.features = add_residual_anomalies(self.features, self.valid_mae)
        self.ready = True
        self.error = ""
        logger.info(
            "Loaded %s feature hours and model %s.",
            f"{len(self.features):,}",
            selected,
        )


app_data = AppData()


def require_ready() -> AppData:
    if not app_data.ready:
        raise RuntimeError(app_data.error)
    return app_data
