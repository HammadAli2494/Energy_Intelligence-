"""Create data/processed/spain_hourly_load.csv from the raw OPSD extract.

Usage (from the project root):

    python ml_pipeline/prepare_data.py
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.ml.preprocessing import (  # noqa: E402
    prepare_energy_series,
    save_processed_energy,
)

logger = logging.getLogger(__name__)

DEFAULT_RAW = ROOT / "data" / "raw" / "spain_hourly_load.csv"
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "spain_hourly_load.csv"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Clean Spanish hourly load and write a processed CSV."
    )
    parser.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the processed file if it already exists.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(message)s",
    )

    if not args.raw.exists():
        logger.error("Raw file not found. Run: python scripts/download_dataset.py")
        return 1

    if args.output.exists() and not args.force:
        logger.info("Processed file already exists: %s", args.output)
        logger.info("Pass --force to build it again.")
        return 0

    series = prepare_energy_series(args.raw)
    save_processed_energy(series, args.output)

    n_rows = len(series)
    n_missing = int(series["load_mw"].isna().sum())
    n_interpolated = int(series["load_was_interpolated"].sum())
    logger.info("Wrote %s", args.output)
    logger.info("Hours: %s", f"{n_rows:,}")
    logger.info("Interpolated short gaps: %s", n_interpolated)
    logger.info("Still missing load_mw: %s", n_missing)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
