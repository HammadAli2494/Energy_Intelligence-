# Data

Put datasets here. Do not commit large raw files (`data/raw/*.csv` is gitignored).

| Folder | Use |
| --- | --- |
| `raw/` | Original files produced by our download script |
| `processed/` | Cleaned hourly load from `ml_pipeline/prepare_data.py` |

## Chosen dataset (Phase 2)

**Spanish hourly electricity load**, extracted from Open Power System Data (OPSD) time series 2020-10-06. The values originally come from the ENTSO-E Transparency Platform.

| Item | Value |
| --- | --- |
| Local file | `data/raw/spain_hourly_load.csv` |
| Columns | `utc_timestamp`, `cet_cest_timestamp`, `load_mw` |
| `load_mw` | National electricity demand in Spain, megawatts |
| Rows | 50,401 hours (2015–Sep 2020), 23 missing load values |
| Typical demand | about 16.6–41.0 GW (mean ≈ 28.4 GW) |
| Weather | Cached separately in `madrid_hourly_weather.csv` (Madrid, Open-Meteo). |

Full problem statement, target definition, and leakage notes: [docs/problem_definition.md](../docs/problem_definition.md)

## Download

From the project root:

```powershell
cd "C:\Users\Hammad Ali\Energy Intelligence"
.\.venv\Scripts\python.exe scripts\download_dataset.py
```

The script streams a large European CSV and writes only Spain’s load columns. Re-run with `--force` if you need a fresh copy.

```powershell
.\.venv\Scripts\python.exe scripts\download_dataset.py --force
```

## Processed file (Phase 4)

Build it after the raw CSV exists:

```powershell
.\.venv\Scripts\python.exe ml_pipeline\prepare_data.py
```

| Item | Value |
| --- | --- |
| File | `data/processed/spain_hourly_load.csv` |
| Extra columns | `load_was_missing`, `load_was_interpolated` |
| Interpolation | Interior gaps of 1–3 hours only |
| Not done | No lag features, no weather, no clipped peaks |

On the current extract: 6 hours interpolated, 17 still missing (series start/end, a long 2 Jan 2015 gap, and 1 May 2015).

## Weather cache (Phase 5)

Madrid hourly weather from Open-Meteo, aligned to UTC:

```powershell
.\.venv\Scripts\python.exe ml_pipeline\download_weather.py
```

| Item | Value |
| --- | --- |
| File | `data/processed/madrid_hourly_weather.csv` |
| Columns | `utc_timestamp`, `temperature_c`, `relative_humidity_pct`, `wind_speed_kmh` |
| Coverage | 2015-01-01 00:00 UTC → 2020-09-30 23:00 UTC (50,400 hours) |
| Location | Madrid 40.4168 N, 3.7038 W (representative, not all of Spain) |

The energy series has one extra hour at 2014-12-31 23:00 UTC, so that row will not have weather until it is dropped or left missing in Phase 6. Re-run with `--force` only if you need a fresh download.

## Feature table (Phase 6)

```powershell
.\.venv\Scripts\python.exe ml_pipeline\build_features.py
```

| Item | Value |
| --- | --- |
| File | `data/processed/spain_hourly_features.csv` |
| Rows (current build) | 50,014 complete hours |
| Target | `load_mw` at hour t |
| Weather used | Last known hour (t−1), not observed weather at t |

Incomplete history (first week, remaining load gaps) is dropped so lag_168 is always defined.
