"""Train one-hour-ahead demand models and save the winner.

Fits only on the training period. Chooses the model with the lowest
validation MAE. Test metrics are reported after that choice.

Usage (from the project root):

    python ml_pipeline/train.py
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.ml.features import FEATURE_COLUMNS, TARGET_COLUMN  # noqa: E402
from app.ml.metrics import regression_metrics  # noqa: E402
from app.ml.predictor import predict_forecast  # noqa: E402
from app.ml.split import time_split  # noqa: E402

logger = logging.getLogger(__name__)

DEFAULT_FEATURES = ROOT / "data" / "processed" / "spain_hourly_features.csv"
DEFAULT_MODEL = ROOT / "models" / "forecast_model.joblib"
DEFAULT_METADATA = ROOT / "models" / "model_metadata.json"
DEFAULT_FEATURE_LIST = ROOT / "models" / "feature_list.json"


def _baseline_artifact(model_type: str) -> dict:
    return {
        "model_type": model_type,
        "sklearn_pipeline": None,
        "feature_columns": FEATURE_COLUMNS,
        "target": TARGET_COLUMN,
    }


def _sklearn_artifact(model_type: str, pipeline: Pipeline) -> dict:
    return {
        "model_type": model_type,
        "sklearn_pipeline": pipeline,
        "feature_columns": FEATURE_COLUMNS,
        "target": TARGET_COLUMN,
    }


def _linear_pipeline() -> Pipeline:
    return Pipeline(
        [
            ("scaler", StandardScaler()),
            ("model", LinearRegression()),
        ]
    )


def _forest() -> RandomForestRegressor:
    return RandomForestRegressor(
        n_estimators=80,
        max_depth=12,
        min_samples_leaf=5,
        random_state=42,
        n_jobs=-1,
    )


def _boosting() -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        max_depth=8,
        learning_rate=0.08,
        max_iter=200,
        random_state=42,
    )


def _feature_importance(artifact: dict) -> dict[str, float] | None:
    estimator = artifact.get("sklearn_pipeline")
    if estimator is None:
        return None
    if hasattr(estimator, "named_steps"):
        estimator = estimator.named_steps.get("model", estimator)
    if hasattr(estimator, "feature_importances_"):
        values = estimator.feature_importances_
    elif hasattr(estimator, "coef_"):
        values = estimator.coef_
    else:
        return None
    return {
        name: round(float(value), 4)
        for name, value in zip(FEATURE_COLUMNS, values)
    }


def evaluate_artifact(artifact: dict, frame: pd.DataFrame) -> dict[str, float]:
    predicted = predict_forecast(artifact, frame)
    return regression_metrics(frame[TARGET_COLUMN], predicted)


def train_and_compare(frame: pd.DataFrame) -> tuple[dict, dict]:
    train, valid, test = time_split(frame)
    logger.info("Train hours: %s", f"{len(train):,}")
    logger.info("Valid hours: %s", f"{len(valid):,}")
    logger.info("Test hours:  %s (2020 stress period)", f"{len(test):,}")

    candidates: dict[str, dict] = {
        "persistence": _baseline_artifact("persistence"),
        "moving_average_24": _baseline_artifact("moving_average_24"),
    }

    linear = _linear_pipeline()
    linear.fit(train[FEATURE_COLUMNS], train[TARGET_COLUMN])
    candidates["linear_regression"] = _sklearn_artifact("linear_regression", linear)

    forest = _forest()
    logger.info("Fitting random forest...")
    forest.fit(train[FEATURE_COLUMNS], train[TARGET_COLUMN])
    candidates["random_forest"] = _sklearn_artifact("random_forest", forest)

    boosting = _boosting()
    logger.info("Fitting histogram gradient boosting...")
    boosting.fit(train[FEATURE_COLUMNS], train[TARGET_COLUMN])
    candidates["hist_gradient_boosting"] = _sklearn_artifact(
        "hist_gradient_boosting", boosting
    )

    comparison: dict[str, dict] = {}
    for name, artifact in candidates.items():
        comparison[name] = {
            "train": evaluate_artifact(artifact, train),
            "valid": evaluate_artifact(artifact, valid),
            "test": evaluate_artifact(artifact, test),
        }
        logger.info(
            "%s | valid MAE=%s MW | test MAE=%s MW",
            name,
            comparison[name]["valid"]["mae"],
            comparison[name]["test"]["mae"],
        )

    selected_name = min(comparison, key=lambda name: comparison[name]["valid"]["mae"])
    selected_artifact = candidates[selected_name]
    selected_artifact["selected_because"] = "lowest validation MAE"
    importances = _feature_importance(selected_artifact)

    metadata = {
        "selected_model": selected_name,
        "selection_rule": "lowest validation MAE; test set was not used to choose",
        "target": TARGET_COLUMN,
        "feature_columns": FEATURE_COLUMNS,
        "feature_importance": importances,
        "split": {
            "train": "utc < 2019-01-01",
            "valid": "2019-01-01 <= utc < 2020-01-01",
            "test": "utc >= 2020-01-01 (COVID demand shift)",
            "shuffled": False,
            "n_train": int(len(train)),
            "n_valid": int(len(valid)),
            "n_test": int(len(test)),
        },
        "metrics": comparison,
        "units": {"mae": "MW", "rmse": "MW", "mape": "percent"},
        "notes": [
            "Persistence predicts lag_1. Moving average predicts rolling_mean_24.",
            "2020 test performance can be worse because of COVID-related demand changes.",
            "MAPE is defined because demand is always positive in this table.",
        ],
    }
    return selected_artifact, metadata


def save_training_outputs(
    artifact: dict,
    metadata: dict,
    model_path: Path,
    metadata_path: Path,
    feature_list_path: Path,
) -> None:
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, model_path)
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    feature_list_path.write_text(
        json.dumps(
            {
                "target": TARGET_COLUMN,
                "features": FEATURE_COLUMNS,
                "selected_model": metadata["selected_model"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    logger.info("Saved %s", model_path)
    logger.info("Saved %s", metadata_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Train and compare forecast models.")
    parser.add_argument("--features", type=Path, default=DEFAULT_FEATURES)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--metadata", type=Path, default=DEFAULT_METADATA)
    parser.add_argument("--feature-list", type=Path, default=DEFAULT_FEATURE_LIST)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    if not args.features.exists():
        logger.error("Feature table not found. Run: python ml_pipeline/build_features.py")
        return 1

    frame = pd.read_csv(args.features)
    artifact, metadata = train_and_compare(frame)
    save_training_outputs(
        artifact,
        metadata,
        args.model,
        args.metadata,
        args.feature_list,
    )

    selected = metadata["selected_model"]
    valid_mae = metadata["metrics"][selected]["valid"]["mae"]
    test_mae = metadata["metrics"][selected]["test"]["mae"]
    logger.info("Selected %s (valid MAE %.2f MW, test MAE %.2f MW)", selected, valid_mae, test_mae)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
