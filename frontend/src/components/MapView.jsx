import { MapContainer, TileLayer, Circle, Polyline, Marker, Popup, Tooltip } from "react-leaflet";
import L from "leaflet";

const PUNE_CENTER = [18.5204, 73.8567];

const RISK_COLORS = {
  low: "#34D399",
  moderate: "#FBBF24",
  high: "#F97316",
  critical: "#EF4444",
};

const shelterIcon = L.divIcon({
  className: "",
  html: `<div style="
    width:26px;height:26px;border-radius:8px;
    background:#111A2C;border:1.5px solid #2DD4BF;
    display:flex;align-items:center;justify-content:center;
    font-size:14px;box-shadow:0 2px 8px rgba(0,0,0,0.5);
  ">🏠</div>`,
  iconSize: [26, 26],
  iconAnchor: [13, 13],
});

export default function MapView({
  zones = [],
  roads = [],
  shelters = [],
  route = null,
  height = "100%",
}) {
  return (
    <div style={{ height }} className="relative w-full overflow-hidden rounded-xl">
      <MapContainer
        center={PUNE_CENTER}
        zoom={12}
        scrollWheelZoom
        style={{ height: "100%", width: "100%" }}
      >
        <TileLayer
          attribution='&copy; <a href="https://carto.com/attributions">CARTO</a> &copy; OpenStreetMap contributors'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        {/* Layer 1 — Flood risk zones */}
        {zones.map((z) => (
          <Circle
            key={z.id}
            center={[z.lat, z.lng]}
            radius={z.radius}
            pathOptions={{
              color: RISK_COLORS[z.level] || RISK_COLORS.moderate,
              fillColor: RISK_COLORS[z.level] || RISK_COLORS.moderate,
              fillOpacity: 0.25,
              weight: 1.5,
            }}
          >
            <Tooltip direction="top" opacity={1}>
              <span className="font-mono text-xs">
                {z.name} — {z.level.toUpperCase()}
              </span>
            </Tooltip>
          </Circle>
        ))}

        {/* Layer 2 — Roads */}
        {roads.map((r) => (
          <Polyline
            key={r.id}
            positions={r.path}
            pathOptions={{
              color: r.status === "unsafe" ? "#EF4444" : "#34D399",
              weight: 4,
              opacity: 0.85,
              dashArray: r.status === "unsafe" ? "2 6" : undefined,
            }}
          >
            <Tooltip sticky>
              <span className="font-mono text-xs">
                {r.name} — {r.status === "unsafe" ? "Unsafe" : "Safe"}
              </span>
            </Tooltip>
          </Polyline>
        ))}

        {/* Layer 3 — Shelters */}
        {shelters.map((s) => (
          <Marker key={s.id} position={[s.lat, s.lng]} icon={shelterIcon}>
            <Popup>
              <div className="font-mono text-xs space-y-0.5">
                <p className="font-semibold">{s.name}</p>
                <p>Capacity: {s.capacity}</p>
                <p>Available: {s.available}</p>
                <p>Risk: {s.risk?.toUpperCase()}</p>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Layer 4 — Active recommended route */}
        {route && route.length > 1 && (
          <Polyline
            positions={route}
            pathOptions={{ color: "#2DD4BF", weight: 5, opacity: 0.95 }}
          />
        )}
      </MapContainer>
    </div>
  );
}
