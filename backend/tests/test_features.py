from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.ml.features import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    add_features,
    drop_incomplete_rows,
    join_energy_and_weather,
    to_feature_table,
)


def _toy_frames() -> tuple[pd.DataFrame, pd.DataFrame]:
    hours = pd.date_range("2018-01-01", periods=200, freq="h", tz="UTC")
    energy = pd.DataFrame(
        {
            "utc": hours,
            "local": hours.tz_convert("Europe/Madrid"),
            "load_mw": pd.Series(range(200), dtype="float"),
        }
    )
    weather = pd.DataFrame(
        {
            "utc": hours,
            "temperature_c": pd.Series(range(200), dtype="float") + 10,
            "relative_humidity_pct": 50.0,
            "wind_speed_kmh": 5.0,
        }
    )
    return energy, weather


def test_lags_and_rolling_means_do_not_use_the_target() -> None:
    energy, weather = _toy_frames()
    featured = drop_incomplete_rows(add_features(join_energy_and_weather(energy, weather)))
    row = featured.iloc[0]
    target_time = row["utc"]
    history = energy.set_index("utc")["load_mw"]

    assert row[TARGET_COLUMN] == history.loc[target_time]
    assert row["lag_1"] == history.loc[target_time - pd.Timedelta(hours=1)]
    assert row["lag_24"] == history.loc[target_time - pd.Timedelta(hours=24)]
    assert row["lag_168"] == history.loc[target_time - pd.Timedelta(hours=168)]

    expected_roll = history.loc[
        target_time - pd.Timedelta(hours=24) : target_time - pd.Timedelta(hours=1)
    ].mean()
    assert abs(row["rolling_mean_24"] - expected_roll) < 1e-9
    assert row["rolling_mean_24"] != row[TARGET_COLUMN]


def test_weather_uses_previous_hour_not_target_hour() -> None:
    energy, weather = _toy_frames()
    featured = drop_incomplete_rows(add_features(join_energy_and_weather(energy, weather)))
    row = featured.iloc[0]
    weather_at = weather.set_index("utc")
    previous = row["utc"] - pd.Timedelta(hours=1)
    same_hour = row["utc"]

    assert row["temperature_c"] == weather_at.loc[previous, "temperature_c"]
    assert row["temperature_c"] != weather_at.loc[same_hour, "temperature_c"]


def test_weekend_flag_uses_local_saturday() -> None:
    hours = pd.date_range("2018-01-06", periods=3, freq="h", tz="UTC")  # Saturday morning UTC
    energy = pd.DataFrame(
        {
            "utc": hours,
            "local": hours.tz_convert("Europe/Madrid"),
            "load_mw": [20000.0, 20100.0, 20200.0],
        }
    )
    featured = add_features(energy)
    assert int(featured["is_weekend"].iloc[0]) == 1
    assert int(featured["day_of_week"].iloc[0]) == 5


def test_feature_table_stays_chronological() -> None:
    energy, weather = _toy_frames()
    table = to_feature_table(
        drop_incomplete_rows(add_features(join_energy_and_weather(energy, weather)))
    )
    stamps = pd.to_datetime(table["utc_timestamp"], utc=True)
    assert stamps.is_monotonic_increasing
    assert TARGET_COLUMN in table.columns
    for column in FEATURE_COLUMNS:
        assert column in table.columns


def test_incomplete_history_is_dropped() -> None:
    energy, weather = _toy_frames()
    featured = add_features(join_energy_and_weather(energy, weather))
    complete = drop_incomplete_rows(featured)
    assert len(complete) == 200 - 168
    assert complete[FEATURE_COLUMNS].isna().sum().sum() == 0
