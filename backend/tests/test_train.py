import pandas as pd

from app.ml.features import FEATURE_COLUMNS, TARGET_COLUMN
from app.ml.metrics import regression_metrics
from app.ml.predictor import predict_forecast
from app.ml.split import time_split


def test_metrics_on_perfect_predictions() -> None:
    scores = regression_metrics([100.0, 200.0, 300.0], [100.0, 200.0, 300.0])
    assert scores["mae"] == 0
    assert scores["rmse"] == 0
    assert scores["mape"] == 0


def test_metrics_known_error() -> None:
    scores = regression_metrics([100.0, 100.0], [110.0, 90.0])
    assert scores["mae"] == 10
    assert scores["rmse"] == 10
    assert scores["mape"] == 10


def test_time_split_is_chronological_and_not_shuffled() -> None:
    frame = pd.DataFrame(
        {
            "utc_timestamp": [
                "2020-02-01T00:00:00Z",
                "2018-06-01T00:00:00Z",
                "2019-06-01T00:00:00Z",
                "2017-01-01T00:00:00Z",
            ],
            "load_mw": [1, 2, 3, 4],
        }
    )
    train, valid, test = time_split(frame)
    train_times = pd.to_datetime(train["utc_timestamp"], utc=True)
    valid_times = pd.to_datetime(valid["utc_timestamp"], utc=True)
    test_times = pd.to_datetime(test["utc_timestamp"], utc=True)

    assert train_times.max() < valid_times.min()
    assert valid_times.max() < test_times.min()
    assert train_times.is_monotonic_increasing


def test_persistence_predicts_lag_1() -> None:
    frame = pd.DataFrame(
        {
            col: [10.0, 20.0, 30.0]
            for col in FEATURE_COLUMNS
        }
    )
    frame["lag_1"] = [100.0, 200.0, 300.0]
    frame[TARGET_COLUMN] = [101.0, 202.0, 303.0]
    artifact = {
        "model_type": "persistence",
        "sklearn_pipeline": None,
        "feature_columns": FEATURE_COLUMNS,
        "target": TARGET_COLUMN,
    }
    predicted = predict_forecast(artifact, frame)
    assert predicted.tolist() == [100.0, 200.0, 300.0]
