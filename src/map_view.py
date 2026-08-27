import folium

PUNE_CENTER = [18.5204, 73.8567]

def _coords(G, node):
    d = G.nodes[node]
    return float(d.get("y", d.get("lat"))), float(d.get("x", d.get("lon")))

def build_map(G, route=None, response_paths=None, incidents=None, units=None, infrastructure=None, show_all_roads=False, gis_layers=None):
    m = folium.Map(
        location=PUNE_CENTER,
        zoom_start=12,
        control_scale=True,
        tiles="CartoDB positron",
    )

    edges = list(G.edges(keys=True, data=True))
    if not show_all_roads and len(edges) > 2500:
        # Keep the map responsive: show closed/high-risk edges plus a deterministic sample.
        critical = [e for e in edges if float(e[3].get("risk", 0)) >= 0.55]
        remaining = [e for e in edges if float(e[3].get("risk", 0)) < 0.55]
        step = max(1, len(remaining) // 1200)
        edges = critical + remaining[::step]

    for u, v, k, d in edges:
        try:
            a, b = _coords(G, u), _coords(G, v)
            risk = float(d.get("risk", 0))
            if d.get("closed"):
                color = "#991b1b"
                weight = 4
            elif risk >= 0.75:
                color = "#dc2626"
                weight = 3.5
            elif risk >= 0.55:
                color = "#f59e0b"
                weight = 3
            else:
                color = "#16a34a"
                weight = 2
            folium.PolyLine(
                [a, b],
                color=color,
                weight=weight,
                opacity=0.65,
                tooltip=f"Risk {risk:.2f} | {d.get('risk_class','LOW')} | {'CLOSED' if d.get('closed') else 'OPEN'}",
            ).add_to(m)
        except Exception:
            continue

    if route:
        pts = [_coords(G, n) for n in route]
        folium.PolyLine(pts, color="#2563eb", weight=8, opacity=0.95, tooltip="Risk-aware evacuation route").add_to(m)
        folium.Marker(pts[0], tooltip="EVACUATION ORIGIN", icon=folium.Icon(color="blue", icon="play")).add_to(m)
        folium.Marker(pts[-1], tooltip="SHELTER / DESTINATION", icon=folium.Icon(color="green", icon="home")).add_to(m)

    for p in response_paths or []:
        if p:
            folium.PolyLine([_coords(G, n) for n in p], color="#7c3aed", weight=5, opacity=0.8, tooltip="Emergency response path").add_to(m)

    for row in (infrastructure.to_dict("records") if infrastructure is not None and not infrastructure.empty else []):
        folium.CircleMarker(
            [row["lat"], row["lon"]],
            radius=5,
            color="#0f766e",
            fill=True,
            fill_opacity=0.85,
            tooltip=f"{row['type']} | {row['name']}",
        ).add_to(m)

    for inc in incidents or []:
        folium.Marker(
            _coords(G, inc["node"]),
            tooltip=f"{inc['id']} | severity {inc['severity']:.2f} | simulated",
            icon=folium.Icon(color="red", icon="warning-sign"),
        ).add_to(m)

    for unit in units or []:
        folium.Marker(
            _coords(G, unit["node"]),
            tooltip=f"{unit['id']} | {unit.get('type','unit')} | simulated",
            icon=folium.Icon(color="purple", icon="plus"),
        ).add_to(m)

    # Overlay the teammate's verified Ravet study-area/reference layers.
    if gis_layers:
        study = gis_layers.get("study_area")
        if study:
            folium.GeoJson(
                study, name="Ravet study area",
                style_function=lambda _: {"color": "#0f172a", "weight": 2, "fillOpacity": 0.03}
            ).add_to(m)
        pavana = gis_layers.get("pavana")
        if pavana:
            folium.GeoJson(
                pavana, name="Pavana River reference",
                style_function=lambda _: {"color": "#0284c7", "weight": 4, "opacity": 0.9}
            ).add_to(m)

    folium.LayerControl().add_to(m)
    return m
