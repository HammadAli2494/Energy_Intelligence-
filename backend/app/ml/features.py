"""Create one-hour-ahead forecasting features.

Each row is the hour we want to predict (time t):

- load_mw is the target (unknown at forecast time, used only in training)
- lags and rolling means use load before t only
- calendar features use the clock at t (known in advance)
- weather columns are the last known hour (t-1), not observed weather at t

This module does not train a model.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from app.ml.preprocessing import LOCAL_TZ

TARGET_COLUMN = "load_mw"
FEATURE_COLUMNS = [
    "hour",
    "day_of_week",
    "month",
    "is_weekend",
    "lag_1",
    "lag_24",
    "lag_168",
    "rolling_mean_24",
    "rolling_mean_168",
    "temperature_c",
    "relative_humidity_pct",
    "wind_speed_kmh",
]
METADATA = {
    "target": TARGET_COLUMN,
    "features": FEATURE_COLUMNS,
    "timezone_for_calendar": LOCAL_TZ,
    "weather_timing": "lag_1 — last known Madrid hour, not observed weather at t",
    "lag_1": "load at t-1",
    "lag_24": "load at t-24 (same hour yesterday)",
    "lag_168": "load at t-168 (same hour last week)",
    "rolling_mean_24": "mean load from t-24 through t-1",
    "rolling_mean_168": "mean load from t-168 through t-1",
}


def load_processed_energy(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["utc"] = pd.to_datetime(frame["utc_timestamp"], utc=True)
    frame["local"] = frame["utc"].dt.tz_convert(LOCAL_TZ)
    frame["load_mw"] = pd.to_numeric(frame["load_mw"], errors="coerce")
    return frame.sort_values("utc").drop_duplicates(subset=["utc"], keep="first")


def load_processed_weather(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    frame["utc"] = pd.to_datetime(frame["utc_timestamp"], utc=True)
    return frame.sort_values("utc").drop_duplicates(subset=["utc"], keep="first")


def join_energy_and_weather(energy: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    weather_cols = ["utc", "temperature_c", "relative_humidity_pct", "wind_speed_kmh"]
    missing = set(weather_cols).difference(weather.columns)
    if missing:
        raise ValueError(f"Weather file is missing columns: {sorted(missing)}")

    merged = energy.merge(weather[weather_cols], on="utc", how="left")
    return merged.sort_values("utc").reset_index(drop=True)


def add_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Add calendar, lag, rolling, and last-known weather columns."""
    out = frame.copy()
    local = out["local"]
    out["hour"] = local.dt.hour.astype("int16")
    out["day_of_week"] = local.dt.dayofweek.astype("int8")
    out["month"] = local.dt.month.astype("int8")
    out["is_weekend"] = (out["day_of_week"] >= 5).astype("int8")

    load = out["load_mw"]
    previous_load = load.shift(1)
    out["lag_1"] = previous_load
    out["lag_24"] = load.shift(24)
    out["lag_168"] = load.shift(168)
    out["rolling_mean_24"] = previous_load.rolling(window=24, min_periods=24).mean()
    out["rolling_mean_168"] = previous_load.rolling(window=168, min_periods=168).mean()

    for column in ("temperature_c", "relative_humidity_pct", "wind_speed_kmh"):
        if column in out.columns:
            out[column] = out[column].shift(1)
    return out


def drop_incomplete_rows(frame: pd.DataFrame) -> pd.DataFrame:
    required = [TARGET_COLUMN, *FEATURE_COLUMNS]
    return frame.dropna(subset=required).reset_index(drop=True)


def to_feature_table(frame: pd.DataFrame) -> pd.DataFrame:
    table = pd.DataFrame(
        {
            "utc_timestamp": frame["utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "local_timestamp": frame["local"].dt.strftime("%Y-%m-%dT%H:%M:%S%z"),
            TARGET_COLUMN: frame[TARGET_COLUMN],
        }
    )
    for column in FEATURE_COLUMNS:
        table[column] = frame[column]
    return table.reset_index(drop=True)


def build_feature_table(
    energy_path: str | Path,
    weather_path: str | Path,
) -> pd.DataFrame:
    energy = load_processed_energy(energy_path)
    weather = load_processed_weather(weather_path)
    merged = join_energy_and_weather(energy, weather)
    featured = add_features(merged)
    complete = drop_incomplete_rows(featured)
    return to_feature_table(complete)


def save_feature_table(table: pd.DataFrame, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(output_path, index=False)

    metadata_path = output_path.with_name("feature_list.json")
    metadata_path.write_text(json.dumps(METADATA, indent=2), encoding="utf-8")
    return output_path


def build_inference_row(
    energy: pd.DataFrame,
    weather: pd.DataFrame,
    target_utc: pd.Timestamp,
) -> pd.DataFrame:
    """Features for predicting load at target_utc using only earlier hours."""
    target = pd.Timestamp(target_utc)
    if target.tzinfo is None:
        target = target.tz_localize("UTC")
    else:
        target = target.tz_convert("UTC")

    loads = energy.set_index("utc")["load_mw"].sort_index()
    weather_idx = weather.set_index("utc").sort_index()

    lag_hours = {
        "lag_1": 1,
        "lag_24": 24,
        "lag_168": 168,
    }
    values: dict[str, float] = {}
    for name, hours_back in lag_hours.items():
        stamp = target - pd.Timedelta(hours=hours_back)
        if stamp not in loads.index or pd.isna(loads.loc[stamp]):
            raise ValueError(f"Insufficient history for {name} at {target.isoformat()}.")
        values[name] = float(loads.loc[stamp])

    window_24 = loads.loc[target - pd.Timedelta(hours=24) : target - pd.Timedelta(hours=1)]
    window_168 = loads.loc[target - pd.Timedelta(hours=168) : target - pd.Timedelta(hours=1)]
    if window_24.isna().any() or len(window_24) < 24:
        raise ValueError("Insufficient history for rolling_mean_24.")
    if window_168.isna().any() or len(window_168) < 168:
        raise ValueError("Insufficient history for rolling_mean_168.")

    weather_stamp = target - pd.Timedelta(hours=1)
    if weather_stamp not in weather_idx.index:
        raise ValueError("No last-known weather for this hour.")
    weather_row = weather_idx.loc[weather_stamp]
    if pd.isna(weather_row[["temperature_c", "relative_humidity_pct", "wind_speed_kmh"]]).any():
        raise ValueError("Last-known weather values are missing.")

    local = target.tz_convert(LOCAL_TZ)
    row = {
        "hour": int(local.hour),
        "day_of_week": int(local.dayofweek),
        "month": int(local.month),
        "is_weekend": int(local.dayofweek >= 5),
        "lag_1": values["lag_1"],
        "lag_24": values["lag_24"],
        "lag_168": values["lag_168"],
        "rolling_mean_24": float(window_24.mean()),
        "rolling_mean_168": float(window_168.mean()),
        "temperature_c": float(weather_row["temperature_c"]),
        "relative_humidity_pct": float(weather_row["relative_humidity_pct"]),
        "wind_speed_kmh": float(weather_row["wind_speed_kmh"]),
    }
    return pd.DataFrame([row])
