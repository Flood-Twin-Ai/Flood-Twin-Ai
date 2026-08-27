"""
Integration and Unit Tests for the Data/IoT Integration Layer.

Tests:
1. IoT water-level telemetry schema validation.
2. Storing and retrieving the latest sensor readings per zone.
3. Integration of rainfall/weather data with water-level telemetry and AI/ML model inference.
4. Safe fallback behavior during network/sensor feed outages.
5. FastAPI IoT route validation, HTTP response statuses, and payloads.
"""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import urllib.error

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.api.iot_routes import router as iot_router
from app.api.iot_schemas import (
    BulkWaterLevelTelemetry,
    WaterLevelTelemetry,
    WaterLevelTelemetryResponse,
    ZoneLiveStatusResponse,
    ZoneWeatherData,
)
from app.services.integration_service import (
    get_all_zones_live_assessment,
    get_zone_live_assessment,
    prepare_zone_prediction_input,
)
from app.services.sensor_service import (
    DEFAULT_BASELINE_WATER_LEVEL_CM,
    clear_sensor_store,
    get_all_water_levels,
    get_latest_water_level,
    get_water_level_record,
    record_bulk_water_level,
    record_water_level,
    validate_zone_id,
)
from app.services.weather_service import (
    clear_weather_cache,
    fetch_zone_weather,
    get_live_rainfall,
    get_rainfall_forecast,
)

# Test client mounted with the IoT router
app = FastAPI()
app.include_router(iot_router)
client = TestClient(app)


@pytest.fixture(autouse=True)
def cleanup_stores():
    """Resets in-memory sensor store and weather cache before each test."""
    clear_sensor_store()
    clear_weather_cache()
    yield
    clear_sensor_store()
    clear_weather_cache()


# =====================================================================
# 1. Telemetry Validation Tests
# =====================================================================

def test_water_level_telemetry_valid():
    telemetry = WaterLevelTelemetry(
        zone_id="Z001",
        water_level_cm=85.5,
        sensor_id="WL-101",
    )
    assert telemetry.zone_id == "Z001"
    assert telemetry.water_level_cm == 85.5
    assert telemetry.sensor_id == "WL-101"


def test_water_level_telemetry_negative_raises_validation_error():
    with pytest.raises(ValidationError):
        WaterLevelTelemetry(zone_id="Z001", water_level_cm=-10.0)


def test_bulk_telemetry_empty_list_raises_error():
    with pytest.raises(ValidationError):
        BulkWaterLevelTelemetry(readings=[])


def test_record_water_level_unknown_zone_raises_value_error():
    telemetry = WaterLevelTelemetry(zone_id="Z999", water_level_cm=50.0)
    with pytest.raises(ValueError, match="Unknown zone_id"):
        record_water_level(telemetry)


def test_record_water_level_excessive_value_raises_value_error():
    telemetry = WaterLevelTelemetry(zone_id="Z001", water_level_cm=15000.0)
    with pytest.raises(ValueError, match="exceeds plausible"):
        record_water_level(telemetry)


# =====================================================================
# 2. Sensor Service Storage & Retrieval Tests
# =====================================================================

def test_sensor_service_default_baseline():
    level = get_latest_water_level("Z001")
    assert level == DEFAULT_BASELINE_WATER_LEVEL_CM
    assert get_water_level_record("Z001") is None


def test_sensor_service_record_and_retrieve():
    telemetry = WaterLevelTelemetry(
        zone_id="Z001",
        water_level_cm=92.4,
        sensor_id="WL-101",
    )
    res = record_water_level(telemetry)
    assert res.status == "recorded"
    assert res.water_level_cm == 92.4

    latest = get_latest_water_level("Z001")
    assert latest == 92.4

    record = get_water_level_record("Z001")
    assert record is not None
    assert record["sensor_id"] == "WL-101"
    assert record["water_level_cm"] == 92.4


def test_sensor_service_bulk_recording():
    t1 = WaterLevelTelemetry(zone_id="Z001", water_level_cm=45.0)
    t2 = WaterLevelTelemetry(zone_id="Z002", water_level_cm=65.0)
    bulk = BulkWaterLevelTelemetry(readings=[t1, t2])

    responses = record_bulk_water_level(bulk)
    assert len(responses) == 2
    assert get_latest_water_level("Z001") == 45.0
    assert get_latest_water_level("Z002") == 65.0


def test_sensor_service_get_all_water_levels():
    record_water_level(WaterLevelTelemetry(zone_id="Z001", water_level_cm=50.0))
    all_levels = get_all_water_levels()
    assert len(all_levels) == 12
    assert all_levels["Z001"] == 50.0
    assert all_levels["Z002"] == DEFAULT_BASELINE_WATER_LEVEL_CM


# =====================================================================
# 3. Weather Service with Mocks
# =====================================================================

def _get_mock_open_meteo_response():
    times = [
        "2026-08-25T12:00",
        "2026-08-25T13:00",
        "2026-08-25T14:00",
        "2026-08-25T15:00",
        "2026-08-25T16:00",
        "2026-08-25T17:00",
        "2026-08-25T18:00",
        "2026-08-25T19:00",
        "2026-08-25T20:00",
        "2026-08-25T21:00",
    ]
    precip = [5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 15.0, 10.0, 5.0, 0.0]
    return {
        "latitude": 19.076,
        "longitude": 72.8777,
        "hourly": {"time": times, "precipitation": precip},
    }


