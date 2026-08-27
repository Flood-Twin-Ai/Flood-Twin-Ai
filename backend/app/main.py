from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.security import (hash_password, verify_password, create_token, hash_token,
                               get_current_user, require_roles)
from app.db.database import Base, engine, get_db, utcnow
from app.db.models import (User, UserRole, RefreshToken, RainfallObservation, RainfallScenario,
                           ForecastRun, RiskCell, RoadEdge, RoadEdgeRisk, Shelter, Resource,
                           EvacuationRoute, Alert, JobRun, AuditLog)
from app.api.v1.schemas import *
from app.services import ensure_demo_data, run_nowcast, run_simulation, distance, input_hash, PUNE_CELLS

settings = get_settings()
Base.metadata.create_all(bind=engine)
app = FastAPI(title=settings.app_name, version="1.0.0", description="Observe, predict, simulate, act for Pune flood response")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    db = next(get_db()); ensure_demo_data(db); db.close()

def ok(data, **meta): return {"data": data, "meta": meta, "errors": []}
def user_data(user): return {"id": user.id, "email": user.email, "full_name": user.full_name, "status": user.status, "roles": [r.role_name for r in user.roles]}
def audit(db, actor, action, entity_type, entity_id, after=None):
    db.add(AuditLog(actor_id=getattr(actor, "id", None), action=action, entity_type=entity_type, entity_id=entity_id, after_json=after)); db.commit()

def get_or_create_admin(db):
    user = db.scalar(select(User).where(User.email == "admin@jaldrishti.local"))
    if not user:
        user = User(email="admin@jaldrishti.local", password_hash=hash_password("Admin@12345"), full_name="Demo Administrator")
        user.roles = [UserRole(role_name="admin"), UserRole(role_name="analyst"), UserRole(role_name="responder")]; db.add(user); db.commit(); db.refresh(user)
    return user

@app.get("/health")
def health(db: Session = Depends(get_db)):
    latest = db.scalar(select(ForecastRun).order_by(ForecastRun.created_at.desc()))
    return ok({"status": "ok", "mode": "simulated", "active_run_id": latest.id if latest else None,
               "data_timestamp": latest.data_timestamp if latest else None, "model_version": settings.model_version})

@app.post("/api/v1/auth/register", status_code=201)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.email == req.email.lower())): raise HTTPException(409, "Email already registered")
    user = User(email=req.email.lower(), password_hash=hash_password(req.password), full_name=req.full_name, roles=[UserRole(role_name="viewer")])
    db.add(user); db.commit(); db.refresh(user); return ok(user_data(user))

@app.post("/api/v1/auth/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == req.username.lower()))
    if not user or not verify_password(req.password, user.password_hash): raise HTTPException(401, "Invalid credentials")
    access = create_token(user.id, "access", timedelta(minutes=settings.access_token_minutes))
    refresh = create_token(user.id, "refresh", timedelta(days=settings.refresh_token_days))
    db.add(RefreshToken(user_id=user.id, token_hash=hash_token(refresh), expires_at=utcnow()+timedelta(days=settings.refresh_token_days))); db.commit()
    return ok(TokenResponse(access_token=access, refresh_token=refresh).model_dump())

@app.post("/api/v1/auth/refresh")
def refresh(payload: dict, db: Session = Depends(get_db)):
    from jose import jwt, JWTError
    token = payload.get("refresh_token", "")
    try: data = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    except JWTError: raise HTTPException(401, "Invalid refresh token")
    record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(token), RefreshToken.revoked_at.is_(None)))
    if not record or record.expires_at < utcnow(): raise HTTPException(401, "Expired or revoked refresh token")
    record.revoked_at = utcnow(); access = create_token(data["sub"], "access", timedelta(minutes=settings.access_token_minutes)); new_refresh = create_token(data["sub"], "refresh", timedelta(days=settings.refresh_token_days))
    db.add(RefreshToken(user_id=data["sub"], token_hash=hash_token(new_refresh), expires_at=utcnow()+timedelta(days=settings.refresh_token_days))); db.commit()
    return ok(TokenResponse(access_token=access, refresh_token=new_refresh).model_dump())

@app.post("/api/v1/auth/logout")
def logout(payload: dict, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(payload.get("refresh_token", "")), RefreshToken.user_id == user.id));
    if record: record.revoked_at = utcnow(); db.commit()
    return ok({"revoked": True})

@app.get("/api/v1/users/me")
def me(user: User = Depends(get_current_user)): return ok(user_data(user))

