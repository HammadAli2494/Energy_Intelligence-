"""Load a saved one-hour-ahead forecast artifact and predict.

Training lives in ml_pipeline/train.py. This module only runs inference.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import pandas as pd

from app.ml.features import FEATURE_COLUMNS, TARGET_COLUMN


def load_forecast_artifact(path: str | Path) -> dict:
    artifact = joblib.load(path)
    required = {"model_type", "feature_columns", "target"}
    missing = required.difference(artifact)
    if missing:
        raise ValueError(f"Model file is missing keys: {sorted(missing)}")
    return artifact


def predict_forecast(artifact: dict, features: pd.DataFrame) -> pd.Series:
    columns = artifact["feature_columns"]
    missing = set(columns).difference(features.columns)
    if missing:
        raise ValueError(f"Features missing from input: {sorted(missing)}")

    frame = features[columns]
    model_type = artifact["model_type"]

    if model_type == "persistence":
        values = frame["lag_1"].to_numpy()
    elif model_type == "moving_average_24":
        values = frame["rolling_mean_24"].to_numpy()
    else:
        pipeline = artifact.get("sklearn_pipeline")
        if pipeline is None:
            raise ValueError(f"No sklearn pipeline stored for model_type={model_type}.")
        values = pipeline.predict(frame)

    return pd.Series(values, index=features.index, name="predicted_load_mw")
