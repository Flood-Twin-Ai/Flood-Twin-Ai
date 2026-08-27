from datetime import datetime
from uuid import uuid4
from sqlalchemy import String, Float, Integer, Boolean, DateTime, ForeignKey, Text, JSON, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base, utcnow


def uid() -> str:
    return str(uuid4())

class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    roles: Mapped[list["UserRole"]] = relationship(cascade="all, delete-orphan")

class UserRole(Base):
    __tablename__ = "user_roles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role_name: Mapped[str] = mapped_column(String(40), index=True)

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class RainfallObservation(Base):
    __tablename__ = "rainfall_observations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    source_id: Mapped[str | None] = mapped_column(String(36), index=True)
    source_event_id: Mapped[str | None] = mapped_column(String(255), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    intensity_mm_hr: Mapped[float] = mapped_column(Float)
    accumulation_mm: Mapped[float] = mapped_column(Float, default=0)
    quality_flag: Mapped[str] = mapped_column(String(30), default="valid")

class RainfallScenario(Base):
    __tablename__ = "rainfall_scenarios"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    scenario_type: Mapped[str] = mapped_column(String(30), index=True)
    created_by: Mapped[str | None] = mapped_column(String(36))
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="created")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class ForecastRun(Base):
    __tablename__ = "forecast_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    scenario_id: Mapped[str | None] = mapped_column(ForeignKey("rainfall_scenarios.id"), index=True)
    model_version: Mapped[str] = mapped_column(String(80))
    horizon_min: Mapped[int] = mapped_column(Integer, index=True)
    status: Mapped[str] = mapped_column(String(30), default="completed", index=True)
    data_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)

class RiskCell(Base):
    __tablename__ = "risk_cells"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    run_id: Mapped[str] = mapped_column(ForeignKey("forecast_runs.id", ondelete="CASCADE"), index=True)
    cell_id: Mapped[str] = mapped_column(String(80), index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    probability: Mapped[float] = mapped_column(Float)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    confidence: Mapped[float] = mapped_column(Float)
    explanation: Mapped[list] = mapped_column(JSON, default=list)

class RoadEdge(Base):
    __tablename__ = "road_edges"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    osm_id: Mapped[str] = mapped_column(String(100), unique=True)
    from_node: Mapped[str] = mapped_column(String(80))
    to_node: Mapped[str] = mapped_column(String(80))
    length_m: Mapped[float] = mapped_column(Float)
    base_speed_kph: Mapped[float] = mapped_column(Float)
    road_class: Mapped[str] = mapped_column(String(50))
    geometry: Mapped[dict] = mapped_column(JSON)

class RoadEdgeRisk(Base):
    __tablename__ = "road_edge_risk"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    run_id: Mapped[str] = mapped_column(ForeignKey("forecast_runs.id", ondelete="CASCADE"), index=True)
    edge_id: Mapped[str] = mapped_column(ForeignKey("road_edges.id"), index=True)
    risk_score: Mapped[float] = mapped_column(Float)
    blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    expected_delay_min: Mapped[float] = mapped_column(Float, default=0)

class Shelter(Base):
    __tablename__ = "shelters"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    name: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    capacity: Mapped[int] = mapped_column(Integer)
    available_capacity: Mapped[int] = mapped_column(Integer)
    accessibility: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(30), default="open")

class Resource(Base):
    __tablename__ = "resources"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    resource_type: Mapped[str] = mapped_column(String(80), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    available: Mapped[int] = mapped_column(Integer)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    owner: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(30), default="available")

class EvacuationRoute(Base):
    __tablename__ = "evacuation_routes"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    run_id: Mapped[str | None] = mapped_column(String(36), index=True)
    origin: Mapped[dict] = mapped_column(JSON)
    destination: Mapped[dict] = mapped_column(JSON)
    geometry: Mapped[dict] = mapped_column(JSON)
    travel_time_sec: Mapped[float] = mapped_column(Float)
    risk_exposure: Mapped[float] = mapped_column(Float)
    route_status: Mapped[str] = mapped_column(String(30))
    blocked_edges: Mapped[list] = mapped_column(JSON, default=list)
    explanation: Mapped[list] = mapped_column(JSON, default=list)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    run_id: Mapped[str | None] = mapped_column(String(36), index=True)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    alert_type: Mapped[str] = mapped_column(String(80))
    cause: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(30), default="active", index=True)
    confidence: Mapped[float] = mapped_column(Float)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class JobRun(Base):
    __tablename__ = "job_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    job_type: Mapped[str] = mapped_column(String(80), index=True)
    input_hash: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(30), default="queued", index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    error: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    actor_id: Mapped[str | None] = mapped_column(String(36), index=True)
    action: Mapped[str] = mapped_column(String(120))
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[str | None] = mapped_column(String(36))
    before_json: Mapped[dict | None] = mapped_column(JSON)
    after_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

Index("ix_risk_run_cell", RiskCell.run_id, RiskCell.cell_id, unique=True)
Index("ix_observation_source_time", RainfallObservation.source_id, RainfallObservation.observed_at)
Index("ix_job_idempotency", JobRun.job_type, JobRun.input_hash, unique=True)
