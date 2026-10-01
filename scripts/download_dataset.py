"""Download Spanish hourly electricity load from Open Power System Data.

The full OPSD file covers many European countries (~124 MB). This script
streams that file and keeps only the Spain load columns we need.
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
import urllib.request
from pathlib import Path

OPSD_URL = (
    "https://data.open-power-system-data.org/time_series/2020-10-06/"
    "time_series_60min_singleindex.csv"
)
SOURCE_LOAD_COLUMN = "ES_load_actual_entsoe_transparency"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "data" / "raw" / "spain_hourly_load.csv"
OUTPUT_COLUMNS = ["utc_timestamp", "cet_cest_timestamp", "load_mw"]


def extract_spain_row(source_row: dict[str, str]) -> dict[str, str]:
    """Keep timestamps and rename the Spain load column."""
    return {
        "utc_timestamp": source_row.get("utc_timestamp", "").strip(),
        "cet_cest_timestamp": source_row.get("cet_cest_timestamp", "").strip(),
        "load_mw": source_row.get(SOURCE_LOAD_COLUMN, "").strip(),
    }


def parse_load_mw(value: str) -> float | None:
    if value == "":
        return None
    return float(value)


def download_spain_load(force: bool = False) -> Path:
    if OUTPUT_PATH.exists() and not force:
        print(f"File already exists: {OUTPUT_PATH}")
        print("Pass --force to download again.")
        return OUTPUT_PATH

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        OPSD_URL,
        headers={"User-Agent": "EnergyIntelligence/0.1 (educational portfolio)"},
    )

    row_count = 0
    missing_load = 0
    min_load = None
    max_load = None
    load_sum = 0.0
    load_count = 0
    first_timestamp = ""
    last_timestamp = ""

    print(f"Downloading OPSD hourly time series from:\n  {OPSD_URL}")
    print("Streaming Spain load columns only. This can take a few minutes.")

    with urllib.request.urlopen(request, timeout=120) as response:
        text_stream = io.TextIOWrapper(response, encoding="utf-8", newline="")
        reader = csv.DictReader(text_stream)

        with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=OUTPUT_COLUMNS)
            writer.writeheader()

            for source_row in reader:
                row = extract_spain_row(source_row)
                if not row["utc_timestamp"]:
                    continue

                writer.writerow(row)
                row_count += 1
                last_timestamp = row["utc_timestamp"]
                if not first_timestamp:
                    first_timestamp = row["utc_timestamp"]

                load_value = parse_load_mw(row["load_mw"])
                if load_value is None:
                    missing_load += 1
                else:
                    load_count += 1
                    load_sum += load_value
                    min_load = load_value if min_load is None else min(min_load, load_value)
                    max_load = load_value if max_load is None else max(max_load, load_value)

                if row_count % 10000 == 0:
                    print(f"  processed {row_count:,} hourly rows...")

    print()
    print(f"Saved: {OUTPUT_PATH}")
    print(f"Rows: {row_count:,}")
    print(f"UTC range: {first_timestamp}  ->  {last_timestamp}")
    print(f"Missing load_mw values: {missing_load:,}")
    if load_count:
        mean_load = load_sum / load_count
        print(f"load_mw with values: {load_count:,}")
        print(f"Min / mean / max MW: {min_load:.1f} / {mean_load:.1f} / {max_load:.1f}")

    return OUTPUT_PATH


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download Spanish hourly electricity load (OPSD / ENTSO-E)."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Download again even if data/raw/spain_hourly_load.csv already exists.",
    )
    args = parser.parse_args()

    try:
        download_spain_load(force=args.force)
    except Exception as exc:
        print(f"Download failed: {exc.__class__.__name__}", file=sys.stderr)
        print("Check your internet connection and try again.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
