"""
Integration Service for FloodTwin AI.

Acts as the central orchestrator connecting:
- Weather Service (live rainfall observations & future forecasts)
- Sensor Service (live/cached water-level telemetry)
- Zone GIS metadata (elevation, drainage capacity, flood frequency)
- AI/ML Model Engine (risk score prediction & forward trajectory simulation)

Provides unified interfaces producing structured assessment payloads (ZoneLiveStatusResponse)
ready for consumption by Backend, Dashboard, and Digital Twin modules.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.api.iot_schemas import (
    ForecastPoint,
    ZoneLiveStatusResponse,
)
from app.models.forecast import (
    forecast_risk_trajectory,
    predict_risk_score,
    risk_level_from_score,
)
from app.services.sensor_service import (
    DEFAULT_BASELINE_WATER_LEVEL_CM,
    get_latest_water_level,
)
from app.services.weather_service import (
    get_live_rainfall,
    get_rainfall_forecast,
    load_zones_data,
)

logger = logging.getLogger(__name__)

ZONES_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "zones.json")
)


def _get_zone_metadata(zone_id: str) -> Dict[str, Any]:
    """Retrieves static metadata for a given zone_id from zones.json."""
    zones = load_zones_data()
    for zone in zones:
        if zone.get("zone_id") == zone_id:
            return zone
    raise ValueError(f"Zone '{zone_id}' not found in configuration")


def prepare_zone_prediction_input(zone_id: str) -> Dict[str, Any]:
    """
    Collects live rainfall and water-level readings and combines them with static zone metadata.

    Returns a normalized feature dictionary ready for the AI/ML prediction engine:
      - zone_id, zone_name
      - rainfall_mm_last_1h, rainfall_mm_last_6h
      - water_level_cm
      - drainage_capacity, elevation_m, historical_flood_frequency
    """
    zone = _get_zone_metadata(zone_id)

    # 1. Fetch live rainfall observations (with safe fallback)
    try:
        weather = get_live_rainfall(zone_id)
        rainfall_1h = max(0.0, float(weather.get("rainfall_mm_last_1h", 0.0)))
        rainfall_6h = max(0.0, float(weather.get("rainfall_mm_last_6h", 0.0)))
    except Exception as err:
        logger.warning(
            f"Failed to collect weather for zone {zone_id} ({err}). Using 0.0 mm baseline."
        )
        rainfall_1h = 0.0
        rainfall_6h = 0.0

    # 2. Fetch latest water level from IoT sensor store (with safe baseline default)
    try:
        water_level = get_latest_water_level(
            zone_id, default=DEFAULT_BASELINE_WATER_LEVEL_CM
        )
    except Exception as err:
        logger.warning(
            f"Failed to collect sensor telemetry for zone {zone_id} ({err}). Using baseline."
        )
        water_level = DEFAULT_BASELINE_WATER_LEVEL_CM

    return {
        "zone_id": zone_id,
        "zone_name": zone.get("name", zone_id),
        "rainfall_mm_last_1h": round(rainfall_1h, 2),
        "rainfall_mm_last_6h": round(rainfall_6h, 2),
        "water_level_cm": round(water_level, 2),
        "drainage_capacity": float(zone["drainage_capacity"]),
        "elevation_m": float(zone["elevation_m"]),
        "historical_flood_frequency": float(zone["historical_flood_frequency"]),
        "lat": float(zone.get("lat", 0.0)),
        "lng": float(zone.get("lng", 0.0)),
    }


def get_zone_live_assessment(
    zone_id: str, forecast_hours: int = 6
) -> ZoneLiveStatusResponse:
    """
    Performs full end-to-end integration assessment for a single zone:
    1. Collects live rainfall and water-level data.
    2. Runs AI/ML model to predict real-time flood risk score (0-100) and severity level.
    3. Retrieves multi-hour rainfall forecast and simulates forward risk trajectory.
    4. Bundles output into a typed ZoneLiveStatusResponse.
    """
    zone_input = prepare_zone_prediction_input(zone_id)
    zone_meta = _get_zone_metadata(zone_id)

    # 1. Run real-time AI risk score prediction
    score = predict_risk_score(
        rainfall_mm_last_1h=zone_input["rainfall_mm_last_1h"],
        rainfall_mm_last_6h=zone_input["rainfall_mm_last_6h"],
        water_level_cm=zone_input["water_level_cm"],
        drainage_capacity=zone_input["drainage_capacity"],
        elevation_m=zone_input["elevation_m"],
        historical_flood_frequency=zone_input["historical_flood_frequency"],
    )
    risk_level = risk_level_from_score(score)

    # 2. Collect rainfall forecast series
    try:
        rainfall_forecast = get_rainfall_forecast(
            zone_id, hours=forecast_hours
        )
    except Exception as err:
        logger.warning(
            f"Failed to fetch rainfall forecast for zone {zone_id} ({err}). Using 0.0 mm."
        )
        rainfall_forecast = [0.0] * forecast_hours

    # 3. Simulate forward risk trajectory
    trajectory_raw = forecast_risk_trajectory(
        zone=zone_meta,
        rainfall_forecast_mm=rainfall_forecast,
        current_water_level_cm=zone_input["water_level_cm"],
    )

    forecast_points = [
        ForecastPoint(
            hours_ahead=point["hours_ahead"],
            predicted_risk_score=point["predicted_risk_score"],
            risk_level=point["risk_level"],
        )
        for point in trajectory_raw
    ]

    return ZoneLiveStatusResponse(
        zone_id=zone_id,
        zone_name=zone_input["zone_name"],
        rainfall_mm_last_1h=zone_input["rainfall_mm_last_1h"],
        rainfall_mm_last_6h=zone_input["rainfall_mm_last_6h"],
        water_level_cm=zone_input["water_level_cm"],
        risk_score=round(score, 2),
        risk_level=risk_level,
        rainfall_forecast_mm=rainfall_forecast,
        forecast_trajectory=forecast_points,
        timestamp=datetime.now(timezone.utc),
    )


def get_all_zones_live_assessment(
    forecast_hours: int = 6,
) -> List[ZoneLiveStatusResponse]:
    """
    Executes live data integration and AI risk assessment across all 12 configured zones.
    """
    zones = load_zones_data()
    assessments: List[ZoneLiveStatusResponse] = []

    for zone in zones:
        z_id = zone.get("zone_id")
        if not z_id:
            continue
        try:
            assessment = get_zone_live_assessment(
                zone_id=z_id, forecast_hours=forecast_hours
            )
            assessments.append(assessment)
        except Exception as err:
            logger.error(
                f"Failed to generate assessment for zone {z_id}: {err}"
            )

    return assessments
