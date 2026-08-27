from app.services import severity, run_nowcast
from app.db.database import Base, SessionLocal, engine
from app.db.models import ForecastRun


def test_severity_bands():
    assert severity(.1) == "low"
    assert severity(.4) == "moderate"
    assert severity(.7) == "high"
    assert severity(.9) == "critical"


def test_rainfall_changes_risk():
    Base.metadata.drop_all(bind=engine); Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    low = run_nowcast(db, None, 60, intensity=10)
    high = run_nowcast(db, None, 60, intensity=100)
    assert high.summary["max_probability"] > low.summary["max_probability"]
    db.close()


def test_health_and_auth(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"
