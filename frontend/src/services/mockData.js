// Demo-mode fallback data. Used whenever the backend at VITE_API_BASE_URL
// is unreachable, so the UI is always presentable (SIH judges, offline demo, etc).

export const MOCK_SUMMARY = {
  risk_level: "HIGH",
  rainfall_mm_hr: 85,
  active_alerts: 12,
  active_shelters: 18,
};

export const MOCK_RISK_ZONES = [
  { id: "z1", name: "Kharadi", lat: 18.5515, lng: 73.9345, level: "critical", radius: 650 },
  { id: "z2", name: "Yerwada", lat: 18.5605, lng: 73.8827, level: "high", radius: 520 },
  { id: "z3", name: "Kothrud", lat: 18.5074, lng: 73.8077, level: "moderate", radius: 480 },
  { id: "z4", name: "Hadapsar", lat: 18.5089, lng: 73.9260, level: "high", radius: 560 },
  { id: "z5", name: "Aundh", lat: 18.5590, lng: 73.8070, level: "low", radius: 400 },
  { id: "z6", name: "Sinhagad Road", lat: 18.4735, lng: 73.8265, level: "moderate", radius: 440 },
];

export const MOCK_UNSAFE_ROADS = [
  {
    id: "r1",
    name: "Kharadi Bypass",
    status: "unsafe",
    path: [
      [18.5605, 73.9420],
      [18.5540, 73.9370],
      [18.5470, 73.9310],
    ],
  },
  {
    id: "r2",
    name: "Mundhwa-Kharadi Rd",
    status: "unsafe",
    path: [
      [18.5390, 73.9280],
      [18.5460, 73.9330],
      [18.5515, 73.9345],
    ],
  },
  {
    id: "r3",
    name: "University Road",
    status: "safe",
    path: [
      [18.5590, 73.8070],
      [18.5550, 73.8290],
      [18.5515, 73.8450],
    ],
  },
];

export const MOCK_SHELTERS = [
  { id: "s1", name: "Shelter A — Kharadi Community Hall", lat: 18.5470, lng: 73.9300, capacity: 500, available: 320, risk: "low", distance_km: 1.2 },
  { id: "s2", name: "Shelter B — Yerwada High School", lat: 18.5650, lng: 73.8790, capacity: 350, available: 140, risk: "low", distance_km: 2.8 },
  { id: "s3", name: "Shelter C — Kothrud Sports Complex", lat: 18.5040, lng: 73.8050, capacity: 600, available: 480, risk: "moderate", distance_km: 4.1 },
  { id: "s4", name: "Shelter D — Hadapsar Municipal Bldg", lat: 18.5110, lng: 73.9300, capacity: 250, available: 40, risk: "low", distance_km: 0.9 },
];

export const MOCK_ALERTS = [
  {
    id: "a1",
    zone: "Kharadi Zone",
    level: "critical",
    cause: "Heavy rainfall + low drainage capacity",
    action: "Evacuate low-lying areas immediately.",
    updated_minutes_ago: 2,
  },
  {
    id: "a2",
    zone: "Hadapsar Zone",
    level: "high",
    cause: "River bank overflow risk within 45 minutes",
    action: "Avoid riverside routes; move to higher ground.",
    updated_minutes_ago: 9,
  },
  {
    id: "a3",
    zone: "Kothrud Zone",
    level: "moderate",
    cause: "Waterlogging reported on Paud Road",
    action: "Expect delays; use alternate routes where possible.",
    updated_minutes_ago: 21,
  },
  {
    id: "a4",
    zone: "Yerwada Zone",
    level: "high",
    cause: "Drainage capacity exceeded near Nagar Road",
    action: "Two-wheelers advised to avoid underpasses.",
    updated_minutes_ago: 34,
  },
];

export const MOCK_RAINFALL_TIMELINE = [
  { minute: 0, actual: 12, predicted: null },
  { minute: 15, actual: 28, predicted: null },
  { minute: 30, actual: 46, predicted: null },
  { minute: 45, actual: 61, predicted: null },
  { minute: 60, actual: 85, predicted: null },
  { minute: 75, actual: null, predicted: 92 },
  { minute: 90, actual: null, predicted: 78 },
  { minute: 105, actual: null, predicted: 55 },
  { minute: 120, actual: null, predicted: 40 },
];

export const MOCK_RISK_DISTRIBUTION = [
  { name: "Low", value: 9, level: "low" },
  { name: "Moderate", value: 6, level: "moderate" },
  { name: "High", value: 4, level: "high" },
  { name: "Critical", value: 1, level: "critical" },
];

// Very rough deterministic "simulation" so the what-if slider feels alive in demo mode.
export function mockSimulate(rainfall, horizonMinutes = 60) {
  const intensity = Math.min(Math.max((rainfall - 20) / 80, 0), 1); // 0..1
  const levels = ["low", "moderate", "high", "critical"];
  const levelIndex = Math.min(3, Math.floor(intensity * 4));
  const unsafeRoads = Math.round(2 + intensity * 20);
  const bestShelter = intensity > 0.7 ? MOCK_SHELTERS[1] : MOCK_SHELTERS[0];

  return {
    rainfall,
    horizon_minutes: horizonMinutes,
    risk_level: levels[levelIndex],
    unsafe_road_count: unsafeRoads,
    recommended_shelter: bestShelter.name,
    zones: MOCK_RISK_ZONES.map((z, i) => ({
      ...z,
      level: levels[Math.min(3, Math.max(0, levelIndex - (i % 2)))],
    })),
  };
}
