import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

export const API = axios.create({
  baseURL: BASE_URL,
  timeout: 10000,
});

// ---- Risk & map layers ----
export const getRiskMap = () => API.get("/risk");
export const getFloodedAreas = () => API.get("/flooded-areas");
export const getUnsafeRoads = () => API.get("/roads/unsafe");

// ---- Alerts ----
export const getAlerts = () => API.get("/alerts");
export const acknowledgeAlert = (alertId) => API.post(`/alerts/${alertId}/ack`);

// ---- Shelters ----
export const getShelters = () => API.get("/shelters");
export const getShelterById = (id) => API.get(`/shelters/${id}`);

// ---- Routing ----
export const getSafeRoute = (from, to) => API.post("/route", { from, to });

// ---- Rainfall & simulation ----
export const getRainfallTimeline = () => API.get("/rainfall/timeline");
export const simulateFlood = (rainfallMmPerHr, horizonMinutes = 60) =>
  API.post("/simulate", { rainfall: rainfallMmPerHr, horizon_minutes: horizonMinutes });

// ---- Dashboard summary (risk/rainfall/alerts/shelters counts) ----
export const getDashboardSummary = () => API.get("/summary");

export default API;
