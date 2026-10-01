"""Time-series split. Rows stay in chronological order; nothing is shuffled."""

from __future__ import annotations

import pandas as pd

TRAIN_END = pd.Timestamp("2019-01-01", tz="UTC")
VALID_END = pd.Timestamp("2020-01-01", tz="UTC")


def time_split(
    frame: pd.DataFrame,
    timestamp_col: str = "utc_timestamp",
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Train: through 2018. Validation: 2019. Test: 2020 (COVID stress year)."""
    ordered = frame.copy()
    ordered["_utc"] = pd.to_datetime(ordered[timestamp_col], utc=True)
    ordered = ordered.sort_values("_utc")

    train = ordered.loc[ordered["_utc"] < TRAIN_END].drop(columns="_utc")
    valid = ordered.loc[
        (ordered["_utc"] >= TRAIN_END) & (ordered["_utc"] < VALID_END)
    ].drop(columns="_utc")
    test = ordered.loc[ordered["_utc"] >= VALID_END].drop(columns="_utc")

    if train.empty or valid.empty or test.empty:
        raise ValueError("A time split is empty. Check the feature-table date range.")

    return (
        train.reset_index(drop=True),
        valid.reset_index(drop=True),
        test.reset_index(drop=True),
    )
