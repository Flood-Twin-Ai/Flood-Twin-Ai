import pandas as pd
from .routing import safest_route

def prioritize_incidents(G, incidents, units):
    results = []
    for inc in incidents:
        candidates = []
        for unit in units:
            route = safest_route(G, unit["node"], inc["node"])
            if route:
                # Primary: route risk; secondary: travel distance.
                assignment_cost = route["risk_exposure"] + 0.15 * route["distance_km"]
                candidates.append((assignment_cost, route, unit))

        candidates.sort(key=lambda x: x[0])
        if candidates:
            _, route, unit = candidates[0]
            # Higher score = more urgent. This is a prototype priority index.
            priority = min(
                100.0,
                55.0 * float(inc["severity"])
                + 25.0 * route["avg_risk"]
                + 20.0 * min(1.0, route["distance_km"] / 10.0),
            )
            results.append({
                "incident": inc["id"],
                "severity": round(float(inc["severity"]), 2),
                "assigned_unit": unit["id"],
                "distance_km": round(route["distance_km"], 2),
                "route_risk": round(route["avg_risk"], 3),
                "priority_score": round(priority, 1),
                "path": route["path"],
            })
        else:
            results.append({
                "incident": inc["id"],
                "severity": round(float(inc["severity"]), 2),
                "assigned_unit": "NO FEASIBLE UNIT",
                "distance_km": None,
                "route_risk": None,
                "priority_score": 100.0,
                "path": [],
            })

    return pd.DataFrame(results).sort_values("priority_score", ascending=False) if results else pd.DataFrame(
        columns=["incident","severity","assigned_unit","distance_km","route_risk","priority_score","path"]
    )
