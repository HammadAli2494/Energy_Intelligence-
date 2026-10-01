"""Persist real forecast and anomaly rows to MongoDB when Atlas is connected."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import pandas as pd
from pymongo.errors import PyMongoError

from app.database.mongodb import get_database
from app.ml.anomaly_detector import residual_thresholds
from app.ml.features import TARGET_COLUMN
from app.services.app_data import AppData

logger = logging.getLogger(__name__)

FORECAST_COLLECTION = "forecast_history"
ANOMALY_COLLECTION = "anomalies"
MODEL_RUNS_COLLECTION = "model_runs"
CONTACT_COLLECTION = "contact_messages"


def _utc_key(stamp) -> str:
    value = pd.Timestamp(stamp)
    if value.tzinfo is None:
        value = value.tz_localize("UTC")
    else:
        value = value.tz_convert("UTC")
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def ensure_indexes() -> None:
    database = get_database()
    if database is None:
        return
    database[FORECAST_COLLECTION].create_index("timestamp", unique=True)
    database[ANOMALY_COLLECTION].create_index("timestamp", unique=True)
    database[MODEL_RUNS_COLLECTION].create_index("model_name")
    database[CONTACT_COLLECTION].create_index("created_at")
    database[CONTACT_COLLECTION].create_index("email")


def persist_forecast_point(point: dict, source: str) -> None:
    database = get_database()
    if database is None:
        return

    actual = point.get("actual_load_mw")
    predicted = point.get("predicted_load_mw")
    difference = None
    if actual is not None and predicted is not None:
        difference = round(float(predicted) - float(actual), 2)

    document = {
        "timestamp": _utc_key(point["utc_timestamp"]),
        "actual_demand": None if actual is None else round(float(actual), 2),
        "predicted_demand": None if predicted is None else round(float(predicted), 2),
        "difference": difference,
        "severity": point.get("severity"),
        "source": source,
        "created_at": datetime.now(timezone.utc),
    }
    try:
        database[FORECAST_COLLECTION].update_one(
            {"timestamp": document["timestamp"]},
            {"$set": document},
            upsert=True,
        )
    except PyMongoError:
        logger.error("Could not persist a forecast row.")


def persist_anomaly_row(row: pd.Series, thresholds: dict[str, float]) -> None:
    database = get_database()
    if database is None:
        return

    stamp = _utc_key(row["utc"])
    document = {
        "timestamp": stamp,
        "actual_demand": round(float(row[TARGET_COLUMN]), 2),
        "predicted_demand": round(float(row["predicted_load_mw"]), 2),
        "deviation": round(float(row["abs_residual_mw"]), 2),
        "difference": round(float(row["residual_mw"]), 2),
        "threshold_medium": thresholds["medium"],
        "threshold_high": thresholds["high"],
        "severity": str(row["severity"]),
        "is_anomaly": True,
        "created_at": datetime.now(timezone.utc),
    }
    try:
        database[ANOMALY_COLLECTION].update_one(
            {"timestamp": stamp},
            {"$set": document},
            upsert=True,
        )
    except PyMongoError:
        logger.error("Could not persist an anomaly row.")


def persist_model_run(data: AppData) -> None:
    database = get_database()
    if database is None:
        return

    selected = data.metadata["selected_model"]
    metrics = data.metadata["metrics"][selected]
    document = {
        "model_name": selected,
        "mae": metrics["valid"]["mae"],
        "rmse": metrics["valid"]["rmse"],
        "mape": metrics["valid"]["mape"],
        "test_mae": metrics["test"]["mae"],
        "test_rmse": metrics["test"]["rmse"],
        "test_mape": metrics["test"]["mape"],
        "validation_period": data.metadata["split"]["valid"],
        "test_period": data.metadata["split"]["test"],
        "selection_rule": data.metadata["selection_rule"],
        "created_at": datetime.now(timezone.utc),
    }
    try:
        database[MODEL_RUNS_COLLECTION].update_one(
            {
                "model_name": selected,
                "validation_period": document["validation_period"],
            },
            {"$set": document},
            upsert=True,
        )
    except PyMongoError:
        logger.error("Could not persist model-run metadata.")


def seed_analytics_store(data: AppData) -> None:
    """Write a bounded slice of already-computed results. Does not invent values."""
    if get_database() is None or not data.ready:
        return

    ensure_indexes()
    thresholds = residual_thresholds(data.valid_mae)
    recent = data.features.tail(168)
    for _, row in recent.iterrows():
        persist_forecast_point(
            {
                "utc_timestamp": row["utc"],
                "actual_load_mw": None if pd.isna(row[TARGET_COLUMN]) else float(row[TARGET_COLUMN]),
                "predicted_load_mw": float(row["predicted_load_mw"]),
                "severity": None if pd.isna(row.get("severity")) else str(row["severity"]),
            },
            source="dataset",
        )

    flagged = data.features.loc[data.features["severity"].notna()].sort_values("utc").tail(200)
    for _, row in flagged.iterrows():
        persist_anomaly_row(row, thresholds)

    persist_model_run(data)
    logger.info("Seeded MongoDB from computed forecast and anomaly rows.")


def recent_forecasts_from_mongo(limit: int) -> list[dict] | None:
    database = get_database()
    if database is None:
        return None
    try:
        cursor = (
            database[FORECAST_COLLECTION]
            .find({}, {"_id": 0})
            .sort("timestamp", -1)
            .limit(limit)
        )
        return list(cursor)
    except PyMongoError:
        logger.error("Could not read forecast_history.")
        return None
