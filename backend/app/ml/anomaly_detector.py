"""Flag unusual demand using forecast residuals.

An anomaly here means: actual load differed from the model's expected
load by more than a documented multiple of validation MAE.

It is not evidence of equipment failure.
"""

from __future__ import annotations

import pandas as pd

from app.ml.features import TARGET_COLUMN


def residual_thresholds(valid_mae: float) -> dict[str, float]:
    return {
        "medium": 2.0 * valid_mae,
        "high": 3.0 * valid_mae,
    }


def severity_from_deviation(abs_residual: float, valid_mae: float) -> str | None:
    thresholds = residual_thresholds(valid_mae)
    if abs_residual >= thresholds["high"]:
        return "high"
    if abs_residual >= thresholds["medium"]:
        return "medium"
    return None


def add_residual_anomalies(frame: pd.DataFrame, valid_mae: float) -> pd.DataFrame:
    out = frame.copy()
    out["residual_mw"] = out["predicted_load_mw"] - out[TARGET_COLUMN]
    out["abs_residual_mw"] = out["residual_mw"].abs()
    out["severity"] = out["abs_residual_mw"].map(
        lambda value: severity_from_deviation(float(value), valid_mae)
    )
    return out


def anomaly_rows(frame: pd.DataFrame) -> pd.DataFrame:
    flagged = frame.loc[frame["severity"].notna()].copy()
    return flagged.sort_values("abs_residual_mw", ascending=False)
