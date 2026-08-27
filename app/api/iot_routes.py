"""
FastAPI Routes for Data/IoT Integration Layer in FloodTwin AI.

Exposes REST endpoints for:
- Ingesting and querying water-level IoT sensor telemetry.
- Querying consolidated real-time zone assessments (combining live weather,
  sensor readings, and AI/ML model predictions).
- Synchronizing external weather feeds.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.api.iot_schemas import (
    BulkWaterLevelTelemetry,
    WaterLevelTelemetry,
    WaterLevelTelemetryResponse,
    WeatherSyncResponse,
    ZoneLiveStatusResponse,
)
from app.services.integration_service import (
    get_all_zones_live_assessment,
    get_zone_live_assessment,
    prepare_zone_prediction_input,
)
from app.services.sensor_service import (
    get_all_water_levels,
    get_latest_water_level,
    get_water_level_record,
    record_bulk_water_level,
    record_water_level,
    validate_zone_id,
)
from app.services.weather_service import (
    clear_weather_cache,
    load_zones_data,
)

router = APIRouter(prefix="/iot", tags=["Data/IoT Integration"])


@router.post(
    "/telemetry/water-level",
    response_model=WaterLevelTelemetryResponse,
    summary="Ingest Water Level Sensor Telemetry",
    description="Receives and validates a real-time water-level reading from a hardware sensor or gateway.",
)
def ingest_water_level_telemetry(payload: WaterLevelTelemetry):
    if not validate_zone_id(payload.zone_id):
        raise HTTPException(
            status_code=404, detail=f"Zone '{payload.zone_id}' not found"
        )

    try:
        response = record_water_level(payload)
        return response
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.post(
    "/telemetry/water-level/bulk",
    response_model=List[WaterLevelTelemetryResponse],
    summary="Batch Ingest Water Level Telemetry",
    description="Ingests multiple sensor readings across multiple zones in a single batch request.",
)
def ingest_bulk_water_level_telemetry(payload: BulkWaterLevelTelemetry):
    try:
        responses = record_bulk_water_level(payload)
        return responses
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))


@router.get(
    "/water-level/{zone_id}",
    summary="Get Latest Water Level for a Zone",
    description="Retrieves the most recent recorded water level (cm) and sensor metadata for the specified zone.",
)
def get_zone_water_level(zone_id: str):
    if not validate_zone_id(zone_id):
        raise HTTPException(
            status_code=404, detail=f"Zone '{zone_id}' not found"
        )

    water_level = get_latest_water_level(zone_id)
    record = get_water_level_record(zone_id)

    return {
        "zone_id": zone_id,
        "water_level_cm": water_level,
        "sensor_id": record["sensor_id"] if record else None,
        "recorded_at": record["recorded_at"] if record else None,
        "is_baseline_default": record is None,
    }


@router.get(
    "/water-level",
    response_model=Dict[str, float],
    summary="Get Latest Water Levels for All Zones",
    description="Returns a dictionary mapping all known zone IDs to their latest water levels in centimeters.",
)
def get_all_zones_water_levels():
    return get_all_water_levels()


@router.get(
    "/live-assessment/{zone_id}",
    response_model=ZoneLiveStatusResponse,
    summary="Get Integrated Real-Time Assessment for a Zone",
    description="Combines live rainfall, water level, and static zone data to run AI flood risk scoring and forward trajectory forecasting.",
)
def get_zone_assessment(
    zone_id: str,
    forecast_hours: int = Query(
        default=6,
        ge=1,
        le=24,
        description="Number of future hours for rainfall forecast and risk trajectory simulation",
    ),
):
    if not validate_zone_id(zone_id):
        raise HTTPException(
            status_code=404, detail=f"Zone '{zone_id}' not found"
        )

    try:
        assessment = get_zone_live_assessment(
            zone_id=zone_id, forecast_hours=forecast_hours
        )
        return assessment
    except Exception as err:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate assessment for zone '{zone_id}': {err}",
        )


@router.get(
    "/live-overview",
    response_model=List[ZoneLiveStatusResponse],
    summary="Get Real-Time Overview for All Zones",
    description="Returns consolidated live status and AI predictions for all 12 zones for GIS dashboard visualization.",
)
def get_live_overview(
    forecast_hours: int = Query(
        default=6,
        ge=1,
        le=24,
        description="Number of future hours for rainfall forecast and risk trajectory simulation",
    ),
):
    try:
        overview = get_all_zones_live_assessment(forecast_hours=forecast_hours)
        return overview
    except Exception as err:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate live overview: {err}",
        )


@router.post(
    "/sync-weather",
    response_model=WeatherSyncResponse,
    summary="Force Sync External Weather Data",
    description="Clears cache and forces an updated sync from the external Open-Meteo weather API across all zones.",
)
def sync_weather():
    clear_weather_cache()
    zones = load_zones_data()
    return WeatherSyncResponse(
        status="ok",
        synced_zones_count=len(zones),
        source="open-meteo",
        synced_at=datetime.now(timezone.utc),
    )
