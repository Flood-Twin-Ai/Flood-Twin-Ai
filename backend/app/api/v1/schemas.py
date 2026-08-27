from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

class Envelope(BaseModel):
    data: Any
    meta: dict = {}
    errors: list = []

class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=255)

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class ObservationIn(BaseModel):
    source_id: str | None = None
    source_event_id: str | None = None
    observed_at: datetime
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    intensity_mm_hr: float = Field(ge=0, le=1000)
    accumulation_mm: float = Field(default=0, ge=0)
    quality_flag: Literal["valid", "suspect", "quarantined"] = "valid"

class ScenarioIn(BaseModel):
    scenario_type: Literal["live", "replay", "what_if"] = "what_if"
    intensity_mm_hr: float = Field(default=30, ge=0, le=1000)
    multiplier: float = Field(default=1, ge=0, le=20)
    duration_min: int = Field(default=60, ge=1, le=720)
    affected_area: dict | None = None
    drainage_adjustment: float = Field(default=0, ge=-1, le=1)

class NowcastIn(BaseModel):
    scenario_id: str | None = None
    horizon_min: Literal[30, 60, 120] = 60

class SimulationIn(ScenarioIn):
    baseline_run_id: str | None = None
    horizons: list[Literal[30, 60, 120]] = [30, 60, 120]

class Point(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

class RouteIn(BaseModel):
    origin: Point
    destination: Point
    run_id: str | None = None
    risk_penalty: float = Field(default=4, ge=0, le=100)
    allow_blocked: bool = False

class DispatchIn(BaseModel):
    resource_id: str
    alert_id: str | None = None
    priority: int = Field(ge=1, le=5)
    assigned_to: str | None = None

class RoleUpdate(BaseModel):
    roles: list[str]

class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    email: str
    full_name: str
    status: str
    roles: list[str] = []

class ErrorResponse(BaseModel):
    data: None = None
    meta: dict = {}
    errors: list[dict]
