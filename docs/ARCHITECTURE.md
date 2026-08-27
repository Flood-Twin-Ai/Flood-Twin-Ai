# JAL-DRISHTI Architecture

## Core pipeline

Rainfall + duration -> scenario engine -> transparent road risk -> vulnerable/closed roads -> dynamic graph -> risk-aware evacuation and emergency response.

## Modules

- `scenario_engine.py`: predefined and custom scenario logic.
- `risk_model.py`: transparent weighted road-risk index.
- `road_network.py`: OSMnx acquisition, synthetic fallback, scenario risk attachment.
- `routing.py`: shortest-distance and risk-aware shortest-path algorithms.
- `response_optimizer.py`: incident/unit assignment using risk-aware route cost.
- `infrastructure.py`: optional OSM-tagged facilities.
- `map_view.py`: Folium visualization.
- `app.py`: Streamlit interface and orchestration.

## Important design decision

The prototype deliberately separates **data acquisition** from **risk/routing logic**. This lets the team replace the baseline risk model with a calibrated GIS/ML/hydrologic model later without rewriting the routing/UI layers.
