import networkx as nx

def _simple_graph(G):
    H = nx.DiGraph()
    for u, v, k, d in G.edges(keys=True, data=True):
        if d.get("closed"):
            continue
        cost = float(d.get("risk_cost", d.get("travel_time_min", 1.0)))
        dist = float(d.get("distance_km", 1.0))
        risk = float(d.get("risk", 0.0))
        if not H.has_edge(u, v) or cost < H[u][v]["weight"]:
            H.add_edge(u, v, weight=cost, distance_km=dist, risk=risk)
    return H

def _route_from_path(H, path):
    distance = sum(H[a][b]["distance_km"] for a, b in zip(path, path[1:]))
    risk_exposure = sum(H[a][b]["risk"] for a, b in zip(path, path[1:]))
    edges = max(1, len(path) - 1)
    return {
        "path": path,
        "distance_km": distance,
        "risk_exposure": risk_exposure,
        "avg_risk": risk_exposure / edges,
        "edges": edges,
    }

def safest_route(G, start, destination):
    H = _simple_graph(G)
    try:
        path = nx.shortest_path(H, start, destination, weight="weight")
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None
    return _route_from_path(H, path)

def shortest_route(G, start, destination):
    H = _simple_graph(G)
    try:
        path = nx.shortest_path(H, start, destination, weight="distance_km")
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None
    return _route_from_path(H, path)
