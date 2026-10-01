# Problem Definition

**Current phase:** Application complete. The API serves the saved model; residual anomalies and the React dashboard read those real outputs.

## What are we building?

A **one-hour-ahead electricity demand forecast** for Spain, plus later flags for unusually large forecast errors (anomaly detection).

In plain language: at 14:00, predict how many megawatts Spain will consume at 15:00.

## Why this problem?

Electricity is generated and used at the same time. Grid operators, retailers, and analysts care about the next hours of demand because it affects generation scheduling and imbalance costs.

This project does **not** make operational dispatch decisions. Forecasts are estimates for an educational / portfolio application.

## Dataset choice

| Item | Choice |
| --- | --- |
| Source | [Open Power System Data — Time series 2020-10-06](https://data.open-power-system-data.org/time_series/2020-10-06/) |
| Original publisher | ENTSO-E Transparency Platform |
| File we create | `data/raw/spain_hourly_load.csv` |
| Geography | Spain (national total load) |
| Resolution | 1 hour |
| Period | 2015 through mid-2020 (as published in this OPSD version) |
| License | OPSD data package, typically CC-BY-4.0; cite OPSD and ENTSO-E |

### Why this dataset (not a random Kaggle file)

1. **Hourly national load in MW** matches a demand-forecasting product.
2. **Public and citable**, with a documented processing pipeline.
3. **Known geography**, so Phase 5 can attach Open-Meteo weather for Spain.
4. **Direct HTTP download** — no Kaggle account or API token.
5. It is less overused in tutorials than the PJM East (`PJME`) Kaggle CSV.

### Alternatives considered

| Dataset | Why not for this project |
| --- | --- |
| PJM East hourly (Kaggle) | Easy, but used in many identical GitHub projects; US weather join is less clean. |
| UCI household power | One home, minute-level. Too small a scale for a “demand platform”. |
| Spain Kaggle energy + weather | Weather already included, but usually needs a Kaggle token. We will fetch weather ourselves from Open-Meteo. |

## Raw columns

The full OPSD CSV has ~300 country columns. Our script keeps three:

| Column | Meaning | How we use it |
| --- | --- | --- |
| `utc_timestamp` | Hour start in UTC | Canonical time index. Safer around daylight-saving changes. |
| `cet_cest_timestamp` | Same hour in Spain local time (CET/CEST) | Local **hour of day** and weekday features. People and industry follow local clocks, not UTC. |
| `load_mw` | Spain total electricity load in megawatts (`ES_load_actual_entsoe_transparency`) | **Target source.** This is actual consumption, not a forecast. |

OPSD also publishes `ES_load_forecast_entsoe_transparency` (an official day-ahead load forecast) and wind/solar **generation**. We do **not** store those in our raw file.

- The official forecast is useful later as a **comparison**, not as a feature. Using it as an input would mean we are not building an independent model.
- Wind/solar generation is **supply**, not demand. It should not be treated as a driver of consumption.

## ML target

**Target name:** `load_mw` at the **next hour**.

If the current row is hour \(t\):

- Inputs may use information available at time \(t\) (and earlier).
- The label is `load_mw` at \(t + 1\) hour.

Example:

| utc_timestamp | load_mw at t | target (load at t+1) |
| --- | ---: | ---: |
| 2018-06-15 14:00 | 28,400 | 28,900 |
| 2018-06-15 15:00 | 28,900 | … |

The model is a **one-step-ahead hourly regressor**, not a 24-hour sequence model. That keeps training and the later FastAPI endpoint simple.

## Inputs actually used

Calendar, lag, rolling, and last-known Madrid weather features are implemented in `backend/app/ml/features.py`. Weather files come from Open-Meteo (Madrid).

| Feature | Expected signal | Leakage risk |
| --- | --- | --- |
| `hour` (local) | Overnight low, morning ramp, evening peak | Low, if taken from the timestamp of \(t\) or \(t+1\) consistently. For predicting \(t+1\), the hour of \(t+1\) is known in advance. |
| `day_of_week` | Weekdays vs Sunday | Low. Calendar is known ahead of time. |
| `month` | Heating / cooling seasons | Low. |
| `is_weekend` | Lower industrial/office load | Low. |
| `lag_1` | Demand changes slowly hour to hour | Must be load at \(t\), never \(t+1\). |
| `lag_24` | Same hour yesterday | Must be load at \(t-23\) relative to target \(t+1\), i.e. yesterday’s same hour. |
| `lag_168` | Same hour last week | Same idea; weekly seasonality. |
| `rolling_mean_24` | Recent level of demand | Window must end at \(t\), not include the target. |
| `rolling_mean_168` | Typical week level | Same. |
| temperature, humidity, wind (Open-Meteo, Madrid) | Heating and air-conditioning | Do not use future **observed** weather unless we treat it as a “perfect weather forecast” assumption and say so. |

### Weather location

Spain’s load is **national**. Open-Meteo needs coordinates. We will use **Madrid** (approx. 40.42 N, 3.70 W) as a single representative weather point.

That is a simplification: coastal and inland temperatures differ. It is acceptable for this project if we state it as a limitation.

## What this application still does not do

- No live ENTSO-E feed (the extract ends 30 September 2020)
- No operational dispatch recommendations
- No equipment-failure classifier — residuals only

## What could go wrong later

- **Missing hours** in the load series create gaps in lags.
- **Daylight saving** can duplicate or skip local hours; UTC as the index avoids most of that.
- **National load + Madrid weather** will miss regional heat waves.
- **Shuffling rows** would leak the future into training. Time-series split only.
- **Using the target column inside a feature** (for example rolling mean that includes \(t+1\)) would inflate accuracy.

## Citation

Open Power System Data. 2020. *Data Package Time series*. Version 2020-10-06. https://doi.org/10.25832/time_series/2020-10-06

Primary series: ENTSO-E Transparency Platform, Spain total load.

## Observed file profile (after download)

These numbers come from `scripts/download_dataset.py` on the extracted CSV. They are **descriptive**, not model scores.

| Item | Value |
| --- | --- |
| File | `data/raw/spain_hourly_load.csv` |
| Rows | 50,401 hours |
| UTC range | 2014-12-31 23:00 → 2020-09-30 23:00 |
| Missing `load_mw` | 23 rows (including the first hours of 2015 and the last hour in the file) |
| Demand when present | min 16,575 MW · mean 28,442 MW · max 41,015 MW |

The first rows look like this (empty `load_mw` means “not published yet” for that hour):

```text
utc_timestamp,cet_cest_timestamp,load_mw
2014-12-31T23:00:00Z,2015-01-01T00:00:00+0100,
2015-01-01T00:00:00Z,2015-01-01T01:00:00+0100,
2015-01-01T01:00:00Z,2015-01-01T02:00:00+0100,22734.0000
```

2020 includes COVID-related demand changes in Spain. A test set that is only 2020 may not represent earlier years. That is a data issue, not something to “fix” by ignoring it. Test MAE is therefore expected to be worse than 2019 validation MAE.
