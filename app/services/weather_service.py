"""
Weather Service for FloodTwin AI.

Integrates with the Open-Meteo API to fetch observed precipitation and short-term
rainfall forecasts based on zone geographic coordinates (lat/lng) loaded from
app/data/zones.json.

Includes an in-memory cache (TTL: 10 minutes) and resilient offline fallback logic.
"""

import json
import logging
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

ZONES_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "zones.json")
)

# In-memory cache configuration (10 minutes TTL)
CACHE_TTL_SECONDS = 600
_weather_cache: Dict[str, Dict[str, Any]] = {}


def clear_weather_cache() -> None:
    """Clears all cached weather data."""
    global _weather_cache
    _weather_cache.clear()


def load_zones_data() -> List[Dict[str, Any]]:
    """Loads all zones from app/data/zones.json."""
    if not os.path.exists(ZONES_PATH):
        raise FileNotFoundError(f"zones.json not found at {ZONES_PATH}")
    with open(ZONES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_zone_by_id(zone_id: str) -> Dict[str, Any]:
    """Finds zone metadata by zone_id or raises ValueError."""
    zones = load_zones_data()
    for zone in zones:
        if zone.get("zone_id") == zone_id:
            return zone
    raise ValueError(f"Zone '{zone_id}' not found in {ZONES_PATH}")


def _find_current_hour_index(times: List[str]) -> int:
    """Finds the index of the hourly timestamp closest to current UTC time."""
    if not times:
        return 0

    now_utc = datetime.now(timezone.utc)
    now_hour_str = now_utc.strftime("%Y-%m-%dT%H:00")

    if now_hour_str in times:
        return times.index(now_hour_str)

    best_idx = 0
    min_diff = float("inf")
    for idx, t_str in enumerate(times):
        try:
            t_dt = datetime.fromisoformat(t_str).replace(tzinfo=timezone.utc)
            diff = abs((t_dt - now_utc).total_seconds())
            if diff < min_diff:
                min_diff = diff
                best_idx = idx
        except Exception:
            continue
    return best_idx


def _generate_fallback_weather(lat: float, lng: float) -> Dict[str, Any]:
    """Generates synthetic hourly rainfall series for offline/fallback execution."""
    now_utc = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    times = []
    precipitation = []

    # Generate 24 hours of past data and 48 hours of future data
    for offset in range(-24, 49):
        hour_dt = now_utc + timedelta(hours=offset)
        times.append(hour_dt.strftime("%Y-%m-%dT%H:00"))
        # Baseline plausible precipitation
        precipitation.append(round(max(0.0, float((abs(offset * 7) % 25))), 1))

    return {
        "latitude": lat,
        "longitude": lng,
        "hourly": {
            "time": times,
            "precipitation": precipitation,
        },
        "source": "fallback_offline",
    }


def fetch_zone_weather(
    lat: float,
    lng: float,
    past_days: int = 1,
    forecast_days: int = 2,
) -> Dict[str, Any]:
    """
    Fetches hourly precipitation from Open-Meteo API for given coordinates.
    Results are cached in memory for CACHE_TTL_SECONDS.
    """
    cache_key = f"{lat:.4f}_{lng:.4f}_{past_days}_{forecast_days}"
    now = time.time()

    if cache_key in _weather_cache:
        entry = _weather_cache[cache_key]
        if now - entry["cached_at"] < CACHE_TTL_SECONDS:
            return entry["data"]

    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat:.4f}&longitude={lng:.4f}"
        f"&hourly=precipitation"
        f"&past_days={past_days}"
        f"&forecast_days={forecast_days}"
        f"&timezone=UTC"
    )

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "FloodTwinAI/1.0 (weather-service)"},
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                data["source"] = "open-meteo"
                _weather_cache[cache_key] = {"data": data, "cached_at": now}
                return data
    except Exception as err:
        logger.warning(
            f"Failed to fetch live weather from Open-Meteo ({err}). Using fallback data."
        )

    fallback_data = _generate_fallback_weather(lat, lng)
    _weather_cache[cache_key] = {"data": fallback_data, "cached_at": now}
    return fallback_data


def get_live_rainfall(zone_id: str) -> Dict[str, Any]:
    """
    Retrieves observed rainfall for the last 1 hour and past 6 hours for a specific zone.

    Returns:
        {
            "zone_id": str,
            "rainfall_mm_last_1h": float,
            "rainfall_mm_last_6h": float,
            "source": str,
            "timestamp": str
        }
    """
    zone = _get_zone_by_id(zone_id)
    weather_data = fetch_zone_weather(lat=zone["lat"], lng=zone["lng"])

    hourly = weather_data.get("hourly", {})
    times = hourly.get("time", [])
    precip = hourly.get("precipitation", [])

    if not precip:
        return {
            "zone_id": zone_id,
            "rainfall_mm_last_1h": 0.0,
            "rainfall_mm_last_6h": 0.0,
            "source": weather_data.get("source", "unknown"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    current_idx = _find_current_hour_index(times)

    # Observed rainfall last 1h (at or immediately prior to current hour)
    rainfall_1h = precip[current_idx] if current_idx < len(precip) else 0.0

    # Cumulative rainfall over the last 6 hours
    start_idx = max(0, current_idx - 5)
    past_6h_window = precip[start_idx : current_idx + 1]
    rainfall_6h = sum(past_6h_window) if past_6h_window else rainfall_1h

    return {
        "zone_id": zone_id,
        "rainfall_mm_last_1h": round(float(rainfall_1h), 2),
        "rainfall_mm_last_6h": round(float(rainfall_6h), 2),
        "source": weather_data.get("source", "open-meteo"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def get_rainfall_forecast(zone_id: str, hours: int = 6) -> List[float]:
    """
    Retrieves forecasted hourly rainfall (mm) for the next N hours (1 to 6h) for a specific zone.

    Returns:
        List[float] of length `hours`, e.g. [12.0, 18.5, 25.0, 10.0, 5.0, 0.0]
    """
    zone = _get_zone_by_id(zone_id)
    weather_data = fetch_zone_weather(lat=zone["lat"], lng=zone["lng"])

    hourly = weather_data.get("hourly", {})
    times = hourly.get("time", [])
    precip = hourly.get("precipitation", [])

    if not precip:
        return [0.0] * hours

    current_idx = _find_current_hour_index(times)

    # Forecast begins at current_idx + 1
    forecast_start = current_idx + 1
    forecast_end = forecast_start + hours
    forecast_slice = precip[forecast_start:forecast_end]

    # Pad with trailing 0.0 if forecast slice is shorter than requested hours
    if len(forecast_slice) < hours:
        forecast_slice.extend([0.0] * (hours - len(forecast_slice)))

    return [round(float(val), 2) for val in forecast_slice[:hours]]
