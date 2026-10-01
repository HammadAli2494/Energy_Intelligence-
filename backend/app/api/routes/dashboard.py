from fastapi import APIRouter

from app.api.dependencies import loaded_data
from app.services.forecast_service import analytics_payload, dashboard_summary, history_points

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard/summary")
def dashboard():
    data = loaded_data()
    summary = dashboard_summary(data)
    summary["recent_history"] = history_points(data, limit=168)
    return summary


@router.get("/analytics")
def analytics():
    data = loaded_data()
    return analytics_payload(data)


@router.get("/model/metrics")
def model_metrics():
    data = loaded_data()
    return {
        "selected_model": data.metadata["selected_model"],
        "selection_rule": data.metadata["selection_rule"],
        "split": data.metadata["split"],
        "metrics": data.metadata["metrics"],
        "units": data.metadata["units"],
        "notes": data.metadata.get("notes", []),
        "feature_columns": data.metadata["feature_columns"],
        "feature_importance": data.metadata.get("feature_importance"),
        "disclaimer": "Metrics are from the offline time-series evaluation. They are not live accuracy.",
    }
