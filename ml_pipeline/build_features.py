"""Build the one-hour-ahead feature table.

Usage (from the project root):

    python ml_pipeline/build_features.py
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.ml.features import build_feature_table, save_feature_table  # noqa: E402

logger = logging.getLogger(__name__)

DEFAULT_ENERGY = ROOT / "data" / "processed" / "spain_hourly_load.csv"
DEFAULT_WEATHER = ROOT / "data" / "processed" / "madrid_hourly_weather.csv"
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "spain_hourly_features.csv"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create leakage-safe forecast features.")
    parser.add_argument("--energy", type=Path, default=DEFAULT_ENERGY)
    parser.add_argument("--weather", type=Path, default=DEFAULT_WEATHER)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    if not args.energy.exists():
        logger.error("Processed energy not found. Run: python ml_pipeline/prepare_data.py")
        return 1
    if not args.weather.exists():
        logger.error("Weather cache not found. Run: python ml_pipeline/download_weather.py")
        return 1
    if args.output.exists() and not args.force:
        logger.info("Feature file already exists: %s", args.output)
        logger.info("Pass --force to build it again.")
        return 0

    table = build_feature_table(args.energy, args.weather)
    save_feature_table(table, args.output)
    logger.info("Wrote %s", args.output)
    logger.info("Rows: %s", f"{len(table):,}")
    logger.info("UTC range: %s -> %s", table["utc_timestamp"].iloc[0], table["utc_timestamp"].iloc[-1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
