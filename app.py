import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from src.config import PUNE_CENTER, SCENARIOS
from src.demo_data import build_demo_events, get_named_waypoints
from src.infrastructure import load_infrastructure
from src.gis_overlay import load_ravet_layers
from src.map_view import build_map
from src.response_optimizer import prioritize_incidents
from src.road_network import attach_scenario_risk, load_pune_graph
from src.routing import safest_route, shortest_route
from src.scenario_engine import scenario_summary

st.set_page_config(
    page_title="JAL-DRISHTI | Pune Flood Response",
    page_icon="🌧️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
.metric-card {border:1px solid #e5e7eb;border-radius:12px;padding:12px;background:#fff;}
.small-note {font-size:0.86rem;color:#64748b;}
</style>
""", unsafe_allow_html=True)

st.title("🌧️ JAL-DRISHTI")
st.subheader("Pune Flood Scenario, Vulnerability & Emergency Routing Engine")
st.caption("ARC Reactors • College SIH Internal Prototype • Assigned module: flood scenarios, vulnerable roads/infrastructure, evacuation and emergency response")

with st.sidebar:
    st.header("Scenario Controls")
    use_live = st.toggle("Use OpenStreetMap road/infrastructure data", value=True)
    scenario_name = st.selectbox("Scenario", ["Custom", "Moderate", "Heavy", "Extreme"])

    if scenario_name == "Custom":
        rain = st.slider("Rainfall intensity (mm/hour)", 10.0, 200.0, 100.0, 5.0)
        duration = st.slider("Duration (hours)", 0.5, 6.0, 2.0, 0.5)
        closure = st.slider("Road closure threshold", 0.60, 0.95, 0.78, 0.01)
    else:
        s = SCENARIOS[scenario_name]
        rain, duration, closure = s.rainfall_mm_h, s.duration_h, s.closure_threshold
        st.info(f"{scenario_name}: {rain:.0f} mm/h for {duration:.1f} h")

    show_all_roads = st.checkbox("Show all road segments on map", value=False)
    st.divider()
    st.markdown("**Map legend**")
    st.markdown("🟢 lower modeled risk  •  🟠 moderate/high  •  🔴 critical  •  🔵 evacuation  •  🟣 response")
    st.caption("Risk is a prototype scenario index, not an official flood forecast.")

@st.cache_resource(show_spinner="Loading Pune road network…")
def get_graph(use_live):
    return load_pune_graph(use_live=use_live)

@st.cache_data(show_spinner="Loading mapped infrastructure…")
def get_infrastructure(use_live):
    return load_infrastructure(use_live=use_live)

@st.cache_data
def get_gis_layers():
    return load_ravet_layers("gis/GIS_Data")

G0, road_source = get_graph(use_live)
infra, infra_source = get_infrastructure(use_live)
gis_layers = get_gis_layers()

if st.button("▶ Run / Recalculate Scenario", type="primary", use_container_width=True):
    st.session_state["scenario_run"] = True

if "scenario_run" not in st.session_state:
    st.info("Set a rainfall scenario and click **Run / Recalculate Scenario**.")
    st.stop()

G = attach_scenario_risk(G0, rain, duration, closure)

st.warning(
    "Prototype limitation: the risk score is a transparent decision-support index. "
    "It is not calibrated flood depth/probability. When no validated DEM is supplied, "
    "the terrain feature is only a relative proxy."
)

# Named demo waypoints are approximate locations used to make the prototype easy to demonstrate.
waypoints = get_named_waypoints()
waypoint_names = list(waypoints)

c1, c2 = st.columns(2)
with c1:
    origin_name = st.selectbox("Evacuation origin", waypoint_names, index=0)
with c2:
    destination_name = st.selectbox("Shelter / destination", waypoint_names, index=min(3, len(waypoint_names)-1))

# Find the nearest graph nodes for the selected named waypoints.
# Waypoints store latitude/longitude only; node IDs are resolved against the
# currently loaded graph so both OSM and synthetic fallback graphs work.
from src.road_network import nearest_node
start = nearest_node(G, waypoints[origin_name]["lat"], waypoints[origin_name]["lon"])
destination = nearest_node(G, waypoints[destination_name]["lat"], waypoints[destination_name]["lon"])

safe = safest_route(G, start, destination)
short = shortest_route(G, start, destination)

edges = __import__("src.road_network", fromlist=["edge_dataframe"]).edge_dataframe(G)
closed = int((edges["status"] == "CLOSED").sum())
high = int((edges["risk"] >= 0.55).sum())
critical = int((edges["risk"] >= 0.75).sum())
mean_risk = float(edges["risk"].mean()) if not edges.empty else 0.0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Rainfall", f"{rain:.0f} mm/h")
k2.metric("Road segments", f"{len(edges):,}")
k3.metric("High-risk", f"{high:,}")
k4.metric("Closed", f"{closed:,}")
k5.metric("Mean risk", f"{mean_risk:.3f}")

incidents, units = build_demo_events(G)
response_df = prioritize_incidents(G, incidents, units)
response_paths = [p for p in response_df["path"].tolist() if p] if not response_df.empty else []

st.subheader("1. Pune Risk & Routing Map")
route_path = safe["path"] if safe else None
st_folium(
    build_map(
        G,
        route=route_path,
        response_paths=response_paths,
        incidents=incidents,
        units=units,
        infrastructure=infra,
        show_all_roads=show_all_roads,
        gis_layers=gis_layers,
    ),
    width=None,
    height=620,
)

st.subheader("2. Evacuation Route Analysis")
if safe:
    a, b, c, d = st.columns(4)
    a.metric("Risk-aware distance", f"{safe['distance_km']:.2f} km")
    b.metric("Average route risk", f"{safe['avg_risk']:.3f}")
    c.metric("Risk exposure", f"{safe['risk_exposure']:.3f}")
    if short:
        extra = safe["distance_km"] - short["distance_km"]
        d.metric("Extra distance vs shortest", f"{extra:+.2f} km")
    st.success(
        "The blue route minimizes a risk-aware cost after closed roads are excluded. "
        "A longer route may be selected when it has lower modeled flood exposure."
    )
else:
    st.error("No feasible evacuation route exists under this scenario and closure threshold.")

with st.expander("Routing diagnostics"):
    st.write("Origin:", origin_name, start)
    st.write("Destination:", destination_name, destination)
    st.write("Risk-aware route:", safe["path"] if safe else None)
    st.write("Shortest-distance route:", short["path"] if short else None)

st.subheader("3. Vulnerable Road Segments")
st.dataframe(edges[["from", "to", "distance_km", "risk", "risk_class", "status"]].head(80), use_container_width=True, height=340)

st.subheader("4. Critical / Vulnerable Infrastructure")
if infra.empty:
    st.info("No OSM infrastructure layer was retrieved. The road-risk and routing engine remains usable.")
else:
    st.dataframe(
        infra[["type", "name", "lat", "lon", "source"]].head(120),
        use_container_width=True,
        height=300,
    )

st.subheader("5. Emergency Response Prioritization")
if response_df.empty:
    st.info("No response incidents available.")
else:
    display = response_df.drop(columns=["path"])
    st.dataframe(display, use_container_width=True, height=260)

st.subheader("6. Scenario Comparison")
rows = []
for name, s in SCENARIOS.items():
    S = attach_scenario_risk(G0, s.rainfall_mm_h, s.duration_h, s.closure_threshold)
    E = __import__("src.road_network", fromlist=["edge_dataframe"]).edge_dataframe(S)
    r = safest_route(S, start, destination)
    rows.append({
        "scenario": name,
        "rainfall_mm_h": s.rainfall_mm_h,
        "duration_h": s.duration_h,
        "high_risk_roads": int((E["risk"] >= 0.55).sum()),
        "closed_roads": int((E["status"] == "CLOSED").sum()),
        "route_km": round(r["distance_km"], 2) if r else None,
        "avg_route_risk": round(r["avg_risk"], 3) if r else None,
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True)

st.subheader("7. What the Prototype Demonstrates")
st.markdown("""
- **Scenario engine:** rainfall intensity + duration drive a reproducible scenario.
- **Risk engine:** transparent weighted score using scenario intensity/duration, road exposure and OSM hydro indicators, plus a terrain proxy when no DEM is available.
- **Vulnerability:** road segments are classified as LOW / MODERATE / HIGH / CRITICAL and can be closed at a configurable threshold.
- **Evacuation:** a dynamic graph removes closed edges and minimizes a risk-aware routing cost.
- **Emergency response:** available units are evaluated against incident severity, travel distance and route risk.
- **Pune GIS:** OpenStreetMap can provide a real driving network and tagged facilities when online access is available.
""")

st.subheader("8. Engineering Honesty")
st.markdown("""
**Do not present this prototype as an operational flood warning system.**  
For real deployment, the terrain proxy must be replaced by a validated DEM; drainage capacity, authoritative rainfall/forecast feeds and historical flood observations must be integrated; and thresholds/models must be calibrated and reviewed by disaster-management/GIS experts.
""")

st.caption(f"Road source: {road_source} • Infrastructure source: {infra_source} • Integrated study area: Ravet / Pimpri-Chinchwad • Map center: {PUNE_CENTER}")
