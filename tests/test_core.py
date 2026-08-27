from src.road_network import build_synthetic_pune_graph, attach_scenario_risk
from src.routing import safest_route, shortest_route
from src.response_optimizer import prioritize_incidents

def test_risk_increases_with_rainfall():
    g = build_synthetic_pune_graph(8)
    low = attach_scenario_risk(g, 30, 1, 0.99)
    high = attach_scenario_risk(g, 180, 4, 0.99)
    low_mean = sum(d["risk"] for *_, d in low.edges(data=True)) / low.number_of_edges()
    high_mean = sum(d["risk"] for *_, d in high.edges(data=True)) / high.number_of_edges()
    assert high_mean > low_mean

def test_route_exists_without_closures():
    g = build_synthetic_pune_graph(6)
    g = attach_scenario_risk(g, 30, 1, 0.99)
    nodes = list(g.nodes)
    route = safest_route(g, nodes[0], nodes[-1])
    assert route is not None
    assert route["distance_km"] > 0

def test_route_fails_when_every_edge_is_closed():
    g = build_synthetic_pune_graph(5)
    g = attach_scenario_risk(g, 200, 6, 0.0)
    nodes = list(g.nodes)
    assert safest_route(g, nodes[0], nodes[-1]) is None

def test_shortest_route_and_safe_route_are_available():
    g = build_synthetic_pune_graph(7)
    g = attach_scenario_risk(g, 80, 2, 0.99)
    nodes = list(g.nodes)
    assert shortest_route(g, nodes[0], nodes[-1]) is not None
    assert safest_route(g, nodes[0], nodes[-1]) is not None

def test_emergency_assignment():
    g = build_synthetic_pune_graph(7)
    g = attach_scenario_risk(g, 60, 1, 0.99)
    nodes = list(g.nodes)
    incidents = [{"id": "INC-01", "node": nodes[-1], "severity": 0.9}]
    units = [{"id": "FIRE-A", "node": nodes[0]}]
    df = prioritize_incidents(g, incidents, units)
    assert len(df) == 1
    assert df.iloc[0]["assigned_unit"] == "FIRE-A"
