import os
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.api.schemas import (
    RiskScoreRequest,
    RiskScoreResponse,
    ForecastRequest,
    ForecastResponse,
    ForecastPoint,
    ZoneInfo,
    HealthResponse,
)
from app.data.synthetic_data import load_zones
from app.models.forecast import (
    predict_risk_score,
    forecast_risk_trajectory,
    risk_level_from_score,
)
from app.models.train import MODEL_PATH

router = APIRouter()


def _get_zone_or_404(zone_id: str) -> dict:
    zones = load_zones()
    for zone in zones:
        if zone["zone_id"] == zone_id:
            return zone
    raise HTTPException(status_code=404, detail=f"Zone '{zone_id}' not found")


@router.post("/predict/risk-score", response_model=RiskScoreResponse, tags=["Prediction"])
def predict_risk(payload: RiskScoreRequest):
    zone = _get_zone_or_404(payload.zone_id)

    score = predict_risk_score(
        rainfall_mm_last_1h=payload.rainfall_mm_last_1h,
        rainfall_mm_last_6h=payload.rainfall_mm_last_6h,
        water_level_cm=payload.water_level_cm,
        drainage_capacity=zone["drainage_capacity"],
        elevation_m=zone["elevation_m"],
        historical_flood_frequency=zone["historical_flood_frequency"],
    )

    return RiskScoreResponse(
        zone_id=payload.zone_id,
        risk_score=round(score, 2),
        risk_level=risk_level_from_score(score),
        timestamp=datetime.now(timezone.utc),
    )


@router.post("/predict/forecast", response_model=ForecastResponse, tags=["Prediction"])
def predict_forecast(payload: ForecastRequest):
    zone = _get_zone_or_404(payload.zone_id)

    trajectory = forecast_risk_trajectory(
        zone=zone,
        rainfall_forecast_mm=payload.rainfall_forecast_mm,
        current_water_level_cm=payload.current_water_level_cm,
    )

    return ForecastResponse(
        zone_id=payload.zone_id,
        forecast=[ForecastPoint(**point) for point in trajectory],
    )


@router.get("/zones", response_model=list[ZoneInfo], tags=["Zones"])
def get_zones():
    zones = load_zones()
    return [ZoneInfo(**z) for z in zones]


@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check():
    return HealthResponse(status="ok", model_loaded=os.path.exists(MODEL_PATH))
