# FloodTwin AI — Prediction Engine (Member 1: AI/ML)

FastAPI microservice that predicts urban flood risk scores and short-term
(1–6h) forecasts per zone. This is the AI/ML module in the FloodTwin AI
pipeline: **Data Collection → AI Prediction → Digital Twin → Simulation →
Risk Assessment → Route Optimization → Dashboard**.

It's built to run fully offline with synthetic training data, so nothing
here blocks on Member 6 wiring up real sensors — swap `synthetic_data.py`'s
role later without touching the API contract, and Backend/Frontend can
integrate against this today.

## Setup

```bash
cd floodtwin-ai-engine
pip install -r requirements.txt

# Train the model (creates app/models/risk_model.pkl)
python train_and_save_model.py

# Run the server
uvicorn app.main:app --reload
```

Server runs at `http://localhost:8000`. Interactive docs at
`http://localhost:8000/docs`.

## Retraining

Just re-run `python train_and_save_model.py`. It regenerates 5,000 rows of
synthetic data and retrains from scratch — takes a few seconds.

To use real sensor data instead of synthetic data, replace the call in
`app/models/train.py` (`generate_training_data`) with your real dataset,
keeping the same column names: `rainfall_mm_last_1h`, `rainfall_mm_last_6h`,
`water_level_cm`, `drainage_capacity`, `elevation_m`,
`historical_flood_frequency`, `risk_score`.

## API Contract

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/predict/risk-score` | Real-time risk score (0–100) for one zone |
| POST | `/predict/forecast` | Risk trajectory for next N hours for one zone |
| GET | `/zones` | Static metadata for all zones (for GIS/dashboard) |
| GET | `/health` | Health check |

### POST /predict/risk-score

Request:
```json
{
  "zone_id": "Z001",
  "rainfall_mm_last_1h": 35.0,
  "rainfall_mm_last_6h": 80.0,
  "water_level_cm": 120.0
}
```

Response:
```json
{
  "zone_id": "Z001",
  "risk_score": 62.4,
  "risk_level": "high",
  "timestamp": "2026-08-24T10:15:00Z"
}
```

`risk_level` buckets: `low` (0–25), `moderate` (26–50), `high` (51–75),
`severe` (76–100).

### POST /predict/forecast

Request:
```json
{
  "zone_id": "Z001",
  "rainfall_forecast_mm": [15, 25, 40, 30, 10, 5],
  "current_water_level_cm": 70.0
}
```
Each element in `rainfall_forecast_mm` is forecasted rainfall (mm) for the
next hour, in order (index 0 = next 1h, index 1 = the hour after, etc).
This forecast normally comes from a weather API (Member 6's job) — for
local testing you can pass any array.

Response:
```json
{
  "zone_id": "Z001",
  "forecast": [
    { "hours_ahead": 1, "predicted_risk_score": 56.9, "risk_level": "high" },
    { "hours_ahead": 2, "predicted_risk_score": 67.0, "risk_level": "high" }
  ]
}
```

### GET /zones

Returns all zone metadata (id, name, lat/lng, elevation, drainage capacity,
historical flood frequency). This is what the GIS/Digital Twin module
(Member 2) should pull to render the base map.

### GET /health

```json
{ "status": "ok", "model_loaded": true }
```

## Error handling

- Unknown `zone_id` → `404` with `{"detail": "Zone '...' not found"}`
- Negative rainfall/water-level values → `422` with validation detail

## Model

RandomForestRegressor (scikit-learn), trained on 5,000 synthetic rows.
Current run: **MAE ≈ 4.8, R² ≈ 0.94** on held-out test data. Feature
importances (highest first): `rainfall_mm_last_1h`, `rainfall_mm_last_6h`,
`historical_flood_frequency`, `elevation_m`, `drainage_capacity`,
`water_level_cm` — matches physical intuition (short-burst rainfall
dominates near-term risk).

## Project structure

```
floodtwin-ai-engine/
├── app/
│   ├── main.py                 # FastAPI app entrypoint
│   ├── data/
│   │   ├── synthetic_data.py   # synthetic training data generator
│   │   └── zones.json          # 12 mock urban zones
│   ├── models/
│   │   ├── train.py            # trains + saves RandomForest model
│   │   ├── forecast.py         # prediction + forecast logic
│   │   └── risk_model.pkl      # trained model (generated)
│   ├── api/
│   │   ├── routes.py
│   │   └── schemas.py
│   └── core/
│       └── config.py
├── requirements.txt
├── train_and_save_model.py
└── README.md
```

## Next steps / integration notes for the team

- **Member 5 (Backend):** call this service directly from your API layer,
  or reverse-proxy it. Response schemas are stable and documented above.
- **Member 6 (Data/IoT):** once real rainfall/water-level sensors or a
  weather API are wired up, swap the request source feeding
  `/predict/risk-score` and `/predict/forecast` — no contract changes needed.
- **Member 2/3 (GIS/Simulation):** `/zones` gives you the static layer;
  call `/predict/risk-score` per zone to color your heatmap/simulation.
