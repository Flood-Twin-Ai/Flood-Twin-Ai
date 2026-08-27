from .config import PUNE_WAYPOINTS
from .road_network import nearest_node

def get_named_waypoints():
    return {
        name: {"lat": lat, "lon": lon}
        for name, (lat, lon) in PUNE_WAYPOINTS.items()
    }

def build_demo_events(G):
    """Demonstration incidents/units located near named Pune waypoints.
    These are simulated events, not live emergency calls."""
    places = get_named_waypoints()
    usable = []
    for name, p in places.items():
        node = nearest_node(G, p["lat"], p["lon"])
        if node is not None:
            usable.append((name, node))
    if len(usable) < 4:
        nodes = list(G.nodes)
        usable = [(f"Demo-{i+1}", n) for i, n in enumerate(nodes[:8])]

    incidents = [
        {"id": "INC-01", "node": usable[1][1], "severity": 0.95, "location": usable[1][0]},
        {"id": "INC-02", "node": usable[min(3, len(usable)-1)][1], "severity": 0.70, "location": usable[min(3, len(usable)-1)][0]},
        {"id": "INC-03", "node": usable[min(5, len(usable)-1)][1], "severity": 0.50, "location": usable[min(5, len(usable)-1)][0]},
    ]
    units = [
        {"id": "FIRE-A", "node": usable[0][1], "type": "Fire"},
        {"id": "AMB-B", "node": usable[min(2, len(usable)-1)][1], "type": "Ambulance"},
        {"id": "POLICE-C", "node": usable[min(6, len(usable)-1)][1], "type": "Police"},
    ]
    return incidents, units
