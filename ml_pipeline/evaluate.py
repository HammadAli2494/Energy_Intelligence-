"""Print saved model metrics. Does not retrain.

Usage (from the project root):

    python ml_pipeline/evaluate.py
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

from app.ml.features import TARGET_COLUMN  # noqa: E402
from app.ml.metrics import regression_metrics  # noqa: E402
from app.ml.predictor import load_forecast_artifact, predict_forecast  # noqa: E402
from app.ml.split import time_split  # noqa: E402

logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the saved forecast model.")
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
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    if not args.model.exists():
        logger.error("No saved model. Run: python ml_pipeline/train.py")
        return 1

    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    logger.info("Selected model: %s", metadata["selected_model"])
    logger.info("Selection rule: %s", metadata["selection_rule"])

    print()
    print(f"{'model':<24} {'valid MAE':>10} {'valid RMSE':>11} {'test MAE':>10} {'test RMSE':>11}")
    for name, scores in metadata["metrics"].items():
        marker = "*" if name == metadata["selected_model"] else " "
        print(
            f"{marker}{name:<23} {scores['valid']['mae']:10.2f} {scores['valid']['rmse']:11.2f} "
            f"{scores['test']['mae']:10.2f} {scores['test']['rmse']:11.2f}"
        )

    if args.features.exists():
        frame = pd.read_csv(args.features)
        _, _, test = time_split(frame)
        artifact = load_forecast_artifact(args.model)
        predicted = predict_forecast(artifact, test)
        live = regression_metrics(test[TARGET_COLUMN], predicted)
        logger.info("Recomputed test MAE from saved model: %s MW", live["mae"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
