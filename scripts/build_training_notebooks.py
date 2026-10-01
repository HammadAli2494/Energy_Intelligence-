from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"


def md(text):
    return nbf.v4.new_markdown_cell(text.strip())


def code(text):
    return nbf.v4.new_code_cell(text.strip())


def write(name, cells):
    nb = nbf.v4.new_notebook()
    nb["cells"] = cells
    nb["metadata"] = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}
    }
    path = NOTEBOOKS / name
    path.write_text(nbf.writes(nb), encoding="utf-8")


SETUP = """
from pathlib import Path
import json
import pandas as pd

def project_root() -> Path:
    here = Path.cwd()
    for candidate in (here, here.parent):
        if (candidate / "models" / "model_metadata.json").exists():
            return candidate
    raise FileNotFoundError("Run: python ml_pipeline/train.py")

ROOT = project_root()
metadata = json.loads((ROOT / "models" / "model_metadata.json").read_text(encoding="utf-8"))
print("Selected:", metadata["selected_model"])
print("Rule:", metadata["selection_rule"])
print(metadata["split"])
"""

write(
    "04_model_training.ipynb",
    [
        md(
            """
# 04 — Model training

**This notebook reads saved results.** Training itself is `ml_pipeline/train.py` so we do not fit models twice by accident.

## What did we train?

One-hour-ahead Spanish demand (`load_mw` at hour t).

## Split (no shuffling)

| Split | Period | Why |
| --- | --- | --- |
| Train | through 2018 | Fit models |
| Validation | 2019 | Choose the winner |
| Test | 2020 | Report performance, including COVID demand shift |

2020 was **not** used to pick the model. If test MAE is worse than validation MAE, that is expected, not a bug we should “fix” by training on 2020.
"""
        ),
        code(SETUP),
        md(
            """
## Models compared

1. **Persistence** — predict `lag_1` (last hour). Strong baseline from EDA.
2. **Moving average 24** — predict `rolling_mean_24`. Weaker baseline.
3. **Linear regression** — scaled features, still a linear combination.
4. **Random forest** — nonlinear, sklearn.
5. **Histogram gradient boosting** — sklearn boosting. XGBoost was not added because this already covers gradient boosting without another library.

Winner = **lowest validation MAE**.
"""
        ),
        code(
            """
rows = []
for name, scores in metadata["metrics"].items():
    rows.append(
        {
            "model": name,
            "valid_MAE_MW": scores["valid"]["mae"],
            "valid_RMSE_MW": scores["valid"]["rmse"],
            "valid_MAPE_pct": scores["valid"]["mape"],
            "test_MAE_MW": scores["test"]["mae"],
            "test_RMSE_MW": scores["test"]["rmse"],
            "test_MAPE_pct": scores["test"]["mape"],
        }
    )
table = pd.DataFrame(rows).sort_values("valid_MAE_MW")
table
"""
        ),
        md(
            """
These numbers come from `models/model_metadata.json`, which was written by the training script. They are not placeholders.

Histogram gradient boosting won on 2019 validation. Test MAE is higher because 2020 demand dropped (COVID). Persistence is already ~1,030 MW MAE — any fancier model must beat that, and the trees did.
"""
        ),
    ],
)

write(
    "05_model_evaluation.ipynb",
    [
        md(
            """
# 05 — Model evaluation

Inspect the **saved** winner on 2020 test hours. We do not retrain here.
"""
        ),
        code(
            """
%matplotlib inline
from pathlib import Path
import json
import sys
import matplotlib.pyplot as plt
import pandas as pd

def project_root() -> Path:
    here = Path.cwd()
    for candidate in (here, here.parent):
        if (candidate / "models" / "forecast_model.joblib").exists():
            return candidate
    raise FileNotFoundError("Run: python ml_pipeline/train.py")

ROOT = project_root()
sys.path.insert(0, str(ROOT / "backend"))
from app.ml.predictor import load_forecast_artifact, predict_forecast
from app.ml.split import time_split
from app.ml.features import TARGET_COLUMN

metadata = json.loads((ROOT / "models" / "model_metadata.json").read_text(encoding="utf-8"))
features = pd.read_csv(ROOT / "data" / "processed" / "spain_hourly_features.csv")
_, _, test = time_split(features)
artifact = load_forecast_artifact(ROOT / "models" / "forecast_model.joblib")
test = test.copy()
test["predicted_load_mw"] = predict_forecast(artifact, test)
test["residual_mw"] = test["predicted_load_mw"] - test[TARGET_COLUMN]
test["utc"] = pd.to_datetime(test["utc_timestamp"], utc=True)
print("Selected:", metadata["selected_model"])
print(metadata["metrics"][metadata["selected_model"]])
"""
        ),
        md("## Actual vs predicted (one test week in January 2020, before the main lockdown drop)"),
        code(
            """
week = test[(test["utc"] >= "2020-01-13") & (test["utc"] < "2020-01-20")]
ax = week.set_index("utc")[[TARGET_COLUMN, "predicted_load_mw"]].plot(
    figsize=(10, 4.2), color=["#64748b", "#0f766e"]
)
ax.set_ylabel("MW")
ax.set_title("Test week: actual vs predicted")
plt.tight_layout()
plt.show()
"""
        ),
        md(
            """
## Residuals

A residual is predicted − actual. If residuals fan out over time or are huge on weekends only, the model is missing a pattern. Random scatter around zero is what we want.
"""
        ),
        code(
            """
fig, axes = plt.subplots(1, 2, figsize=(10, 4))
axes[0].hist(test["residual_mw"], bins=40, color="#0f766e", edgecolor="white")
axes[0].set_title("Test residual distribution")
axes[0].set_xlabel("Predicted − actual (MW)")
axes[1].scatter(test[TARGET_COLUMN], test["predicted_load_mw"], s=6, alpha=0.2, color="#0f766e")
axes[1].plot(
    [test[TARGET_COLUMN].min(), test[TARGET_COLUMN].max()],
    [test[TARGET_COLUMN].min(), test[TARGET_COLUMN].max()],
    color="#64748b",
)
axes[1].set_xlabel("Actual MW")
axes[1].set_ylabel("Predicted MW")
axes[1].set_title("Test actual vs predicted")
plt.tight_layout()
plt.show()
print("Residual mean MW:", round(test["residual_mw"].mean(), 2))
print("Residual std MW:", round(test["residual_mw"].std(), 2))
"""
        ),
        md(
            """
MAE is easier to explain than RMSE: on 2020 test hours the selected model is off by about **311 MW on average**. Mean Spanish demand is around 28,000 MW, so that is a bit over 1% MAPE.

This is still an estimate, not an operational dispatch tool.
"""
        ),
    ],
)

print("Wrote training and evaluation notebooks")