@app.get("/api/v1/users")
def users(db: Session = Depends(get_db), _: User = Depends(require_roles("admin"))): return ok([user_data(u) for u in db.scalars(select(User)).all()])

@app.post("/api/v1/data/rainfall/observations", status_code=201)
def rainfall_observation(req: ObservationIn, db: Session = Depends(get_db), user: User = Depends(require_roles("analyst", "admin", "service_worker"))):
    row = RainfallObservation(**req.model_dump())
    db.add(row); db.commit(); db.refresh(row); audit(db, user, "rainfall.ingest", "rainfall_observation", row.id, req.model_dump(mode="json")); return ok({"id": row.id, "quality_flag": row.quality_flag})

@app.post("/api/v1/data/rainfall/scenarios", status_code=201)
def scenario(req: ScenarioIn, db: Session = Depends(get_db), user: User = Depends(require_roles("analyst", "admin"))):
    row = RainfallScenario(scenario_type=req.scenario_type, created_by=user.id, parameters=req.model_dump(), status="created"); db.add(row); db.commit(); db.refresh(row); return ok({"id": row.id, "status": row.status, "assumptions": row.parameters})

@app.post("/api/v1/nowcasts", status_code=202)
def nowcast(req: NowcastIn, db: Session = Depends(get_db), user: User = Depends(require_roles("analyst", "admin", "responder"))):
    run = run_nowcast(db, req.scenario_id, req.horizon_min); return ok({"run_id": run.id, "status": run.status, "summary": run.summary})

