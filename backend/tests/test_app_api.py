import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ml.anomaly_detector import severity_from_deviation
from app.services.app_data import app_data

client = TestClient(app)


def test_health_includes_model_flag() -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert "model_loaded" in response.json()


def test_residual_severity_rule() -> None:
    assert severity_from_deviation(100, 227) is None
    assert severity_from_deviation(500, 227) == "medium"
    assert severity_from_deviation(800, 227) == "high"


def test_model_metrics_endpoint() -> None:
    if not app_data.ready:
        app_data.load()
    response = client.get("/api/v1/model/metrics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["selected_model"] == "hist_gradient_boosting"
    assert payload["metrics"]["hist_gradient_boosting"]["valid"]["mae"] == pytest.approx(227.02, abs=0.01)


def test_dashboard_and_forecast_use_real_model() -> None:
    if not app_data.ready:
        app_data.load()
    summary = client.get("/api/v1/dashboard/summary")
    assert summary.status_code == 200
    body = summary.json()
    assert body["latest_demand_mw"] > 0
    assert "Sep 2020" in body["dataset_note"] or "2020" in body["dataset_note"]

    latest = client.get("/api/v1/forecast/latest")
    assert latest.status_code == 200
    assert latest.json()["forecast"]["predicted_load_mw"] > 0

    created = client.post("/api/v1/forecast")
    assert created.status_code == 200
    assert created.json()["forecast"]["actual_load_mw"] is None
    assert created.json()["forecast"]["predicted_load_mw"] > 0
    assert body["next_hour"]["predicted_load_mw"] > 0
    assert body["anomalies_total"] >= 0
    assert "valid" in body["model_performance"]

    recent = client.get("/api/v1/forecasts/recent?limit=5")
    assert recent.status_code == 200
    recent_body = recent.json()
    assert recent_body["source"] in {"dataset", "mongodb"}
    assert 1 <= len(recent_body["items"]) <= 5


def test_anomalies_and_invalid_filter() -> None:
    if not app_data.ready:
        app_data.load()
    bad = client.get("/api/v1/anomalies?severity=critical")
    assert bad.status_code == 400
    ok = client.get("/api/v1/anomalies?limit=5")
    assert ok.status_code == 200
    payload = ok.json()
    assert payload["valid_mae_mw"] == pytest.approx(227.02, abs=0.01)
    assert len(payload["items"]) <= 5


def test_contact_rejects_invalid_email() -> None:
    response = client.post(
        "/api/v1/contact",
        json={"name": "A", "email": "not-an-email", "subject": "Hi", "message": "short"},
    )
    assert response.status_code == 422


def test_contact_without_mongo_is_unavailable() -> None:
    response = client.post(
        "/api/v1/contact",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "subject": "Portfolio question",
            "message": "This is a long enough message for validation.",
        },
    )
    assert response.status_code == 503
