import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from download_dataset import extract_spain_row, parse_load_mw


def test_extract_spain_row_renames_load_column() -> None:
    source = {
        "utc_timestamp": "2018-06-15T14:00:00Z",
        "cet_cest_timestamp": "2018-06-15T16:00:00+0200",
        "ES_load_actual_entsoe_transparency": "28400.5",
        "DE_load_actual_entsoe_transparency": "99999",
    }

    row = extract_spain_row(source)

    assert row["utc_timestamp"] == "2018-06-15T14:00:00Z"
    assert row["load_mw"] == "28400.5"
    assert "DE_load_actual_entsoe_transparency" not in row


def test_parse_load_mw_handles_missing_and_numeric_values() -> None:
    assert parse_load_mw("") is None
    assert parse_load_mw("22150.0") == 22150.0
