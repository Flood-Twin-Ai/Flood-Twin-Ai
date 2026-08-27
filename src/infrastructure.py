import pandas as pd
from pathlib import Path

try:
    import osmnx as ox
except Exception:
    ox = None

from .config import PUNE_CENTER, PUNE_RADIUS_M

TAGS = {
    "amenity": ["hospital", "school", "fire_station", "police", "clinic", "social_facility"],
    "emergency": ["ambulance", "fire_hydrant"],
}

def load_infrastructure(use_live=True, radius_m=PUNE_RADIUS_M):
    if not use_live or ox is None:
        return pd.DataFrame(columns=["id","type","name","lat","lon","source"]), "offline/no OSM infrastructure"

    try:
        gdf = ox.features.features_from_point(PUNE_CENTER, tags=TAGS, dist=radius_m)
        if gdf.empty:
            return pd.DataFrame(columns=["id","type","name","lat","lon","source"]), "OSM returned no matching facilities"

        rows = []
        for idx, row in gdf.iterrows():
            geom = row.get("geometry")
            if geom is None:
                continue
            pt = geom if geom.geom_type == "Point" else geom.representative_point()
            rows.append({
                "id": f"OSM-{idx}",
                "type": row.get("amenity") or row.get("emergency") or "other",
                "name": row.get("name") or "Unnamed OSM facility",
                "lat": float(pt.y),
                "lon": float(pt.x),
                "source": "OpenStreetMap",
            })
        return pd.DataFrame(rows), "OpenStreetMap facilities"
    except Exception as exc:
        return pd.DataFrame(columns=["id","type","name","lat","lon","source"]), f"OSM infrastructure unavailable ({type(exc).__name__})"