@patch("urllib.request.urlopen")
def test_fetch_zone_weather_mocked(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(_get_mock_open_meteo_response()).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    data = fetch_zone_weather(19.0760, 72.8777)
    assert data["source"] == "open-meteo"
    assert "hourly" in data
    assert len(data["hourly"]["precipitation"]) == 10


@patch("urllib.request.urlopen")
def test_weather_fallback_on_network_error(mock_urlopen):
    mock_urlopen.side_effect = urllib.error.URLError("Network connection failed")

    data = fetch_zone_weather(19.0760, 72.8777)
    assert data["source"] == "fallback_offline"
    assert "hourly" in data
    assert len(data["hourly"]["precipitation"]) > 0


@patch("urllib.request.urlopen")
def test_live_rainfall_and_forecast_extraction(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(_get_mock_open_meteo_response()).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    rainfall = get_live_rainfall("Z001")
    assert rainfall["zone_id"] == "Z001"
    assert rainfall["rainfall_mm_last_1h"] >= 0
    assert rainfall["rainfall_mm_last_6h"] >= rainfall["rainfall_mm_last_1h"]

    forecast = get_rainfall_forecast("Z001", hours=6)
    assert isinstance(forecast, list)
    assert len(forecast) == 6


# =====================================================================
# 4. Integration Service Tests (Weather + Sensor + AI Model)
# =====================================================================

@patch("urllib.request.urlopen")
def test_prepare_zone_prediction_input(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(_get_mock_open_meteo_response()).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    record_water_level(WaterLevelTelemetry(zone_id="Z001", water_level_cm=75.0))

    features = prepare_zone_prediction_input("Z001")
    assert features["zone_id"] == "Z001"
    assert features["water_level_cm"] == 75.0
    assert "rainfall_mm_last_1h" in features
    assert "rainfall_mm_last_6h" in features
    assert "drainage_capacity" in features
    assert "elevation_m" in features


@patch("urllib.request.urlopen")
def test_get_zone_live_assessment_with_ai(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(_get_mock_open_meteo_response()).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    record_water_level(WaterLevelTelemetry(zone_id="Z001", water_level_cm=110.0))

    assessment = get_zone_live_assessment("Z001", forecast_hours=6)
    assert isinstance(assessment, ZoneLiveStatusResponse)
    assert assessment.zone_id == "Z001"
    assert 0 <= assessment.risk_score <= 100
    assert assessment.risk_level in ["low", "moderate", "high", "severe"]
    assert len(assessment.forecast_trajectory) == 6


@patch("urllib.request.urlopen")
def test_get_all_zones_live_assessment(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(_get_mock_open_meteo_response()).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    assessments = get_all_zones_live_assessment(forecast_hours=3)
    assert len(assessments) == 12
    for item in assessments:
        assert 0 <= item.risk_score <= 100
        assert len(item.forecast_trajectory) == 3


def test_integration_safety_during_total_weather_outage():
    # Calling without mock will trigger the internal fallback logic safely
    assessment = get_zone_live_assessment("Z002", forecast_hours=4)
    assert assessment.zone_id == "Z002"
    assert 0 <= assessment.risk_score <= 100
    assert len(assessment.forecast_trajectory) == 4


# =====================================================================
# 5. IoT API Route Validation Tests
# =====================================================================

def test_api_ingest_telemetry_success():
    response = client.post(
        "/iot/telemetry/water-level",
        json={
            "zone_id": "Z001",
            "water_level_cm": 88.0,
            "sensor_id": "WL-SENSOR-1",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "recorded"
    assert data["zone_id"] == "Z001"
    assert data["water_level_cm"] == 88.0
    assert data["sensor_id"] == "WL-SENSOR-1"


def test_api_ingest_telemetry_unknown_zone_404():
    response = client.post(
        "/iot/telemetry/water-level",
        json={
            "zone_id": "INVALID_ZONE",
            "water_level_cm": 50.0,
        },
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_api_ingest_telemetry_negative_value_422():
    response = client.post(
        "/iot/telemetry/water-level",
        json={
            "zone_id": "Z001",
            "water_level_cm": -20.0,
        },
    )
    assert response.status_code == 422


def test_api_ingest_bulk_telemetry():
    payload = {
        "readings": [
            {"zone_id": "Z001", "water_level_cm": 60.0, "sensor_id": "WL-1"},
            {"zone_id": "Z002", "water_level_cm": 75.0, "sensor_id": "WL-2"},
        ]
    }
    response = client.post("/iot/telemetry/water-level/bulk", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["zone_id"] == "Z001"
    assert data[1]["zone_id"] == "Z002"


def test_api_get_water_level_zone():
    client.post(
        "/iot/telemetry/water-level",
        json={"zone_id": "Z003", "water_level_cm": 95.0, "sensor_id": "WL-3"},
    )
    response = client.get("/iot/water-level/Z003")
    assert response.status_code == 200
    data = response.json()
    assert data["zone_id"] == "Z003"
    assert data["water_level_cm"] == 95.0
    assert data["sensor_id"] == "WL-3"
    assert data["is_baseline_default"] is False


def test_api_get_all_water_levels():
    response = client.get("/iot/water-level")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 12
    assert "Z001" in data


@patch("urllib.request.urlopen")
def test_api_get_live_assessment(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(_get_mock_open_meteo_response()).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    client.post(
        "/iot/telemetry/water-level",
        json={"zone_id": "Z001", "water_level_cm": 115.0},
    )

    response = client.get("/iot/live-assessment/Z001?forecast_hours=6")
    assert response.status_code == 200
    data = response.json()
    assert data["zone_id"] == "Z001"
    assert "risk_score" in data
    assert "risk_level" in data
    assert len(data["forecast_trajectory"]) == 6


@patch("urllib.request.urlopen")
def test_api_get_live_overview(mock_urlopen):
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps(_get_mock_open_meteo_response()).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    response = client.get("/iot/live-overview?forecast_hours=4")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 12


def test_api_sync_weather():
    response = client.post("/iot/sync-weather")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["synced_zones_count"] == 12
    assert data["source"] == "open-meteo"
