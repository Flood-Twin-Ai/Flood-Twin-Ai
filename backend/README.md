# Jal-Drishti Backend

Jal-Drishti is a modular FastAPI backend for Pune urban-flood nowcasting and dynamic emergency response. It implements the documented **observe → predict → simulate → act** loop with deterministic demo data, a database-backed model, GeoJSON map contracts, risk-aware routing, shelter recommendations, resource dispatch, explainable alerts, and idempotent simulation jobs.

## What is included

| Area | Implementation |
|---|---|
| Identity | Email/password registration, bcrypt password hashes, short-lived JWT access tokens, rotating hashed refresh tokens, RBAC |
| Rainfall | Validated observation ingestion and live/replay/what-if scenario records |
| Nowcast | 30/60/120-minute deterministic baseline model with probability, severity, confidence, and reason codes |
| Flood coupling | Rainfall intensity, terrain susceptibility, drainage adjustment, and road-edge propagation |
| Maps | Frontend-ready risk-cell and road-edge GeoJSON with run/model/timestamp metadata |
| Routing | Dynamic risk-weighted Dijkstra/A* style graph search with blocked-edge rules and safety status |
| Decisions | Shelter ranking, resource dispatch, alert generation, acknowledgement, and audit records |
| Operations | Job records, input-hash idempotency, health/freshness endpoint, Docker Compose, migration marker |

The baseline inference engine is deliberately deterministic for the Pune demonstration. It is isolated behind `run_nowcast` so a calibrated XGBoost/Random Forest adapter can replace it without changing API contracts.

## Run locally

```bash
cd jal-drishti-backend
python3 -m pip install -e .
python3 -m scripts.seed_demo
uvicorn app.main:app --reload
```

The API is available at `http://localhost:8000`, OpenAPI documentation at `/docs`, and the health/freshness contract at `/health`.

The local default database is SQLite for zero-dependency demos. Set `DATABASE_URL` to a PostgreSQL/PostGIS URL for staging or production. Docker Compose provisions PostgreSQL/PostGIS and Redis:

```bash
docker compose up --build
```

The demo administrator is created by `scripts/seed_demo.py` with `admin@jaldrishti.local` and `Admin@12345`. Change this credential before any shared deployment.

## Demonstration sequence

1. Authenticate with `POST /api/v1/auth/login`.
2. Create a what-if rainfall input with `POST /api/v1/data/rainfall/scenarios`.
3. Generate a 30, 60, or 120-minute run with `POST /api/v1/nowcasts`.
4. Render changed cells from `GET /api/v1/map/risk?run_id=...` and unsafe road segments from `GET /api/v1/map/roads?run_id=...`.
5. Submit `POST /api/v1/routes` with origin, destination, and `run_id`; the response explicitly returns `route_status`, exposure, blocked edges, travel time, geometry, and explanation.
6. Rank destinations through `GET /api/v1/shelters/recommendations?latitude=...&longitude=...&run_id=...`.
7. Review and acknowledge explainable alerts with `GET /api/v1/alerts` and `POST /api/v1/alerts/{id}/acknowledge`.
8. Run the rainfall-slider workflow through `POST /api/v1/simulations`, then poll `/api/v1/jobs/{job_id}` or `/api/v1/simulations/{simulation_id}`.

## Safety and operational behavior

The API never treats a probability as a certainty. Every risk output includes confidence and reason codes. Routes exclude edges above the configured blocking threshold unless explicitly overridden by a responder, and the response distinguishes `safe`, `caution`, `unsafe`, and `insufficient_data`. Privileged dispatch and alert mutations create audit records. Provider integrations can be added later through the same validated observation and scenario contracts; synthetic scenarios keep the demo functional when feeds are unavailable.

## Tests

```bash
pytest -q
```

The included tests cover severity bands, deterministic rainfall sensitivity, database initialization, and the health response envelope. Extend the integration suite with a PostGIS service for CRS, geometry-validity, and spatial-index tests before production deployment.

## API groups

| Prefix | Purpose |
|---|---|
| `/api/v1/auth` | Register, login, refresh, logout |
| `/api/v1/users` | Current user and admin listing |
| `/api/v1/data` | Rainfall observations and scenarios |
| `/api/v1/nowcasts` | Forecast runs and cell outputs |
| `/api/v1/simulations` and `/api/v1/jobs` | What-if processing and job polling |
| `/api/v1/map` | Risk, roads, and metadata GeoJSON |
| `/api/v1/routes` | Risk-aware route computation |
| `/api/v1/shelters` | Shelter inventory and recommendations |
| `/api/v1/resources` | Resource inventory and responder dispatch |
| `/api/v1/alerts` | Explainable alerts and acknowledgement |

## Project layout

```text
app/
  main.py                 FastAPI application and versioned routes
  services.py             Demo data, nowcast, propagation, alerts, simulation
  core/                   Configuration and security
  db/                     SQLAlchemy database and entities
  api/v1/schemas.py       Pydantic contracts
  workers/worker.py       Worker process entry point
migrations/001_initial.sql
scripts/seed_demo.py
tests/
Dockerfile
docker-compose.yml
```
