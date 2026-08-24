from datetime import datetime
from typing import List, Literal
from pydantic import BaseModel, Field, field_validator


class RiskScoreRequest(BaseModel):
    zone_id: str = Field(..., examples=["Z001"])
    rainfall_mm_last_1h: float = Field(..., ge=0, examples=[35.0])
    rainfall_mm_last_6h: float = Field(..., ge=0, examples=[80.0])
    water_level_cm: float = Field(..., ge=0, examples=[120.0])

    @field_validator("rainfall_mm_last_1h", "rainfall_mm_last_6h", "water_level_cm")
    @classmethod
    def non_negative(cls, v):
        if v < 0:
            raise ValueError("Value must be non-negative")
        return v


class RiskScoreResponse(BaseModel):
    zone_id: str
    risk_score: float
    risk_level: Literal["low", "moderate", "high", "severe"]
    timestamp: datetime


class ForecastRequest(BaseModel):
    zone_id: str = Field(..., examples=["Z001"])
    rainfall_forecast_mm: List[float] = Field(..., examples=[[10.0, 22.0, 35.0]])
    current_water_level_cm: float = Field(..., ge=0, examples=[90.0])

    @field_validator("rainfall_forecast_mm")
    @classmethod
    def non_negative_list(cls, v):
        if any(x < 0 for x in v):
            raise ValueError("Rainfall values must be non-negative")
        if len(v) == 0:
            raise ValueError("rainfall_forecast_mm must contain at least one value")
        return v


class ForecastPoint(BaseModel):
    hours_ahead: int
    predicted_risk_score: float
    risk_level: Literal["low", "moderate", "high", "severe"]


class ForecastResponse(BaseModel):
    zone_id: str
    forecast: List[ForecastPoint]


class ZoneInfo(BaseModel):
    zone_id: str
    name: str
    lat: float
    lng: float
    elevation_m: float
    drainage_capacity: float
    historical_flood_frequency: float


class HealthResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    status: str
    model_loaded: bool
