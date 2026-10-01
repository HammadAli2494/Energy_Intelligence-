from __future__ import annotations

from pathlib import Path

import pandas as pd

from app.ml.preprocessing import (
    interpolate_short_gaps,
    prepare_energy_series,
    to_processed_table,
)


def _raw_csv(tmp_path: Path, rows: list[tuple[str, float | None]]) -> Path:
    path = tmp_path / "raw.csv"
    frame = pd.DataFrame(rows, columns=["utc_timestamp", "load_mw"])
    frame["cet_cest_timestamp"] = ""
    frame.to_csv(path, index=False)
    return path


def test_sorts_and_drops_duplicate_timestamps(tmp_path: Path) -> None:
    path = _raw_csv(
        tmp_path,
        [
            ("2018-01-01T02:00:00Z", 20000),
            ("2018-01-01T00:00:00Z", 18000),
            ("2018-01-01T00:00:00Z", 99999),
            ("2018-01-01T01:00:00Z", 19000),
        ],
    )

    result = prepare_energy_series(path)

    assert list(result.index) == list(pd.date_range(
        "2018-01-01T00:00:00Z", periods=3, freq="h", tz="UTC"
    ))
    assert result["load_mw"].iloc[0] == 18000
    assert result["load_mw"].is_monotonic_increasing


def test_short_gap_is_interpolated(tmp_path: Path) -> None:
    path = _raw_csv(
        tmp_path,
        [
            ("2018-06-01T00:00:00Z", 100.0),
            ("2018-06-01T01:00:00Z", None),
            ("2018-06-01T02:00:00Z", None),
            ("2018-06-01T03:00:00Z", 130.0),
        ],
    )

    result = prepare_energy_series(path)

    assert result["load_mw"].tolist() == [100.0, 110.0, 120.0, 130.0]
    assert result["load_was_interpolated"].tolist() == [False, True, True, False]


def test_long_gap_is_not_partially_filled() -> None:
    index = pd.date_range("2018-06-01", periods=6, freq="h", tz="UTC")
    load = pd.Series([100.0, None, None, None, None, 200.0], index=index)

    filled = interpolate_short_gaps(load, max_hours=3)

    assert filled.iloc[0] == 100.0
    assert filled.iloc[-1] == 200.0
    assert filled.iloc[1:-1].isna().all()


def test_leading_and_trailing_gaps_stay_missing() -> None:
    index = pd.date_range("2018-06-01", periods=5, freq="h", tz="UTC")
    load = pd.Series([None, 100.0, 110.0, 120.0, None], index=index)

    filled = interpolate_short_gaps(load, max_hours=3)

    assert pd.isna(filled.iloc[0])
    assert pd.isna(filled.iloc[-1])
    assert filled.iloc[1:-1].tolist() == [100.0, 110.0, 120.0]


def test_zero_load_is_treated_as_missing(tmp_path: Path) -> None:
    path = _raw_csv(
        tmp_path,
        [
            ("2018-06-01T00:00:00Z", 100.0),
            ("2018-06-01T01:00:00Z", 0.0),
            ("2018-06-01T02:00:00Z", 120.0),
        ],
    )

    result = prepare_energy_series(path)

    assert result["load_mw"].iloc[1] == 110.0
    assert bool(result["load_was_missing"].iloc[1])
    assert bool(result["load_was_interpolated"].iloc[1])


def test_high_demand_is_not_clipped(tmp_path: Path) -> None:
    path = _raw_csv(
        tmp_path,
        [
            ("2017-01-18T18:00:00Z", 40000.0),
            ("2017-01-18T19:00:00Z", 41015.0),
            ("2017-01-18T20:00:00Z", 40900.0),
        ],
    )

    result = prepare_energy_series(path)

    assert result["load_mw"].max() == 41015.0


def test_processed_table_does_not_shuffle_time(tmp_path: Path) -> None:
    path = _raw_csv(
        tmp_path,
        [
            ("2018-01-01T03:00:00Z", 21000),
            ("2018-01-01T01:00:00Z", 19000),
            ("2018-01-01T02:00:00Z", 20000),
        ],
    )

    table = to_processed_table(prepare_energy_series(path))
    stamps = pd.to_datetime(table["utc_timestamp"], utc=True)

    assert stamps.is_monotonic_increasing
    assert list(table.columns) == [
        "utc_timestamp",
        "local_timestamp",
        "load_mw",
        "load_was_missing",
        "load_was_interpolated",
    ]
