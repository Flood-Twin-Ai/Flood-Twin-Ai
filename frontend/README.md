# JAL-DRISHTI — Frontend

React + Vite + Leaflet + Recharts dashboard for the JAL-DRISHTI AI Urban Flood
Decision System (authority control-room view + citizen view).

## Run it

```bash
npm install
npm run dev
```

Open http://localhost:5173

The app works standalone with realistic demo data even with no backend
running — every API call in `src/services/api.js` falls back to
`src/services/mockData.js` on failure (see `useLiveData` hook), so it's safe
to demo before FastAPI is wired up. A "demo data" badge appears in the navbar
whenever you're looking at mock data instead of a live response.

## Connect to the real backend

1. Copy `.env.example` to `.env` and set `VITE_API_BASE_URL` to your FastAPI
   server (default expects `http://localhost:8000/api`).
2. Implement these endpoints on the backend (see `src/services/api.js` for
   the exact calls the frontend makes):
   - `GET /risk` → risk zones `[{ id, name, lat, lng, level, radius }]`
   - `GET /roads/unsafe` → `[{ id, name, status, path: [[lat,lng], ...] }]`
   - `GET /shelters` → `[{ id, name, lat, lng, capacity, available, risk, distance_km }]`
   - `GET /alerts` → `[{ id, zone, level, cause, action, updated_minutes_ago }]`
   - `GET /rainfall/timeline` → `[{ minute, actual, predicted }]`
   - `GET /summary` → `{ risk_level, rainfall_mm_hr, active_alerts, active_shelters }`
   - `POST /route { from, to }` → `{ distance_km, duration_min, risk }`
   - `POST /simulate { rainfall, horizon_minutes }` → `{ risk_level, unsafe_road_count, recommended_shelter, zones }`

## Pages

| Route       | Page               | Purpose                                   |
|-------------|--------------------|--------------------------------------------|
| `/`         | AuthorityDashboard | Control-room: map, KPIs, alerts, charts, what-if simulator |
| `/citizen`  | CitizenDashboard   | Simplified public-facing view              |
| `/alerts`   | Alerts             | Full explainable alert list                |
| `/shelters` | Shelters           | Ranked shelters + safe-route finder        |

## Structure

```
src/
├── components/   Navbar, Sidebar, MapView, RiskCard, AlertPanel,
│                 ShelterCard, RoutePanel, RainfallSlider, Charts
├── pages/        AuthorityDashboard, CitizenDashboard, Alerts, Shelters
├── services/     api.js (axios), mockData.js (demo fallback), useLiveData.js
├── App.jsx       Route definitions
└── main.jsx      React root + BrowserRouter
```

## Design system

Dark "monsoon control-room" palette — deep basin blues (`#070B14`–`#1B2740`),
a teal water accent (`#2DD4BF`), and a four-step risk scale (green → amber →
orange → red). Type: IBM Plex Sans for UI text, IBM Plex Mono for all
numeric/data readouts (risk cards, chart axes, route stats) to give the
dashboard an instrument-panel feel. Tokens live in `tailwind.config.js`.
