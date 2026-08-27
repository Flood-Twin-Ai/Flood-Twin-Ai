import hashlib, math
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.config import get_settings
from app.db.models import (ForecastRun, RiskCell, RoadEdge, RoadEdgeRisk, Shelter, Resource,
                           Alert, JobRun, RainfallScenario, uid)

PUNE_CELLS = [
    ("pune-central", 18.5204, 73.8567, 0.80), ("shivajinagar", 18.5308, 73.8470, 0.75),
    ("yerwada", 18.5514, 73.8790, 0.68), ("kharadi", 18.5511, 73.9388, 0.62),
    ("hadapsar", 18.5089, 73.9260, 0.58), ("swargate", 18.5018, 73.8636, 0.73),
    ("kothrud", 18.5074, 73.8077, 0.48), ("baner", 18.5590, 73.7868, 0.40),
]

def severity(p: float) -> str:
    return "critical" if p >= .8 else "high" if p >= .6 else "moderate" if p >= .35 else "low"

def point_geo(lat: float, lon: float) -> dict:
    return {"type": "Point", "coordinates": [lon, lat]}

def line_geo(points: list[tuple[float, float]]) -> dict:
    return {"type": "LineString", "coordinates": [[lon, lat] for lat, lon in points]}

def distance(a: tuple[float, float], b: tuple[float, float]) -> float:
    return math.hypot((a[0]-b[0])*111, (a[1]-b[1])*105)

def ensure_demo_data(db: Session):
    if db.scalar(select(RoadEdge.id).limit(1)):
        return
    roads = [("central-shiv", "pune-central", "shivajinagar", 1800, 35),
             ("central-swargate", "pune-central", "swargate", 1500, 30),
             ("central-kharadi", "pune-central", "kharadi", 7800, 45),
             ("kharadi-hadapsar", "kharadi", "hadapsar", 5000, 40),
             ("shiv-kothrud", "shivajinagar", "kothrud", 5000, 40),
             ("kothrud-baner", "kothrud", "baner", 4500, 40),
             ("shiv-yerwada", "shivajinagar", "yerwada", 3000, 35),
             ("yerwada-kharadi", "yerwada", "kharadi", 5500, 40)]
    coords = {c[0]: (c[1], c[2]) for c in PUNE_CELLS}
    for osm, a, b, length, speed in roads:
        db.add(RoadEdge(osm_id=osm, from_node=a, to_node=b, length_m=length,
                        base_speed_kph=speed, road_class="primary",
                        geometry=line_geo([coords[a], coords[b]])))
    shelters = [("Pune University Relief Centre", "baner", 500, True),
                ("Kothrud Community Hall", "kothrud", 300, True),
                ("Hadapsar Sports Complex", "hadapsar", 800, False)]
    for name, cell, capacity, accessible in shelters:
        lat, lon, _ = next((x[1:] for x in PUNE_CELLS if x[0] == cell))
        db.add(Shelter(name=name, latitude=lat, longitude=lon, capacity=capacity,
                       available_capacity=capacity, accessibility=accessible))
    for typ, cell, qty in [("ambulance", "swargate", 4), ("pump", "kharadi", 3), ("rescue_team", "shivajinagar", 2)]:
        lat, lon, _ = next((x[1:] for x in PUNE_CELLS if x[0] == cell))
        db.add(Resource(resource_type=typ, quantity=qty, available=qty, latitude=lat,
                        longitude=lon, owner="Pune Emergency Operations Centre"))
    db.commit()

def run_nowcast(db: Session, scenario_id: str | None, horizon: int, intensity: float | None = None, adjustment: float = 0):
    ensure_demo_data(db)
    if scenario_id:
        scenario = db.get(RainfallScenario, scenario_id)
        params = scenario.parameters if scenario else {}
    else:
        params = {}
    rain = intensity if intensity is not None else float(params.get("intensity_mm_hr", 30)) * float(params.get("multiplier", 1))
    run = ForecastRun(scenario_id=scenario_id, model_version=get_settings().model_version, horizon_min=horizon, status="completed")
    db.add(run); db.flush()
    cells = []
    for cell_id, lat, lon, susceptibility in PUNE_CELLS:
        local = min(1, rain / 100 * susceptibility * (1 + horizon / 240))
        drainage_relief = adjustment * .25
        p = max(0, min(1, local - drainage_relief))
        reasons = ["high_recent_rainfall"] if rain >= 50 else ["moderate_recent_rainfall"]
        if susceptibility >= .7: reasons.append("low_elevation")
        if adjustment < -.2: reasons.append("drainage_capacity_exceeded")
        cells.append(RiskCell(run_id=run.id, cell_id=cell_id, latitude=lat, longitude=lon,
                              probability=round(p, 4), severity=severity(p),
                              confidence=round(max(.45, .9 - (rain / 250)), 3), explanation=reasons))
    db.add_all(cells); db.flush()
    risk_by_cell = {c.cell_id: c for c in cells}
    for edge in db.scalars(select(RoadEdge)).all():
        linked = [risk_by_cell.get(edge.from_node), risk_by_cell.get(edge.to_node)]
        score = max((c.probability for c in linked if c), default=0)
        db.add(RoadEdgeRisk(run_id=run.id, edge_id=edge.id, risk_score=score,
                            blocked=score >= get_settings().risk_block_threshold,
                            expected_delay_min=round(score * 30, 2)))
    run.summary = {"cell_count": len(cells), "max_probability": max(c.probability for c in cells), "rainfall_mm_hr": rain}
    db.commit()
    create_alerts(db, run.id, cells)
    return run

def create_alerts(db: Session, run_id: str, cells: list[RiskCell]):
    for c in cells:
        if c.probability >= .6:
            exists = db.scalar(select(Alert).where(Alert.run_id == run_id, Alert.latitude == c.latitude, Alert.longitude == c.longitude))
            if not exists:
                db.add(Alert(run_id=run_id, severity=c.severity, alert_type="flood_risk",
                    cause="; ".join(c.explanation), recommendation="Avoid low-lying roads and move to the nearest viable shelter.",
                    confidence=c.confidence, latitude=c.latitude, longitude=c.longitude))
    db.commit()

def input_hash(payload: dict) -> str:
    return hashlib.sha256(repr(sorted(payload.items())).encode()).hexdigest()

def run_simulation(db: Session, payload: dict):
    scenario = RainfallScenario(scenario_type="what_if", parameters=payload, status="completed")
    db.add(scenario); db.flush()
    outputs = []
    for horizon in payload.get("horizons", [30, 60, 120]):
        run = run_nowcast(db, scenario.id, horizon, payload.get("intensity_mm_hr", 30) * payload.get("multiplier", 1), payload.get("drainage_adjustment", 0))
        outputs.append({"horizon_min": horizon, "run_id": run.id, **run.summary})
    scenario.status = "completed"; db.commit()
    return scenario, outputs
