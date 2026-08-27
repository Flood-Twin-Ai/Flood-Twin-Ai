import numpy as np

# Prototype weights only. These are not calibrated probabilities.
WEIGHTS = {
    "rainfall": 0.45,
    "duration": 0.15,
    "low_elevation": 0.15,
    "road_exposure": 0.15,
    "hydro_indicator": 0.10,
}

def clip01(x):
    return float(np.clip(x, 0.0, 1.0))

def scenario_rainfall_index(rainfall_mm_h):
    return clip01(float(rainfall_mm_h) / 200.0)

def duration_index(duration_h):
    return clip01(float(duration_h) / 6.0)

def edge_features(data):
    highway = data.get("highway", "")
    if isinstance(highway, (list, tuple)):
        highway = highway[0] if highway else ""
    highway = str(highway)

    exposure_map = {
        "motorway": 0.90, "trunk": 0.90, "primary": 0.85,
        "secondary": 0.75, "tertiary": 0.65, "residential": 0.45,
        "unclassified": 0.40, "service": 0.30,
    }
    road_exposure = exposure_map.get(highway, 0.40)

    hydro = 0.0
    if data.get("bridge"):
        hydro += 0.35
    if data.get("tunnel"):
        hydro += 0.25
    if data.get("waterway"):
        hydro += 0.40

    return clip01(road_exposure), clip01(hydro)

def calculate_edge_risk(data, rainfall_mm_h, duration_h, low_elevation=0.5):
    rain = scenario_rainfall_index(rainfall_mm_h)
    dur = duration_index(duration_h)
    exposure, hydro = edge_features(data)
    low = clip01(low_elevation)

    score = (
        WEIGHTS["rainfall"] * rain +
        WEIGHTS["duration"] * dur +
        WEIGHTS["low_elevation"] * low +
        WEIGHTS["road_exposure"] * exposure +
        WEIGHTS["hydro_indicator"] * hydro
    )
    return clip01(score)

def classify_risk(score):
    if score >= 0.75:
        return "CRITICAL"
    if score >= 0.55:
        return "HIGH"
    if score >= 0.35:
        return "MODERATE"
    return "LOW"