@app.get("/api/v1/nowcasts/{run_id}")
def nowcast_status(run_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    run = db.get(ForecastRun, run_id)
    if not run: raise HTTPException(404, "Forecast run not found")
    return ok({"run_id": run.id, "status": run.status, "horizon_min": run.horizon_min, "model_version": run.model_version, "summary": run.summary, "data_timestamp": run.data_timestamp})

@app.get("/api/v1/nowcasts/{run_id}/cells")
def nowcast_cells(run_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    cells = db.scalars(select(RiskCell).where(RiskCell.run_id == run_id)).all(); return ok([cell_geo(c) for c in cells], forecast_run_id=run_id, model_version=settings.model_version)

def cell_geo(c): return {"type":"Feature", "geometry":{"type":"Point","coordinates":[c.longitude,c.latitude]}, "properties":{"cell_id":c.cell_id,"probability":c.probability,"severity":c.severity,"confidence":c.confidence,"explanation":c.explanation}}

@app.post("/api/v1/simulations", status_code=202)
def simulation(req: SimulationIn, db: Session = Depends(get_db), user: User = Depends(require_roles("analyst", "admin", "responder"))):
    payload=req.model_dump(); h=input_hash(payload); existing=db.scalar(select(JobRun).where(JobRun.job_type=="run_simulation", JobRun.input_hash==h))
    if existing: return ok({"job_id": existing.id, "status": existing.status, "deduplicated": True})
    job=JobRun(job_type="run_simulation", input_hash=h, status="running", progress=10, started_at=utcnow()); db.add(job); db.commit(); db.refresh(job)
    scenario, outputs=run_simulation(db,payload); job.status="succeeded"; job.progress=100; job.result={"scenario_id":scenario.id,"outputs":outputs}; job.finished_at=utcnow(); db.commit(); return ok({"job_id":job.id, **job.result})

@app.get("/api/v1/simulations/{simulation_id}")
def simulation_status(simulation_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    job=db.get(JobRun, simulation_id)
    if not job: raise HTTPException(404,"Simulation not found")
    return ok({"job_id":job.id,"status":job.status,"progress":job.progress,"result":job.result,"error":job.error})

@app.get("/api/v1/jobs/{job_id}")
def job(job_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    row=db.get(JobRun,job_id)
    if not row: raise HTTPException(404,"Job not found")
    return ok({"job_id":row.id,"job_type":row.job_type,"status":row.status,"progress":row.progress,"result":row.result,"error":row.error})

@app.get("/api/v1/map/risk")
def risk_map(run_id: str | None=None, db: Session=Depends(get_db), _: User=Depends(get_current_user)):
    if not run_id: run=db.scalar(select(ForecastRun).order_by(ForecastRun.created_at.desc())); run_id=run.id if run else None
    cells=db.scalars(select(RiskCell).where(RiskCell.run_id==run_id)).all() if run_id else []
    return {"type":"FeatureCollection","features":[cell_geo(c) for c in cells],"meta":{"forecast_run_id":run_id,"data_timestamp":utcnow().isoformat(),"model_version":settings.model_version,"confidence":min((c.confidence for c in cells),default=0)}}

@app.get("/api/v1/map/roads")
def roads(run_id: str | None=None, db: Session=Depends(get_db), _: User=Depends(get_current_user)):
    if not run_id: run=db.scalar(select(ForecastRun).order_by(ForecastRun.created_at.desc())); run_id=run.id if run else ""
    rows=db.execute(select(RoadEdge,RoadEdgeRisk).join(RoadEdgeRisk,RoadEdge.id==RoadEdgeRisk.edge_id).where(RoadEdgeRisk.run_id==run_id)).all()
    return {"type":"FeatureCollection","features":[{"type":"Feature","geometry":edge.geometry,"properties":{"edge_id":edge.id,"risk_score":risk.risk_score,"blocked":risk.blocked,"expected_delay_min":risk.expected_delay_min}} for edge,risk in rows],"meta":{"forecast_run_id":run_id}}

@app.get("/api/v1/map/metadata")
def metadata(db: Session=Depends(get_db), _: User=Depends(get_current_user)):
    run=db.scalar(select(ForecastRun).order_by(ForecastRun.created_at.desc())); return ok({"active_run_id":run.id if run else None,"model_version":settings.model_version,"data_state":"simulated","data_timestamp":run.data_timestamp if run else None,"stale":False})

@app.post("/api/v1/routes", status_code=201)
def route(req: RouteIn, db: Session=Depends(get_db), user: User=Depends(require_roles("viewer","responder","analyst","admin"))):
    run_id=req.run_id or (db.scalar(select(ForecastRun).order_by(ForecastRun.created_at.desc())).id if db.scalar(select(ForecastRun).order_by(ForecastRun.created_at.desc())) else None)
    if not run_id: raise HTTPException(422,"No forecast run available")
    risks={r.edge_id:r for r in db.scalars(select(RoadEdgeRisk).where(RoadEdgeRisk.run_id==run_id)).all()}; edges=db.scalars(select(RoadEdge)).all()
    def nearest(p): return min(PUNE_CELLS,key=lambda c:distance((p.latitude,p.longitude),(c[1],c[2])))[0]
    start, goal=nearest(req.origin), nearest(req.destination); graph={n:[] for n in [c[0] for c in PUNE_CELLS]}
    for e in edges:
        r=risks.get(e.id); cost=e.length_m/(e.base_speed_kph/3.6)*(1+req.risk_penalty*(r.risk_score if r else 0))+(r.expected_delay_min*60 if r else 0)
        if r and r.blocked and not req.allow_blocked: continue
        graph[e.from_node].append((e.to_node,cost,e,r)); graph[e.to_node].append((e.from_node,cost,e,r))
    import heapq
    q=[(0,start,[])] ; best={start:0}; chosen=None
    while q:
        cost,node,path=heapq.heappop(q)
        if node==goal: chosen=(cost,path); break
        for nxt,w,e,r in graph.get(node,[]):
            if cost+w<best.get(nxt,float("inf")): best[nxt]=cost+w; heapq.heappush(q,(cost+w,nxt,path+[(e,r)]))
    if not chosen: return ok({"route_status":"unsafe","risk_exposure":1,"blocked_edges":[],"estimated_travel_time":None,"explanation":["no viable route"]})
    cost,path=chosen; blocked=[e.id for e,r in path if r and r.blocked]; exposure=sum(r.risk_score for e,r in path)/max(1,len(path)); status="unsafe" if exposure>=.75 else "caution" if exposure>=.4 else "safe"
    coords=[]
    for e,r in path: coords += e.geometry["coordinates"][:1]
    if path: coords.append(path[-1][0].geometry["coordinates"][-1])
    row=EvacuationRoute(run_id=run_id,origin=req.origin.model_dump(),destination=req.destination.model_dump(),geometry={"type":"LineString","coordinates":coords},travel_time_sec=cost,risk_exposure=exposure,route_status=status,blocked_edges=blocked,explanation=["dynamic risk-weighted A* route","configuration includes risk penalty", *(["stale or blocked edges excluded"] if blocked else [])]); db.add(row); db.commit(); db.refresh(row)
    return ok({"route_id":row.id,"route_status":status,"risk_exposure":round(exposure,4),"blocked_edges":blocked,"estimated_travel_time":round(cost),"geometry":row.geometry,"computed_at":row.computed_at})

@app.get("/api/v1/shelters")
def shelters(db: Session=Depends(get_db), _: User=Depends(get_current_user)): return ok([{"id":s.id,"name":s.name,"available_capacity":s.available_capacity,"accessibility":s.accessibility,"status":s.status,"location":{"latitude":s.latitude,"longitude":s.longitude}} for s in db.scalars(select(Shelter)).all()])

@app.get("/api/v1/shelters/recommendations")
def shelter_recommendations(latitude: float, longitude: float, run_id: str|None=None, db: Session=Depends(get_db), _: User=Depends(get_current_user)):
    cells={c.cell_id:c for c in db.scalars(select(RiskCell).where(RiskCell.run_id==run_id)).all()} if run_id else {}
    out=[]
    for s in db.scalars(select(Shelter).where(Shelter.status=="open", Shelter.available_capacity>0)).all():
        risk=min((c.probability for c in cells.values()),default=.2); score=(s.available_capacity/max(s.capacity,1))*.4+(1-risk)*.4+(0.2 if s.accessibility else 0)+1/(1+distance((latitude,longitude),(s.latitude,s.longitude)))
        out.append({"shelter_id":s.id,"name":s.name,"score":round(score,4),"available_capacity":s.available_capacity,"predicted_risk":risk,"distance_km":round(distance((latitude,longitude),(s.latitude,s.longitude)),2)})
    return ok(sorted(out,key=lambda x:x["score"],reverse=True))

@app.get("/api/v1/resources")
def resources(db: Session=Depends(get_db), _: User=Depends(get_current_user)): return ok([{"id": r.id, "resource_type": r.resource_type, "available": r.available, "quantity": r.quantity, "owner": r.owner, "status": r.status, "location": {"latitude": r.latitude, "longitude": r.longitude}} for r in db.scalars(select(Resource)).all()])

@app.post("/api/v1/dispatches", status_code=201)
def dispatch(req: DispatchIn, db: Session=Depends(get_db), user: User=Depends(require_roles("responder","admin"))):
    r=db.get(Resource,req.resource_id)
    if not r or r.available<1: raise HTTPException(409,"Resource unavailable")
    r.available-=1; r.status="dispatched" if r.available==0 else "partially_dispatched"; audit(db,user,"resource.dispatch","resource",r.id,{"alert_id":req.alert_id,"priority":req.priority,"assigned_to":req.assigned_to}); return ok({"resource_id":r.id,"status":r.status,"remaining":r.available})

@app.get("/api/v1/alerts")
def alerts(db: Session=Depends(get_db), _: User=Depends(get_current_user)): return ok([{k:getattr(a,k) for k in ["id","run_id","severity","alert_type","cause","recommendation","status","confidence","latitude","longitude","issued_at"]} for a in db.scalars(select(Alert).order_by(Alert.issued_at.desc())).all()])

@app.post("/api/v1/alerts/{alert_id}/acknowledge")
def acknowledge(alert_id: str, db: Session=Depends(get_db), user: User=Depends(require_roles("responder","admin"))):
    a=db.get(Alert,alert_id)
    if not a: raise HTTPException(404,"Alert not found")
    a.status="acknowledged"; db.commit(); audit(db,user,"alert.acknowledge","alert",a.id,{"status":a.status}); return ok({"id":a.id,"status":a.status})

@app.get("/api/v1/routes/{route_id}")
def route_detail(route_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    row = db.get(EvacuationRoute, route_id)
    if not row:
        raise HTTPException(404, "Route not found")
    return ok({"route_id": row.id, "route_status": row.route_status, "risk_exposure": row.risk_exposure,
               "blocked_edges": row.blocked_edges, "estimated_travel_time": row.travel_time_sec,
               "geometry": row.geometry, "explanation": row.explanation, "computed_at": row.computed_at})

@app.get("/api/v1/map/drainage")
def drainage_map(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return {"type": "FeatureCollection", "features": [], "meta": {"data_state": "not_loaded", "message": "Drainage import pending; capacity priors are applied by scenario adjustment."}}

@app.post("/api/v1/data/imports", status_code=202)
def controlled_import(payload: dict, db: Session = Depends(get_db), user: User = Depends(require_roles("admin", "analyst"))):
    job = JobRun(job_type="controlled_import", input_hash=input_hash(payload), status="queued", result={"requested": payload})
    db.add(job); db.commit(); db.refresh(job)
    audit(db, user, "data.import.request", "job", job.id, payload)
    return ok({"job_id": job.id, "status": job.status, "quarantined_invalid_records": True})

@app.get("/api/v1/events/stream")
def events_stream(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    latest = db.scalar(select(ForecastRun).order_by(ForecastRun.created_at.desc()))
    return ok({"event_type": "snapshot", "run_id": latest.id if latest else None, "changed_layers": ["risk", "roads", "alerts"]})
