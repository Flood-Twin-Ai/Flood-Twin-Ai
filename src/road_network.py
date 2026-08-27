from pathlib import Path
import math
import random
import networkx as nx
import pandas as pd

try:
    import osmnx as ox
except Exception:
    ox = None

from .config import PUNE_CENTER, PUNE_RADIUS_M
from .risk_model import calculate_edge_risk, classify_risk

CACHE_DIR = Path("cache")
GRAPH_FILE = CACHE_DIR / "pune_drive.graphml"

def _float(v, default=0.0):
    try:
        if isinstance(v, (list, tuple)):
            v = v[0]
        return float(v)
    except Exception:
        return default

def build_synthetic_pune_graph(n=14, seed=42):
    """Clearly labelled offline demonstration graph; not actual Pune roads."""
    rng = random.Random(seed)
    base = nx.grid_2d_graph(n, n)
    G = nx.MultiDiGraph()
    G.add_nodes_from(base.nodes)
    for u, v in base.edges:
        G.add_edge(u, v)
        G.add_edge(v, u)

    for r, c in G.nodes:
        G.nodes[r, c].update(
            y=18.455 + r * 0.0105,
            x=73.785 + c * 0.0110,
            lat=18.455 + r * 0.0105,
            lon=73.785 + c * 0.0110,
            synthetic=True,
        )

    for u, v, k in G.edges(keys=True):
        dist_km = 0.7 + rng.random() * 0.6
        G.edges[u, v, k].update(
            length=dist_km * 1000,
            highway="tertiary",
            bridge=False,
            tunnel=False,
        )
    return G

def load_pune_graph(use_live=True, radius_m=PUNE_RADIUS_M):
    if use_live and ox is not None:
        CACHE_DIR.mkdir(exist_ok=True)
        if GRAPH_FILE.exists():
            try:
                return ox.load_graphml(GRAPH_FILE), "cached OpenStreetMap road network"
            except Exception:
                pass
        try:
            G = ox.graph.graph_from_point(
                PUNE_CENTER,
                dist=radius_m,
                network_type="drive",
                simplify=True,
            )
            G = ox.add_edge_lengths(G)
            ox.save_graphml(G, GRAPH_FILE)
            return G, "OpenStreetMap driving network"
        except Exception as exc:
            return build_synthetic_pune_graph(), f"synthetic fallback ({type(exc).__name__})"
    return build_synthetic_pune_graph(), "synthetic fallback (offline mode)"

def nearest_node(G, lat, lon):
    if ox is not None:
        try:
            return ox.distance.nearest_nodes(G, X=float(lon), Y=float(lat))
        except Exception:
            pass
    best = None
    best_d = float("inf")
    for node, data in G.nodes(data=True):
        y = _float(data.get("y", data.get("lat")))
        x = _float(data.get("x", data.get("lon")))
        d = (y - lat) ** 2 + (x - lon) ** 2
        if d < best_d:
            best_d, best = d, node
    return best

def attach_scenario_risk(G, rainfall_mm_h, duration_h, closure_threshold):
    H = G.copy()
    nodes = list(H.nodes(data=True))
    if not nodes:
        return H

    lats = [_float(d.get("y", d.get("lat")), 0.0) for _, d in nodes]
    lons = [_float(d.get("x", d.get("lon")), 0.0) for _, d in nodes]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    for n, d in H.nodes(data=True):
        lat = _float(d.get("y", d.get("lat")))
        lon = _float(d.get("x", d.get("lon")))
        # Relative spatial proxy only. Replace with DEM-derived elevation for production.
        north = (lat - min_lat) / max(1e-9, max_lat - min_lat)
        east = (lon - min_lon) / max(1e-9, max_lon - min_lon)
        d["terrain_proxy"] = float(1.0 - 0.5 * (north + east))

    for u, v, k, d in H.edges(keys=True, data=True):
        low_proxy = (H.nodes[u]["terrain_proxy"] + H.nodes[v]["terrain_proxy"]) / 2
        d["risk"] = calculate_edge_risk(d, rainfall_mm_h, duration_h, low_proxy)
        d["risk_class"] = classify_risk(d["risk"])

        length_km = _float(d.get("length"), 1000.0) / 1000.0
        # OSM maxspeed can be a string/list; this is only a routing approximation.
        speed = _float(d.get("speed_kph"), 30.0)
        if speed <= 0:
            speed = 30.0
        d["distance_km"] = length_km
        d["travel_time_min"] = (length_km / speed) * 60.0
        d["closed"] = bool(d["risk"] >= closure_threshold)
        # Risk-aware routing cost: travel time is primary; flood exposure penalizes the edge.
        d["risk_cost"] = d["travel_time_min"] * (1.0 + 4.0 * d["risk"])
    return H

def edge_dataframe(G):
    rows = []
    for u, v, k, d in G.edges(keys=True, data=True):
        rows.append({
            "from": str(u),
            "to": str(v),
            "distance_km": round(_float(d.get("distance_km"), 1.0), 3),
            "risk": round(_float(d.get("risk"), 0.0), 3),
            "risk_class": d.get("risk_class", "UNKNOWN"),
            "status": "CLOSED" if d.get("closed") else "OPEN",
        })
    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["from","to","distance_km","risk","risk_class","status"])
    return df.sort_values(["risk", "distance_km"], ascending=[False, True])
