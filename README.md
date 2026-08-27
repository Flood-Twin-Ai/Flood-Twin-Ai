# 🌧️ JAL-DRISHTI — Integrated Ravet/Pune Flood Scenario & Emergency Routing

**Team:** ARC Reactors  
**Target:** Pune metropolitan area — Ravet / Pimpri-Chinchwad MVP study area  
**Purpose:** Integrated final prototype for the assigned flood-scenario, vulnerable-road, evacuation-routing and emergency-response module.

## What was integrated

This repository combines:

1. **ARC Reactors flood/routing engine**
   - rainfall-duration scenarios
   - road-level risk scoring
   - vulnerable/closed roads
   - risk-aware evacuation routing
   - emergency-response prioritization
   - interactive Streamlit dashboard

2. **Teammate's GIS / Digital Twin package**
   - Ravet study-area GeoJSON
   - Pavana River reference geometry
   - QGIS project (`gis/Ravet_FloodTwin_Member2.qgz`)
   - GeoPackage reference package
   - reproducible OSM and SRTM download scripts
   - base maps and source documentation

The application overlays the teammate's **study area and Pavana River reference** on the same interactive map used by the routing engine.

## Important data-status statement

This is a **functional SIH prototype**, not an operational flood forecast.

- OpenStreetMap road/facility data can be acquired online through OSMnx.
- The supplied study-area and Pavana reference files come from the teammate's GIS package.
- Rainfall scenarios, emergency incidents and several risk parameters are prototype inputs.
- The current terrain term is a relative proxy unless a validated DEM has been downloaded and integrated into the risk model.
- The teammate's package explicitly states that it does not contain a fabricated flood-risk heatmap.

Do not present the current risk score as flood probability, flood depth, or an official warning.

## Run

```powershell
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
python -m pytest -q
streamlit run app.py
```

If you only want to test without network access, switch **Use OpenStreetMap road/infrastructure data** off in the dashboard.

## GIS package

Open `gis/Ravet_FloodTwin_Member2.qgz` in QGIS to inspect the teammate's GIS layers.

The teammate's scripts are in `gis/scripts/`:

- `download_osm_member2.sh`
- `download_dem_member2.sh`

The GIS package documents the working extent as:

- South: 18.615
- West: 73.705
- North: 18.675
- East: 73.785
- CRS: EPSG:4326

The extent is a working MVP extent, not an official administrative boundary.

## Architecture

```text
                 RAVET / PUNE GIS
                       │
          ┌────────────┼─────────────┐
          ↓            ↓             ↓
       OSM roads    Study area    Pavana reference
          │            │             │
          └────────────┼─────────────┘
                       ↓
                Scenario Engine
                       ↓
                  Risk Model
                       ↓
             Vulnerable / Closed Roads
                       ↓
               Dynamic Road Graph
                  ↙           ↘
          Evacuation        Emergency
            Routing          Response
                  ↘           ↙
                   Interactive Map
```

## Repository structure

- `app.py` — Streamlit application
- `src/` — scenario, risk, routing, response and GIS integration modules
- `tests/` — automated tests
- `gis/` — teammate's QGIS/GIS package
- `docs/` — architecture, provenance, demo and judge guidance

## Production upgrade

For a scientifically validated flood system, integrate a validated Pune DEM, authoritative rainfall/forecast data, drainage capacity/network, historical flood observations, calibrated thresholds/models and verified shelter/emergency-unit data.

## Attribution

OpenStreetMap data: **© OpenStreetMap contributors, ODbL**.

## License

MIT — see `LICENSE`.
