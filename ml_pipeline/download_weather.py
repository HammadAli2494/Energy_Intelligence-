"""Download hourly Madrid weather from Open-Meteo and cache it locally.

Usage (from the project root):

    python ml_pipeline/download_weather.py
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.weather_service import fetch_historical_hourly  # noqa: E402

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT = ROOT / "data" / "processed" / "madrid_hourly_weather.csv"
DEFAULT_START = date(2015, 1, 1)
DEFAULT_END = date(2020, 9, 30)


def main() -> int:
    parser = argparse.ArgumentParser(description="Cache hourly Open-Meteo weather for Madrid.")
    parser.add_argument("--start", type=date.fromisoformat, default=DEFAULT_START)
    parser.add_argument("--end", type=date.fromisoformat, default=DEFAULT_END)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Download again even if the cache file already exists.",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    weather = fetch_historical_hourly(
        args.start,
        args.end,
        cache_path=args.output,
        force=args.force,
    )
    logger.info("Hours: %s", f"{len(weather):,}")
    logger.info("UTC range: %s -> %s", weather["utc_timestamp"].min(), weather["utc_timestamp"].max())
    logger.info("Missing temperature: %s", int(weather["temperature_c"].isna().sum()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
