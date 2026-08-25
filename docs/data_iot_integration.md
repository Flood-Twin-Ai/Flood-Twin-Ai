# Data/IoT Integration Layer Documentation

## 1. Overview and Purpose

The **Data/IoT Integration Layer** serves as the bridge between external environmental telemetry, field IoT sensor readings, and the **FloodTwin AI Prediction Engine**. 

Its primary purpose is to:
- Ingest and validate live water-level telemetry across urban zones.
- Interface with external meteorological services (Open-Meteo API) to collect real-time observed rainfall and multi-hour rainfall forecasts.
- Consolidate dynamic sensor data with static zone GIS attributes (elevation, drainage capacity, historical flood frequency) loaded from `app/data/zones.json`.
- Feed normalized feature vectors into the AI/ML module (`app/models/forecast.py`) to compute real-time risk scores (0–100), severity classifications (`low`, `moderate`, `high`, `severe`), and forward risk trajectories without modifying the core ML engine.
- Expose modular REST endpoints (`/iot/...`) for frontend dashboards, GIS digital twin layers, and backend orchestration services.

---

## 2. Core Application Files

The Data/IoT layer consists of five modular application files:

```
app/
├── api/
│   ├── iot_schemas.py           # Pydantic models for IoT telemetry, weather, and live status
│   └── iot_routes.py            # FastAPI REST endpoints for IoT operations
└── services/
    ├── weather_service.py       # Open-Meteo API client, 10-minute cache & offline fallback
    ├── sensor_service.py        # Thread-safe in-memory store for water-level telemetry
    └── integration_service.py   # Pipeline orchestrator combining data feeds with AI/ML inference
```

### 2.1. `app/api/iot_schemas.py`
Defines the Pydantic schemas and validation rules:
- `WaterLevelTelemetry`: Ingests individual sensor payloads (`zone_id`, `water_level_cm >= 0`, optional `sensor_id`, `timestamp`).
- `WaterLevelTelemetryResponse`: Confirmation response returning `status="recorded"`, `zone_id`, `water_level_cm`, and UTC timestamp.
- `BulkWaterLevelTelemetry`: Batch ingestion model accepting a non-empty list of `WaterLevelTelemetry`.
- `ZoneWeatherData`: Models 1h and 6h observed rainfall, hourly forecasts, and data provenance.
- `ZoneLiveStatusResponse`: Unified output per zone containing live rainfall, water level, risk score, severity level, and hourly forecast trajectory points.
- `WeatherSyncResponse`: Summarizes cache invalidation and external weather synchronizations.

### 2.2. `app/services/weather_service.py`
Connects to the Open-Meteo API and calculates precipitation metrics:
- Resolves geographical coordinates (`lat`, `lng`) for each zone from `app/data/zones.json`.
- `fetch_zone_weather(lat, lng)`: Queries Open-Meteo hourly precipitation, cached in memory for 10 minutes (`CACHE_TTL_SECONDS = 600`).
- `_generate_fallback_weather(lat, lng)`: Generates safe synthetic weather timelines if the machine is offline or the external API is unreachable.
- `get_live_rainfall(zone_id)`: Calculates `rainfall_mm_last_1h` (short burst) and `rainfall_mm_last_6h` (cumulative soil saturation).
- `get_rainfall_forecast(zone_id, hours=6)`: Extracts a list of future hourly rainfall values (in mm) for the next 1–6 hours.

### 2.3. `app/services/sensor_service.py`
Manages real-time water-level telemetry:
- Maintains a thread-safe in-memory cache (`_water_level_store`) keyed by `zone_id`.
- Enforces validation: `zone_id` existence against `zones.json`, non-negative water level, and physical sensor range ceilings (<= 10,000 cm).
- `record_water_level(telemetry)` & `record_bulk_water_level(bulk)`: Ingests and stores sensor readings.
- `get_latest_water_level(zone_id, default=15.0)`: Retrieves latest reading with a default baseline fallback (`15.0 cm`) so downstream models never encounter `None` values.
- `get_water_level_record(zone_id)` & `get_all_water_levels()`: Retrieves full telemetry metadata or a complete dictionary of all 12 zones.

### 2.4. `app/services/integration_service.py`
Central coordinator connecting data feeds to AI/ML prediction functions:
- `prepare_zone_prediction_input(zone_id)`: Assembles `rainfall_mm_last_1h`, `rainfall_mm_last_6h`, `water_level_cm`, `drainage_capacity`, `elevation_m`, and `historical_flood_frequency`.
- `get_zone_live_assessment(zone_id, forecast_hours=6)`: Calls `predict_risk_score(...)` and `forecast_risk_trajectory(...)` from `app.models.forecast`, packaging results into `ZoneLiveStatusResponse`.
- `get_all_zones_live_assessment(forecast_hours=6)`: Iterates across all 12 zones with isolated error boundaries.

### 2.5. `app/api/iot_routes.py`
Exposes REST endpoints on the `APIRouter(prefix="/iot", tags=["Data/IoT Integration"])`.

---

