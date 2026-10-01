"""Regression metrics for energy demand (MW)."""

from __future__ import annotations

import numpy as np


def regression_metrics(y_true, y_pred) -> dict[str, float]:
    """MAE and RMSE in MW. MAPE in percent. y_true must be non-zero."""
    actual = np.asarray(y_true, dtype=float)
    predicted = np.asarray(y_pred, dtype=float)
    if actual.shape != predicted.shape:
        raise ValueError("y_true and y_pred must have the same shape.")
    if np.any(actual == 0):
        raise ValueError("MAPE is undefined when actual demand is 0.")

    errors = predicted - actual
    mae = float(np.mean(np.abs(errors)))
    rmse = float(np.sqrt(np.mean(errors**2)))
    mape = float(np.mean(np.abs(errors / actual)) * 100)
    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape": round(mape, 3),
    }
