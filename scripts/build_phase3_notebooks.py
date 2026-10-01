"""Create Phase 3 Jupyter notebooks. Run once from the project root."""

from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"


def md(text: str):
    return nbf.v4.new_markdown_cell(text.strip())


def code(text: str):
    return nbf.v4.new_code_cell(text.strip())


def write_notebook(name: str, cells: list) -> Path:
    nb = nbf.v4.new_notebook()
    nb["cells"] = cells
    nb["metadata"] = {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {"name": "python", "pygments_lexer": "ipython3"},
    }
    path = NOTEBOOKS / name
    path.write_text(nbf.writes(nb), encoding="utf-8")
    return path


SETUP = """
%matplotlib inline

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

pd.set_option("display.max_rows", 20)
plt.rcParams.update(
    {
        "figure.figsize": (10, 4.2),
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
    }
)
BRAND = "#0f766e"


def project_root() -> Path:
    here = Path.cwd()
    for candidate in (here, here.parent):
        if (candidate / "data" / "raw" / "spain_hourly_load.csv").exists():
            return candidate
    raise FileNotFoundError(
        "spain_hourly_load.csv not found. From the project root run: "
        "python scripts/download_dataset.py"
    )


ROOT = project_root()
DATA_PATH = ROOT / "data" / "raw" / "spain_hourly_load.csv"
print(f"Using {DATA_PATH}")
"""


def notebook_01() -> None:
    cells = [
        md(
            """
# 01 — Data understanding and cleaning notes

**Phase 3 of Energy Intelligence.** No model is trained here.

## What are we doing?

We inspect the raw Spanish hourly load file before any feature engineering.

## Why?

Charts and models are misleading if timestamps are wrong, hours are missing, or “outliers” are actually winter peaks. Cleaning rules should come from this inspection, not from habit.
"""
        ),
        md("## Setup"),
        code(SETUP),
        md(
            """
## Load the raw file

The CSV has three columns created in Phase 2. `load_mw` is national electricity demand in Spain.
"""
        ),
        code(
            """
raw = pd.read_csv(DATA_PATH)
raw.head()
"""
        ),
        code(
            """
print("rows, columns:", raw.shape)
print()
print(raw.dtypes)
print()
print("null counts:")
print(raw.isna().sum())
"""
        ),
        md(
            """
### What this means

Pandas already read `load_mw` as a number. Empty cells became `NaN` (not zero). Treating missing demand as 0 MW would be a serious error: it would look like the grid shut off.
"""
        ),
        md("## Parse timestamps"),
        code(
            """
df = raw.copy()
df["utc"] = pd.to_datetime(df["utc_timestamp"], utc=True)
# Local clock in Spain. Demand follows this, not UTC.
df["local"] = df["utc"].dt.tz_convert("Europe/Madrid")
df = df.sort_values("utc").reset_index(drop=True)
df[["utc_timestamp", "cet_cest_timestamp", "utc", "local", "load_mw"]].head(4)
"""
        ),
        code(
            """
print("UTC range:", df["utc"].min(), "->", df["utc"].max())
print("Duplicate UTC timestamps:", int(df["utc"].duplicated().sum()))
print("Already sorted by UTC:", bool(df["utc"].is_monotonic_increasing))
"""
        ),
        md(
            """
## Is the clock regular?

For hourly forecasting we need one row per hour. Gaps would break lag features (`lag_1`, `lag_24`).
"""
        ),
        code(
            """
gaps = df["utc"].diff().dropna()
print(gaps.value_counts())
print()
print("Gaps longer than 1 hour:", int((gaps > pd.Timedelta(hours=1)).sum()))
print("Steps shorter than 1 hour:", int((gaps < pd.Timedelta(hours=1)).sum()))
"""
        ),
        md(
            """
### What this means

The UTC index is a complete hourly grid: no duplicates, no missing hours, no extra half-hours. Daylight-saving changes in Spain do **not** punch holes in UTC. That is why we keep UTC as the index and convert to `Europe/Madrid` only for hour-of-day plots.

**What could go wrong:** if we grouped by the raw `cet_cest_timestamp` string and parsed mixed `+0100` / `+0200` offsets without care, pandas can raise a mixed-timezone error. Convert from UTC instead.
"""
        ),
        md("## Missing demand values"),
        code(
            """
missing = df.loc[df["load_mw"].isna(), ["utc", "local", "load_mw"]]
print(f"Missing load_mw: {len(missing)} of {len(df)} rows "
      f"({100 * len(missing) / len(df):.3f}%)")
missing
"""
        ),
        md(
            """
### What this means

Missingness is rare (~0.05%) and clustered:

- the first hours of 2015 (series start)
- several hours on 2 January 2015
- six hours on 1 May 2015 (a public holiday in Spain — a reporting gap is plausible)
- a few hours in late September 2020, plus the last row

This is **not** random salt-and-pepper noise. Short clusters can be interpolated; long leading/trailing gaps should not be invented.

### Cleaning rule to use in Phase 4

1. Keep UTC as the index.
2. Interpolate `load_mw` in time only for gaps of **up to 3 hours**.
3. Leave longer gaps as missing and drop those hours when building lag features.
4. Never fill missing demand with 0.
"""
        ),
        code(
            """
load = df.set_index("utc")["load_mw"]
interpolated = load.interpolate(method="time", limit=3)
still_missing = interpolated.isna().sum()
print(f"Missing after time-interpolate (limit=3 hours): {still_missing}")
print("We do not save a processed file yet. Phase 4 will freeze this rule in a Python module.")
"""
        ),
        md("## Duplicates and invalid values"),
        code(
            """
print("Duplicate full rows:", int(df.duplicated().sum()))
print("load_mw <= 0:", int((df["load_mw"] <= 0).sum()))
print("Non-numeric leftovers:", int(pd.to_numeric(raw["load_mw"], errors="coerce").isna().sum() - df["load_mw"].isna().sum()))
"""
        ),
        md(
            """
### What this means

No duplicate rows, and no zero or negative demand. Invalid records are the 23 `NaN`s already listed.
"""
        ),
        md("## Scale of demand"),
        code(
            """
df["load_mw"].describe().round(1)
"""
        ),
        md(
            """
National Spanish load sits roughly between **16.6 GW and 41.0 GW**, with a mean near **28.4 GW**. That range is physically plausible for a country of Spain’s size. We will look at *when* the extremes happen in notebook 02, before calling them errors.
"""
        ),
        md(
            """
## Cleaning summary (input to Phase 4)

| Check | Result | Action later |
| --- | --- | --- |
| Timezone | Use UTC index; local time via `Europe/Madrid` | Implement in preprocessing |
| Sorting | Already chronological | Still sort defensively |
| Duplicates | None | Drop if they ever appear |
| Hourly gaps | None in UTC | `asfreq("h")` as a safety net |
| Missing load | 23 clustered `NaN`s | Interpolate ≤ 3 hours; otherwise drop at feature time |
| Zeros / negatives | None | Reject if they appear |
| Outliers | See notebook 02 | Do not clip winter peaks without evidence they are errors |

Next: `02_eda.ipynb` for daily, weekly, and seasonal patterns.
"""
        ),
    ]
    write_notebook("01_data_understanding.ipynb", cells)


