import json
from pathlib import Path


def load_geojson(path):
    p = Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def load_ravet_layers(base_dir="gis/GIS_Data"):
    base = Path(base_dir)
    return {
        "study_area": load_geojson(base / "study_area.geojson"),
        "pavana": load_geojson(base / "pavana_reference.geojson"),
    }
