"""Write residual anomalies for the feature table.

Usage:

    python ml_pipeline/detect_anomalies.py
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.ml.anomaly_detector import add_residual_anomalies, anomaly_rows  # noqa: E402
from app.ml.predictor import load_forecast_artifact, predict_forecast  # noqa: E402

logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Flag residual anomalies.")
    parser.add_argument(
        "--features",
        type=Path,
        default=ROOT / "data" / "processed" / "spain_hourly_features.csv",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=ROOT / "models" / "forecast_model.joblib",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=ROOT / "models" / "model_metadata.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "data" / "processed" / "anomalies.csv",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    selected = metadata["selected_model"]
    valid_mae = float(metadata["metrics"][selected]["valid"]["mae"])
    frame = pd.read_csv(args.features)
    artifact = load_forecast_artifact(args.model)
    frame["predicted_load_mw"] = predict_forecast(artifact, frame)
    scored = add_residual_anomalies(frame, valid_mae)
    flagged = anomaly_rows(scored)
    flagged.to_csv(args.output, index=False)
    logger.info("Wrote %s anomalies to %s", f"{len(flagged):,}", args.output)
    logger.info("Medium: %s", int((flagged["severity"] == "medium").sum()))
    logger.info("High: %s", int((flagged["severity"] == "high").sum()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
