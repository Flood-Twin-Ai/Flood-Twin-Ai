import { useNavigate } from "react-router-dom";
import Navbar from "../components/Navbar.jsx";
import MapView from "../components/MapView.jsx";
import { useLiveData } from "../services/useLiveData.js";
import { getDashboardSummary, getRiskMap, getShelters, getAlerts } from "../services/api.js";
import { MOCK_SUMMARY, MOCK_RISK_ZONES, MOCK_SHELTERS, MOCK_ALERTS } from "../services/mockData.js";

const RISK_STYLES = {
  low: "text-risk-low",
  moderate: "text-risk-moderate",
  high: "text-risk-high",
  critical: "text-risk-critical",
};

export default function CitizenDashboard() {
  const navigate = useNavigate();
  const { data: summary, isMock } = useLiveData(getDashboardSummary, MOCK_SUMMARY);
  const { data: zones } = useLiveData(getRiskMap, MOCK_RISK_ZONES);
  const { data: shelters } = useLiveData(getShelters, MOCK_SHELTERS);
  const { data: alerts } = useLiveData(getAlerts, MOCK_ALERTS);

  const topAlert = alerts[0];
  const riskLevel = (summary.risk_level || "moderate").toLowerCase();

  return (
    <div className="h-screen flex flex-col">
      <Navbar riskLevel={riskLevel} isMock={isMock} />

      <main className="flex-1 overflow-y-auto p-5">
        <div className="max-w-md mx-auto space-y-4">
          <p className="eyebrow flex items-center gap-1.5">📍 Pune, Maharashtra</p>

          <div className="panel p-5 text-center">
            <p className="eyebrow mb-2">Current risk</p>
            <p className={`text-3xl font-mono font-bold ${RISK_STYLES[riskLevel]}`}>
              {summary.risk_level}
            </p>
          </div>

          {topAlert && (
            <div className="panel p-4 border-risk-critical/30">
              <p className="text-xs font-mono text-risk-critical uppercase mb-1">🚨 Active alert</p>
              <p className="text-sm text-white mb-1">{topAlert.zone}</p>
              <p className="text-xs text-mist-300">{topAlert.action}</p>
            </div>
          )}

          <div className="panel p-2 h-64">
            <MapView zones={zones} shelters={shelters} height="100%" />
          </div>

          <div className="grid grid-cols-1 gap-3">
            <button onClick={() => navigate("/shelters")} className="btn-primary py-3">
              Find safe route
            </button>
            <button onClick={() => navigate("/shelters")} className="btn-ghost py-3">
              Find nearest shelter
            </button>
            <button onClick={() => navigate("/")} className="btn-ghost py-3">
              View full flood map
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
