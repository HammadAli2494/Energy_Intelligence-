from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from app.core.config import settings
from app.ml.anomaly_detector import residual_thresholds
from app.ml.features import TARGET_COLUMN, build_inference_row
from app.ml.predictor import predict_forecast
from app.services.app_data import AppData
from app.services.persistence import recent_forecasts_from_mongo


def _optional_float(value):
    if value is None or pd.isna(value):
        return None
    return float(value)


def _optional_severity(value):
    if value is None or pd.isna(value):
        return None
    return str(value)


def series_point(row: pd.Series) -> dict:
    actual = row.get(TARGET_COLUMN)
    residual = _optional_float(row.get("residual_mw"))
    return {
        "utc_timestamp": pd.Timestamp(row["utc"]).isoformat(),
        "actual_load_mw": None if pd.isna(actual) else float(actual),
        "predicted_load_mw": float(row["predicted_load_mw"]),
        "residual_mw": residual,
        "abs_residual_mw": None if residual is None else abs(residual),
        "severity": _optional_severity(row.get("severity")),
        "status": "Anomaly" if _optional_severity(row.get("severity")) else "Normal",
        "temperature_c": _optional_float(row.get("temperature_c")),
        "relative_humidity_pct": _optional_float(row.get("relative_humidity_pct")),
        "wind_speed_kmh": _optional_float(row.get("wind_speed_kmh")),
    }


def latest_feature_row(data: AppData) -> dict:
    return series_point(data.features.iloc[-1])


def history_points(data: AppData, limit: int = 168) -> list[dict]:
    chunk = data.features.tail(limit)
    return [series_point(row) for _, row in chunk.iterrows()]


def analytics_payload(data: AppData) -> dict:
    frame = data.features
    hourly = (
        frame.groupby("hour")[TARGET_COLUMN]
        .mean()
        .reset_index()
        .rename(columns={TARGET_COLUMN: "mean_load_mw"})
    )
    weekly = (
        frame.groupby("day_of_week")[TARGET_COLUMN]
        .mean()
        .reset_index()
        .rename(columns={TARGET_COLUMN: "mean_load_mw"})
    )
    monthly = (
        frame.groupby("month")[TARGET_COLUMN]
        .mean()
        .reset_index()
        .rename(columns={TARGET_COLUMN: "mean_load_mw"})
    )
    weather = (
        frame.assign(temp_bin=(frame["temperature_c"] / 2).round() * 2)
        .groupby("temp_bin")[TARGET_COLUMN]
        .mean()
        .reset_index()
        .rename(columns={TARGET_COLUMN: "mean_load_mw", "temp_bin": "temperature_c"})
    )
    return {
        "hourly": hourly.to_dict(orient="records"),
        "weekly": weekly.to_dict(orient="records"),
        "monthly": monthly.to_dict(orient="records"),
        "temperature_bins": weather.to_dict(orient="records"),
        "note": "Averages from the modeled feature table, not live grid telemetry.",
    }


def next_hour_forecast(data: AppData) -> dict:
    last_known = data.energy.dropna(subset=["load_mw"]).iloc[-1]["utc"]
    target = last_known + pd.Timedelta(hours=1)
    feature_row = build_inference_row(data.energy, data.weather, target)
    predicted = float(predict_forecast(data.artifact, feature_row).iloc[0])
    weather_last = data.weather.set_index("utc").loc[last_known]
    return {
        "utc_timestamp": target.isoformat(),
        "actual_load_mw": None,
        "predicted_load_mw": round(predicted, 2),
        "temperature_c": float(weather_last["temperature_c"]),
        "relative_humidity_pct": float(weather_last["relative_humidity_pct"]),
        "wind_speed_kmh": float(weather_last["wind_speed_kmh"]),
        "based_on_last_known_hour": last_known.isoformat(),
    }


def recent_anomalies(data: AppData, limit: int = 8) -> list[dict]:
    flagged = data.features.loc[data.features["severity"].notna()].sort_values("utc")
    page = flagged.tail(limit).iloc[::-1]
    return [series_point(row) for _, row in page.iterrows()]


def recent_forecasts(data: AppData, limit: int = 8) -> dict:
    stored = recent_forecasts_from_mongo(limit)
    if stored:
        items = []
        for row in stored:
            actual = row.get("actual_demand")
            predicted = row.get("predicted_demand")
            difference = row.get("difference")
            severity = row.get("severity")
            items.append(
                {
                    "utc_timestamp": row.get("timestamp"),
                    "actual_load_mw": actual,
                    "predicted_load_mw": predicted,
                    "residual_mw": difference,
                    "abs_residual_mw": None if difference is None else abs(difference),
                    "severity": severity,
                    "status": "Anomaly" if severity else "Normal",
                    "source": "mongodb",
                }
            )
        return {"source": "mongodb", "items": items}

    points = history_points(data, limit=limit)
    return {"source": "dataset", "items": list(reversed(points))}


def dashboard_summary(data: AppData) -> dict:
    latest = data.features.iloc[-1]
    previous = data.features.iloc[-2]
    change = float(latest[TARGET_COLUMN] - previous[TARGET_COLUMN])
    thresholds = residual_thresholds(data.valid_mae)
    recent = data.features.tail(24 * 7)
    anomaly_count = int(recent["severity"].notna().sum())
    selected = data.metadata["selected_model"]
    selected_metrics = data.metadata["metrics"][selected]
    try:
        next_hour = next_hour_forecast(data)
    except ValueError:
        next_hour = None
    return {
        "dataset_note": (
            "Latest values are the last hours in the OPSD extract (through Sep 2020), "
            "not live Spain grid data."
        ),
        "latest_demand_mw": float(latest[TARGET_COLUMN]),
        "predicted_demand_mw": round(float(latest["predicted_load_mw"]), 2),
        "demand_change_mw": round(change, 2),
        "latest_utc": latest["utc"].isoformat(),
        "next_hour": next_hour,
        "anomalies_last_7_days": anomaly_count,
        "anomalies_total": int(data.features["severity"].notna().sum()),
        "recent_anomalies": recent_anomalies(data, limit=8),
        "weather": {
            "location_name": settings.weather_location_name,
            "latitude": settings.weather_latitude,
            "longitude": settings.weather_longitude,
            "temperature_c": float(latest["temperature_c"]),
            "relative_humidity_pct": float(latest["relative_humidity_pct"]),
            "wind_speed_kmh": float(latest["wind_speed_kmh"]),
            "timing": "Last-known Madrid hour (t-1) used as a model input",
        },
        "model": selected,
        "valid_mae_mw": data.valid_mae,
        "model_performance": {
            "selected_model": selected,
            "selection_rule": data.metadata["selection_rule"],
            "valid": selected_metrics["valid"],
            "test": selected_metrics["test"],
            "split": data.metadata["split"],
            "units": data.metadata["units"],
        },
        "anomaly_rule": {
            "medium_mw": thresholds["medium"],
            "high_mw": thresholds["high"],
            "description": (
                "Anomalies indicate observations where actual demand deviates "
                "significantly from the model forecast."
            ),
        },
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    }