def notebook_02() -> None:
    cells = [
        md(
            """
# 02 — Exploratory data analysis

**Phase 3 of Energy Intelligence.** Still no model training.

## What are we doing?

We look for **repeatable structure** in Spanish hourly demand: distribution, daily cycle, weekly cycle, seasons, and how strongly the next hour depends on recent hours.

## Why?

Those patterns tell us which features are worth engineering (hour, weekend, lags) and which years are risky as a test set (2020).
"""
        ),
        md("## Setup"),
        code(SETUP),
        code(
            """
raw = pd.read_csv(DATA_PATH)
df = raw.copy()
df["utc"] = pd.to_datetime(df["utc_timestamp"], utc=True)
df["local"] = df["utc"].dt.tz_convert("Europe/Madrid")
df["hour"] = df["local"].dt.hour
df["weekday"] = df["local"].dt.day_name()
df["month"] = df["local"].dt.month
df["year"] = df["local"].dt.year
df = df.sort_values("utc")
df.head()
"""
        ),
        md(
            """
## Distribution of demand

A histogram answers: is load a tight blob, or a wide spread with a long tail?
"""
        ),
        code(
            """
ax = df["load_mw"].plot.hist(bins=40, color=BRAND, edgecolor="white")
ax.set_title("Distribution of hourly Spanish electricity demand")
ax.set_xlabel("Load (MW)")
ax.set_ylabel("Hours")
plt.tight_layout()
plt.show()
"""
        ),
        md(
            """
### What this means

Demand is unimodal and fairly symmetric around ~28,000 MW. It is not a thin spike, so a “predict the mean every hour” baseline will be mediocre. The left tail (very low load) exists; we will see below that much of it is **nights in spring 2020**, not sensor faults.
"""
        ),
        md(
            """
## Outliers: statistics vs physics

The 1.5×IQR rule is a screen, not a diagnosis. Extreme hours in energy data are often real (cold evenings, heat waves).
"""
        ),
        code(
            """
q1 = df["load_mw"].quantile(0.25)
q3 = df["load_mw"].quantile(0.75)
iqr = q3 - q1
low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
outside = df["load_mw"].dropna()
n_low = int((outside < low).sum())
n_high = int((outside > high).sum())
print(f"IQR fence: {low:.0f} to {high:.0f} MW")
print(f"Hours below fence: {n_low}")
print(f"Hours above fence: {n_high}")
print()
print("Lowest hours:")
print(df.nsmallest(5, "load_mw")[["local", "load_mw"]].to_string(index=False))
print()
print("Highest hours:")
print(df.nlargest(5, "load_mw")[["local", "load_mw"]].to_string(index=False))
"""
        ),
        md(
            """
### What this means

**No hour falls outside the IQR fences.** The lowest points are early mornings in **April 2020** (COVID lockdown). The highest points are **winter evenings** (January 2017). Those are plausible human behaviour, not a reason to winsorize the target.

**What could go wrong:** clipping “outliers” here would remove the very peaks a demand model should learn.
"""
        ),
        md(
            """
## Time-series overview

Plotting 50,000 hourly points is unreadable. Daily mean load shows the trend without hiding 2020.
"""
        ),
        code(
            """
daily = df.set_index("local")["load_mw"].resample("D").mean()
ax = daily.plot(color=BRAND, linewidth=0.8)
ax.set_title("Daily mean demand")
ax.set_xlabel("Local date")
ax.set_ylabel("MW")
plt.tight_layout()
plt.show()
"""
        ),
        md(
            """
### What this means

You can see a repeating seasonal wave (higher in winter and mid-summer) and a **level drop in spring 2020**. A random shuffle of hours would mix COVID and pre-COVID behaviour into both train and test. Time-series order must be preserved later.
"""
        ),
        md(
            """
## Daily pattern (hour of day)

Spain’s clock is late compared with many northern European countries. We expect a low night, a morning ramp, and a late evening peak.
"""
        ),
        code(
            """
hourly = df.groupby("hour")["load_mw"].mean()
ax = hourly.plot(kind="bar", color=BRAND, width=0.85)
ax.set_title("Mean demand by local hour")
ax.set_xlabel("Hour of day (Europe/Madrid)")
ax.set_ylabel("MW")
ax.tick_params(axis="x", rotation=0)
plt.tight_layout()
plt.show()
"""
        ),
        md(
            """
### What this means

- Lowest around **04:00–05:00**.
- Morning ramp from 06:00 to midday.
- A first peak near **13:00**, then a small afternoon dip.
- A second peak around **20:00–21:00**.

That double peak is why `hour` (local) is a strong candidate feature. Using UTC hour would shift this curve and mix winter/summer offsets.
"""
        ),
        md("## Weekly pattern"),
        code(
            """
order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
weekly = df.groupby("weekday")["load_mw"].mean().reindex(order)
ax = weekly.plot(kind="bar", color=BRAND, width=0.7)
ax.set_title("Mean demand by weekday")
ax.set_xlabel("")
ax.set_ylabel("MW")
ax.tick_params(axis="x", rotation=30)
plt.tight_layout()
plt.show()
print((weekly / weekly["Wednesday"] * 100).round(1).astype(str) + "% of Wednesday")
"""
        ),
        md(
            """
### What this means

Weekdays are similar. **Saturday is lower, Sunday is lowest** (about 83% of a typical Wednesday). Industry and offices shutting down is a real effect, so `is_weekend` / `day_of_week` should help. There is little reason to treat Monday as a special extra dummy until residuals say otherwise.
"""
        ),
        md("## Monthly / seasonal pattern"),
        code(
            """
monthly = df.groupby("month")["load_mw"].mean()
ax = monthly.plot(kind="bar", color=BRAND, width=0.8)
ax.set_title("Mean demand by month")
ax.set_xlabel("Month")
ax.set_ylabel("MW")
ax.tick_params(axis="x", rotation=0)
plt.tight_layout()
plt.show()
"""
        ),
        md(
            """
### What this means

- **January–February** are high (heating).
- **April–May** are the lowest on average.
- **July** rises again (air conditioning).
- **August** is a bit lower than July — consistent with widespread summer holidays in Spain.

`month` is therefore a reasonable feature. This is still **not** a weather relationship; it is a calendar average that mixes temperature, holidays, and economic activity.
"""
        ),
        md(
            """
## 2020 vs 2019 (distribution shift)

If 2020 is used as the only test year, we may be testing a different world than we trained on.
"""
        ),
        code(
            """
compare = (
    df[df["year"].isin([2019, 2020])]
    .groupby(["month", "year"])["load_mw"]
    .mean()
    .unstack("year")
)
ax = compare.plot(color=["#64748b", BRAND], marker="o")
ax.set_title("Monthly mean demand: 2019 vs 2020")
ax.set_xlabel("Month")
ax.set_ylabel("MW")
ax.set_xticks(range(1, 13))
plt.tight_layout()
plt.show()
print("April mean 2019 vs 2020:")
print(compare.loc[4].round(0))
"""
        ),
        md(
            """
### What this means

April 2020 is far below April 2019 (lockdown). A fair later split might train through 2018, validate on 2019, and treat 2020 as a **stress test**, not the only proof of accuracy.

We will not drop 2020 from the dataset. We will be honest about it when we evaluate models.
"""
        ),
        md(
            """
## Time-series behaviour (why lags should help)

If load at 15:00 is close to load at 14:00, yesterday, and last week, then `lag_1`, `lag_24`, and `lag_168` are justified **before** we train anything.
"""
        ),
        code(
            """
series = df.set_index("utc")["load_mw"]
lag_corr = pd.Series(
    {
        "lag_1 (previous hour)": series.corr(series.shift(1)),
        "lag_24 (same hour yesterday)": series.corr(series.shift(24)),
        "lag_168 (same hour last week)": series.corr(series.shift(168)),
    }
)
print(lag_corr.round(3))
"""
        ),
        code(
            """
sample = df.dropna(subset=["load_mw"]).copy()
sample["lag_1"] = sample["load_mw"].shift(1)
ax = sample.plot.scatter(
    x="lag_1",
    y="load_mw",
    s=4,
    alpha=0.15,
    color=BRAND,
    figsize=(5.5, 5.5),
)
ax.set_title("Hour t vs hour t-1")
ax.set_xlabel("Previous hour (MW)")
ax.set_ylabel("Current hour (MW)")
plt.tight_layout()
plt.show()
"""
        ),
        md(
            """
### What this means

Hour-to-hour correlation is very high: demand barely jumps in a single hour. Same-hour-yesterday and same-hour-last-week are also strongly related. That supports the planned lag features.

**What could go wrong:** a naive model that always predicts “same as last hour” will already be hard to beat on MAE. We must keep that **persistence baseline** in Phase 6, or any ML model will look better than it is.
"""
        ),
        md(
            """
## Weather relationships

The raw file has **no temperature or humidity**. Plotting load against weather now would require inventing numbers or skipping ahead to the Open-Meteo service (Phase 5).

Hypotheses we will test after the join:

- Cold winter hours → higher heating load (we already see high January evenings).
- Hot summer hours → higher cooling load (we already see a July bump).
- Shoulder seasons (April–May) → weaker temperature effect.

Until weather is joined, do not claim that temperature “causes” these calendar patterns. Holidays and COVID can produce the same shape.
"""
        ),
        md(
            """
## Findings to carry forward

1. **Index:** UTC hourly grid is complete; use local time only for calendar features.
2. **Cleaning:** 23 missing loads; interpolate up to 3 hours; do not fill with 0; do not clip peaks.
3. **Features that look justified:** local hour, weekday/weekend, month, `lag_1`, `lag_24`, `lag_168`.
4. **Baseline:** previous-hour forecast will be strong.
5. **Split:** respect time order; be careful with 2020.
6. **Weather:** wait for Phase 5. No fake weather plots.

Phase 4 will turn the cleaning rules into a reusable Python module. No training yet.
"""
        ),
    ]
    write_notebook("02_eda.ipynb", cells)


if __name__ == "__main__":
    NOTEBOOKS.mkdir(parents=True, exist_ok=True)
    notebook_01()
    notebook_02()
    print("Wrote notebooks in", NOTEBOOKS)
