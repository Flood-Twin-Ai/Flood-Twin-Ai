from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator

from app.api.schemas import ForecastPoint


class WaterLevelTelemetry(BaseModel):
    """Payload sent by an ultrasonic/gauge water-level IoT sensor or gateway."""

    zone_id: str = Field(..., examples=["Z001"], description="Unique identifier of the urban zone")
    water_level_cm: float = Field(..., ge=0, examples=[85.5], description="Current water level in centimeters")
    sensor_id: Optional[str] = Field(None, examples=["WL-101"], description="Optional hardware sensor identifier")
    timestamp: Optional[datetime] = Field(
        default=None,
        description="Sensor reading timestamp (UTC). Defaults to server receipt time if omitted.",
    )

    @field_validator("water_level_cm")
    @classmethod
    def non_negative_water_level(cls, v: float) -> float:
        if v < 0:
            raise ValueError("water_level_cm must be non-negative")
        return v


class WaterLevelTelemetryResponse(BaseModel):
    """Response confirming receipt and processing of water-level telemetry."""

    status: str = Field(..., examples=["recorded"])
    zone_id: str = Field(..., examples=["Z001"])
    water_level_cm: float = Field(..., examples=[85.5])
    sensor_id: Optional[str] = Field(None, examples=["WL-101"])
    recorded_at: datetime


class BulkWaterLevelTelemetry(BaseModel):
    """Payload for batch telemetry updates across multiple sensors/zones."""

    readings: List[WaterLevelTelemetry] = Field(..., description="List of water level readings")

    @field_validator("readings")
    @classmethod
    def non_empty_readings(cls, v: List[WaterLevelTelemetry]) -> List[WaterLevelTelemetry]:
        if len(v) == 0:
            raise ValueError("readings list must not be empty")
        return v


class ZoneWeatherData(BaseModel):
    """Observed and forecasted weather parameters for a specific zone."""

    zone_id: str = Field(..., examples=["Z001"])
    rainfall_mm_last_1h: float = Field(..., ge=0, examples=[25.0])
    rainfall_mm_last_6h: float = Field(..., ge=0, examples=[65.0])
    rainfall_forecast_mm: List[float] = Field(
        default_factory=list,
        examples=[[10.0, 15.0, 25.0, 20.0, 5.0, 0.0]],
        description="Hourly rainfall forecast for the next 1-6 hours (mm)",
    )
    source: str = Field(default="open-meteo", examples=["open-meteo", "sensor", "simulated"])
    last_updated: datetime


class ZoneLiveStatusResponse(BaseModel):
    """
    Unified real-time operational status for a single zone.
    Combines live IoT sensor data, weather data, and AI/ML model risk predictions.
    """

    zone_id: str = Field(..., examples=["Z001"])
    zone_name: str = Field(..., examples=["Riverside Colony"])
    rainfall_mm_last_1h: float = Field(..., ge=0, examples=[35.0])
    rainfall_mm_last_6h: float = Field(..., ge=0, examples=[80.0])
    water_level_cm: float = Field(..., ge=0, examples=[120.0])
    risk_score: float = Field(..., ge=0, le=100, examples=[62.4])
    risk_level: Literal["low", "moderate", "high", "severe"] = Field(..., examples=["high"])
    rainfall_forecast_mm: List[float] = Field(default_factory=list, examples=[[15.0, 25.0, 40.0]])
    forecast_trajectory: List[ForecastPoint] = Field(default_factory=list)
    timestamp: datetime


class WeatherSyncResponse(BaseModel):
    """Response returned when weather data is fetched and synchronized with external APIs."""

    status: str = Field(..., examples=["ok"])
    synced_zones_count: int = Field(..., examples=[12])
    source: str = Field(..., examples=["open-meteo"])
    synced_at: datetime