## 3. Data Flow Architecture

```
[ External Open-Meteo API ]      [ Ultrasonic / Water Level Sensors ]
            │                                    │
            ▼ (HTTP GET / Cache)                 ▼ (HTTP POST / Telemetry)
   weather_service.py                   sensor_service.py
  (1h burst, 6h cumulative,           (Thread-safe in-memory store
   1-6h future forecast)               with 15cm baseline fallback)
            │                                    │
            └───────────────┬────────────────────┘
                            │
                            ▼
                  integration_service.py
               (Merges with zones.json metadata)
                            │
                            ▼
              ┌───────────────────────────┐
              │ app/models/forecast.py    │
              │ • predict_risk_score()    │
              │ • forecast_risk_trajectory│
              └─────────────┬─────────────┘
                            │
                            ▼
                 app/api/iot_routes.py
   (GET /iot/live-assessment/{zone_id}, GET /iot/live-overview)
                            │
                            ▼
           [ Dashboard / GIS Digital Twin / Backend ]
```

---

## 4. Available IoT API Endpoints

| Method | Endpoint | Description | Input Payload / Parameters | Response Model |
|---|---|---|---|---|
| `POST` | `/iot/telemetry/water-level` | Ingests a single water-level reading from a sensor or gateway | `WaterLevelTelemetry` JSON | `WaterLevelTelemetryResponse` |
| `POST` | `/iot/telemetry/water-level/bulk` | Ingests batch water-level readings across multiple zones | `BulkWaterLevelTelemetry` JSON | `List[WaterLevelTelemetryResponse]` |
| `GET` | `/iot/water-level/{zone_id}` | Returns latest recorded water level and sensor metadata | Path: `zone_id` (e.g. `Z001`) | JSON metadata object |
| `GET` | `/iot/water-level` | Returns latest water level (cm) for all 12 zones | None | `Dict[str, float]` |
| `GET` | `/iot/live-assessment/{zone_id}` | Combines live weather, water level & AI risk predictions | Path: `zone_id`, Query: `forecast_hours` (1–24, default 6) | `ZoneLiveStatusResponse` |
| `GET` | `/iot/live-overview` | Comprehensive real-time status across all 12 zones for GIS maps | Query: `forecast_hours` (1–24, default 6) | `List[ZoneLiveStatusResponse]` |
| `POST` | `/iot/sync-weather` | Clears cache and forces sync with Open-Meteo API | None | `WeatherSyncResponse` |

---

## 5. Integration Tests and Mocking

The test suite is located in `tests/test_iot_integration.py` and contains **25 test cases**:

1. **Telemetry Validation (5 tests)**: Verifies Pydantic schema validation, negative value rejections (HTTP 422), unknown zone rejection (HTTP 404), and physical sanity thresholds.
2. **Sensor Service Storage (4 tests)**: Tests baseline fallback (`15.0 cm`), reading updates, bulk updates, and store reset fixtures.
3. **Weather Service (3 tests)**: Tests JSON parsing, rolling window calculations (1h and 6h sums), and offline fallback behavior.
4. **Integration Service (4 tests)**: Tests end-to-end feature vector preparation, AI risk scoring, forecast trajectory simulation, and complete network outage safety.
5. **IoT API Routes (9 tests)**: Tests all endpoints using FastAPI's `TestClient`.

### External Call Isolation
All external HTTP requests to Open-Meteo are mocked using `unittest.mock.patch("urllib.request.urlopen")`. Tests run deterministically with zero external network traffic or third-party dependencies.

---

## 6. How Team Members Can Use and Extend This Layer

### 6.1. Registering the Routes in Main Application
To expose the `/iot/...` endpoints in the running FastAPI application, add one line to `app/main.py`:
```python
from app.api.iot_routes import router as iot_router

app.include_router(iot_router)
```

### 6.2. Consuming Integrated Data in Backend / Frontend
- **Backend (Member 5)**: Query `GET /iot/live-assessment/{zone_id}` or `GET /iot/live-overview` to receive fully processed risk metrics and forecasts.
- **GIS / Digital Twin (Members 2 & 3)**: Use `GET /iot/live-overview` to color-code risk heatmaps across zones.

### 6.3. Extending with Real Sensors or MQTT
- Replace the in-memory dictionary in `app/services/sensor_service.py` with a persistent database (e.g. TimescaleDB, PostgreSQL) or an MQTT subscriber client (e.g. `paho-mqtt`).
- Hardware gateways can directly POST telemetry to `POST /iot/telemetry/water-level`.

---

## 7. Current Limitations

1. **No Physical Hardware Connected**: In-memory prototype store without active serial/LoRaWAN/MQTT physical connections.
2. **In-Memory Volatility**: Sensor readings reset on application restart (mitigated by default baseline water levels).
3. **Weather API Network Dependency**: Uses Open-Meteo public endpoints with automatic fallback to synthetic series when offline.
4. **Routes Not Yet Mounted in `app/main.py`**: The `iot_routes` router is modular and ready to be mounted via `app.include_router(iot_router)` when the team integrates.
