"""
Water Level Sensor Service for FloodTwin AI.

Manages water-level sensor telemetry across urban zones.
Provides in-memory state management, data validation, and modular interfaces
ready to connect to real IoT hardware, gateways, or MQTT subscribers.
"""

import json
import logging
import os
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.api.iot_schemas import (
    BulkWaterLevelTelemetry,
    WaterLevelTelemetry,
    WaterLevelTelemetryResponse,
)

logger = logging.getLogger(__name__)

ZONES_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "zones.json")
)

# Thread-safe in-memory store for the latest water-level telemetry per zone
_store_lock = threading.Lock()
_water_level_store: Dict[str, Dict[str, Any]] = {}

# Default baseline water level (cm) used when a zone has not yet reported telemetry
DEFAULT_BASELINE_WATER_LEVEL_CM = 15.0


def clear_sensor_store() -> None:
    """Clears all stored sensor telemetry (primarily for testing)."""
    with _store_lock:
        _water_level_store.clear()


def load_known_zone_ids() -> List[str]:
    """Loads all valid zone identifiers from app/data/zones.json."""
    if not os.path.exists(ZONES_PATH):
        raise FileNotFoundError(f"zones.json not found at {ZONES_PATH}")
    with open(ZONES_PATH, "r", encoding="utf-8") as f:
        zones = json.load(f)
        return [z["zone_id"] for z in zones if "zone_id" in z]


def validate_zone_id(zone_id: str) -> bool:
    """Checks whether the zone_id exists in the zone configuration."""
    known_zones = load_known_zone_ids()
    return zone_id in known_zones


def record_water_level(
    telemetry: WaterLevelTelemetry,
) -> WaterLevelTelemetryResponse:
    """
    Ingests and records a single water-level telemetry reading from a sensor or gateway.

    Validates:
      - zone_id exists in zones.json
      - water_level_cm is non-negative and within plausible physical limits

    Stores reading in the in-memory store and returns an acknowledgment response.
    """
    if not validate_zone_id(telemetry.zone_id):
        raise ValueError(f"Unknown zone_id '{telemetry.zone_id}'")

    if telemetry.water_level_cm < 0:
        raise ValueError("water_level_cm cannot be negative")

    # Sanity limit check for urban water level (e.g. 0 to 10,000 cm / 100 meters)
    if telemetry.water_level_cm > 10000.0:
        raise ValueError(
            f"water_level_cm value {telemetry.water_level_cm} exceeds plausible sensor range"
        )

    now_utc = datetime.now(timezone.utc)
    reading_timestamp = telemetry.timestamp or now_utc

    record = {
        "zone_id": telemetry.zone_id,
        "water_level_cm": round(float(telemetry.water_level_cm), 2),
        "sensor_id": telemetry.sensor_id,
        "timestamp": reading_timestamp,
        "recorded_at": now_utc,
    }

    with _store_lock:
        _water_level_store[telemetry.zone_id] = record

    logger.debug(
        f"Recorded water level for zone {telemetry.zone_id}: {telemetry.water_level_cm} cm"
    )

    return WaterLevelTelemetryResponse(
        status="recorded",
        zone_id=telemetry.zone_id,
        water_level_cm=record["water_level_cm"],
        sensor_id=telemetry.sensor_id,
        recorded_at=now_utc,
    )


def record_bulk_water_level(
    bulk_telemetry: BulkWaterLevelTelemetry,
) -> List[WaterLevelTelemetryResponse]:
    """
    Ingests multiple water-level telemetry readings in a single batch.
    """
    responses: List[WaterLevelTelemetryResponse] = []
    for reading in bulk_telemetry.readings:
        res = record_water_level(reading)
        responses.append(res)
    return responses


def get_latest_water_level(
    zone_id: str,
    default: Optional[float] = DEFAULT_BASELINE_WATER_LEVEL_CM,
) -> float:
    """
    Retrieves the latest water level (cm) for a given zone.
    If no telemetry has been recorded yet, returns the specified baseline default.
    """
    if not validate_zone_id(zone_id):
        raise ValueError(f"Unknown zone_id '{zone_id}'")

    with _store_lock:
        record = _water_level_store.get(zone_id)
        if record is not None:
            return float(record["water_level_cm"])

    return float(default if default is not None else DEFAULT_BASELINE_WATER_LEVEL_CM)


def get_water_level_record(zone_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves the full telemetry record (water_level_cm, sensor_id, timestamp, recorded_at)
    for a given zone, or None if no telemetry has been ingested yet.
    """
    if not validate_zone_id(zone_id):
        raise ValueError(f"Unknown zone_id '{zone_id}'")

    with _store_lock:
        record = _water_level_store.get(zone_id)
        if record is not None:
            return dict(record)
    return None


def get_all_water_levels() -> Dict[str, float]:
    """
    Retrieves the latest water-level readings across all known zones.
    Zones without telemetry readings will reflect their baseline default.
    """
    all_zone_ids = load_known_zone_ids()
    result: Dict[str, float] = {}

    with _store_lock:
        for z_id in all_zone_ids:
            if z_id in _water_level_store:
                result[z_id] = float(_water_level_store[z_id]["water_level_cm"])
            else:
                result[z_id] = DEFAULT_BASELINE_WATER_LEVEL_CM

    return result
