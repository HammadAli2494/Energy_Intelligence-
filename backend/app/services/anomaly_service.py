from __future__ import annotations

import pandas as pd

from app.ml.anomaly_detector import anomaly_rows, residual_thresholds
from app.ml.features import TARGET_COLUMN
from app.services.app_data import AppData

ANOMALY_NOTE = (
    "Unusual consumption relative to the forecast. This is not proof of equipment failure."
)


def _record(row: pd.Series) -> dict:
    stamp = pd.Timestamp(row["utc"]).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "id": stamp,
        "utc_timestamp": stamp,
        "actual_load_mw": float(row[TARGET_COLUMN]),
        "predicted_load_mw": round(float(row["predicted_load_mw"]), 2),
        "residual_mw": round(float(row["residual_mw"]), 2),
        "abs_residual_mw": round(float(row["abs_residual_mw"]), 2),
        "severity": row["severity"],
        "note": ANOMALY_NOTE,
    }


def list_anomalies(
    data: AppData,
    severity: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    flagged = anomaly_rows(data.features)
    if severity in {"medium", "high"}:
        flagged = flagged.loc[flagged["severity"] == severity]
    total = int(len(flagged))
    page = flagged.iloc[offset : offset + limit]
    thresholds = residual_thresholds(data.valid_mae)
    return {
        "rule": (
            "Residual method: |actual - predicted| compared with 2019 validation MAE "
            f"({data.valid_mae} MW). Medium >= 2x MAE, high >= 3x MAE."
        ),
        "valid_mae_mw": data.valid_mae,
        "medium_threshold_mw": thresholds["medium"],
        "high_threshold_mw": thresholds["high"],
        "total": total,
        "items": [_record(row) for _, row in page.iterrows()],
    }


def get_anomaly(data: AppData, anomaly_id: str) -> dict | None:
    flagged = anomaly_rows(data.features)
    stamps = pd.to_datetime(flagged["utc_timestamp"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    match = flagged.loc[stamps == anomaly_id]
    if match.empty:
        return None
    return _record(match.iloc[0])
