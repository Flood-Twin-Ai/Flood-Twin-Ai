from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)

def test_valid_risk_score():
    response = client.post(
        "/predict/risk-score",
        json={
            "zone_id": "Z001",
            "rainfall_mm_last_1h": 35.0,
            "rainfall_mm_last_6h": 80.0,
            "water_level_cm": 120.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert "risk_level" in data
    assert data["zone_id"] == "Z001"

def test_invalid_zone_id():
    response = client.post(
        "/predict/risk-score",
        json={
            "zone_id": "INVALID_ZONE",
            "rainfall_mm_last_1h": 35.0,
            "rainfall_mm_last_6h": 80.0,
            "water_level_cm": 120.0
        }
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Zone 'INVALID_ZONE' not found"

def test_negative_rainfall():
    response = client.post(
        "/predict/risk-score",
        json={
            "zone_id": "Z001",
            "rainfall_mm_last_1h": -5.0,
            "rainfall_mm_last_6h": 80.0,
            "water_level_cm": 120.0
        }
    )
    assert response.status_code == 422
    # Pydantic returns 422 for validation errors

def test_forecast_correct_hours():
    forecast_input = [15, 25, 40, 30, 10, 5]
    response = client.post(
        "/predict/forecast",
        json={
            "zone_id": "Z001",
            "rainfall_forecast_mm": forecast_input,
            "current_water_level_cm": 70.0
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "forecast" in data
    assert len(data["forecast"]) == len(forecast_input)
    for i, forecast_item in enumerate(data["forecast"]):
        assert forecast_item["hours_ahead"] == i + 1
        assert "predicted_risk_score" in forecast_item
        assert "risk_level" in forecast_item
