"""Clean the Spanish hourly electricity load series.

Rules come from notebooks/01_data_understanding.ipynb (Phase 3).

This module does not create lag features, does not join weather,
and does not train a model.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

LOCAL_TZ = "Europe/Madrid"
MAX_INTERPOLATE_HOURS = 3
PROCESSED_COLUMNS = [
    "utc_timestamp",
    "local_timestamp",
    "load_mw",
    "load_was_missing",
    "load_was_interpolated",
]


def load_raw_energy(path: str | Path) -> pd.DataFrame:
    """Read the Phase 2 CSV. Missing cells become NaN, not zero."""
    frame = pd.read_csv(path)
    required = {"utc_timestamp", "load_mw"}
    missing_cols = required.difference(frame.columns)
    if missing_cols:
        raise ValueError(f"Raw file is missing columns: {sorted(missing_cols)}")
    return frame


def parse_timestamps(frame: pd.DataFrame) -> pd.DataFrame:
    """Build a unique, sorted UTC hourly index and a Spain-local clock column."""
    parsed = frame.copy()
    parsed["utc"] = pd.to_datetime(parsed["utc_timestamp"], utc=True)
    parsed = parsed.dropna(subset=["utc"])
    parsed = parsed.drop_duplicates(subset=["utc"], keep="first")
    parsed = parsed.sort_values("utc")
    parsed = parsed.set_index("utc")
    parsed = parsed.loc[~parsed.index.duplicated(keep="first")]
    parsed = parsed.asfreq("h")
    parsed["local"] = parsed.index.tz_convert(LOCAL_TZ)
    return parsed


def invalidate_nonpositive_load(frame: pd.DataFrame) -> pd.DataFrame:
    """Zero or negative MW is not valid demand. Keep the hour; clear the value."""
    cleaned = frame.copy()
    load = pd.to_numeric(cleaned["load_mw"], errors="coerce")
    invalid = load.notna() & (load <= 0)
    load = load.mask(invalid)
    cleaned["load_mw"] = load
    return cleaned


def interpolate_short_gaps(
    load: pd.Series,
    max_hours: int = MAX_INTERPOLATE_HOURS,
) -> pd.Series:
    """Fill only interior missing runs whose length is at most max_hours.

    pandas interpolate(limit=3) would fill the first three hours of a
    six-hour gap. We do not want that. A long gap stays entirely missing.

    Time interpolation uses both neighbouring observed values. That is
    reconstruction of a historical measurement, not a forecast feature.
    Leading or trailing gaps have no two neighbours and stay missing.
    """
    if load.empty or not load.isna().any():
        return load.copy()

    missing = load.isna()
    run_id = missing.ne(missing.shift(fill_value=False)).cumsum()
    reconstructed = load.interpolate(method="time")
    result = load.copy()
    hour = pd.Timedelta(hours=1)

    for _, run in load.groupby(run_id):
        if not bool(run.isna().all()):
            continue
        if not 1 <= len(run) <= max_hours:
            continue

        previous_stamp = run.index[0] - hour
        next_stamp = run.index[-1] + hour
        has_previous = previous_stamp in load.index and pd.notna(load.loc[previous_stamp])
        has_next = next_stamp in load.index and pd.notna(load.loc[next_stamp])
        if has_previous and has_next:
            result.loc[run.index] = reconstructed.loc[run.index]

    return result


def prepare_energy_series(
    raw_path: str | Path,
    max_interpolate_hours: int = MAX_INTERPOLATE_HOURS,
) -> pd.DataFrame:
    """Run the full cleaning pipeline and return a chronological frame."""
    raw = load_raw_energy(raw_path)
    indexed = parse_timestamps(raw)
    indexed = invalidate_nonpositive_load(indexed)

    was_missing = indexed["load_mw"].isna()
    indexed["load_mw"] = interpolate_short_gaps(
        indexed["load_mw"],
        max_hours=max_interpolate_hours,
    )
    indexed["load_was_missing"] = was_missing
    indexed["load_was_interpolated"] = was_missing & indexed["load_mw"].notna()

    # Peaks are left unchanged on purpose. Phase 3 found no false outliers.
    return indexed[["local", "load_mw", "load_was_missing", "load_was_interpolated"]]


def to_processed_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert the indexed series into a flat table for CSV output."""
    table = pd.DataFrame(
        {
            "utc_timestamp": frame.index.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "local_timestamp": frame["local"].dt.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "load_mw": frame["load_mw"],
            "load_was_missing": frame["load_was_missing"],
            "load_was_interpolated": frame["load_was_interpolated"],
        }
    )
    return table.reset_index(drop=True)


def save_processed_energy(frame: pd.DataFrame, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    table = to_processed_table(frame)
    table.to_csv(output_path, index=False)
    return output_path
