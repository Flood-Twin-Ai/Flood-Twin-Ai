import { useState } from "react";
import Navbar from "../components/Navbar.jsx";
import Sidebar from "../components/Sidebar.jsx";
import MapView from "../components/MapView.jsx";
import RiskCard from "../components/RiskCard.jsx";
import AlertPanel from "../components/AlertPanel.jsx";
import RainfallSlider from "../components/RainfallSlider.jsx";
import { RainfallChart, RiskDistributionChart } from "../components/Charts.jsx";
import { useLiveData } from "../services/useLiveData.js";
import {
  getDashboardSummary,
  getRiskMap,
  getUnsafeRoads,
  getShelters,
  getAlerts,
  getRainfallTimeline,
  simulateFlood,
} from "../services/api.js";
import {
  MOCK_SUMMARY,
  MOCK_RISK_ZONES,
  MOCK_UNSAFE_ROADS,
  MOCK_SHELTERS,
  MOCK_ALERTS,
  MOCK_RAINFALL_TIMELINE,
  MOCK_RISK_DISTRIBUTION,
  mockSimulate,
} from "../services/mockData.js";

export default function AuthorityDashboard() {
  const [activeSection, setActiveSection] = useState("map");
  const [simZones, setSimZones] = useState(null);

  const { data: summary, isMock } = useLiveData(getDashboardSummary, MOCK_SUMMARY);
  const { data: zones } = useLiveData(getRiskMap, MOCK_RISK_ZONES);
  const { data: roads } = useLiveData(getUnsafeRoads, MOCK_UNSAFE_ROADS);
  const { data: shelters } = useLiveData(getShelters, MOCK_SHELTERS);
  const { data: alerts } = useLiveData(getAlerts, MOCK_ALERTS);
  const { data: rainfall } = useLiveData(getRainfallTimeline, MOCK_RAINFALL_TIMELINE);

  const handleSimulate = async (rainfallValue, horizonMinutes) => {
    try {
      const res = await simulateFlood(rainfallValue, horizonMinutes);
      setSimZones(res.data.zones);
      return res.data;
    } catch {
      const mock = mockSimulate(rainfallValue, horizonMinutes);
      setSimZones(mock.zones);
      return mock;
    }
  };

  return (
    <div className="h-screen flex flex-col">
      <Navbar riskLevel={summary.risk_level?.toLowerCase()} isMock={isMock} />

      <div className="flex flex-1 min-h-0">
        <Sidebar active={activeSection} onSelect={setActiveSection} />

        <main className="flex-1 min-w-0 overflow-y-auto p-5 space-y-5">
          {/* KPI row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <RiskCard label="Flood risk" value={summary.risk_level} icon="🌊" />
            <RiskCard label="Rainfall" value={summary.rainfall_mm_hr} unit="mm/h" icon="🌧️" />
            <RiskCard label="Alerts" value={summary.active_alerts} icon="🚨" />
            <RiskCard label="Shelters" value={summary.active_shelters} unit="active" icon="🏠" />
          </div>

          {/* Map + Alerts */}
          <div className="grid grid-cols-1 xl:grid-cols-[1fr_360px] gap-5">
            <div className="panel p-2 h-[440px]">
              <MapView
                zones={simZones || zones}
                roads={roads}
                shelters={shelters}
                height="100%"
              />
            </div>
            <div className="h-[440px]">
              <AlertPanel alerts={alerts} />
            </div>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            <RainfallChart data={rainfall} />
            <RiskDistributionChart data={MOCK_RISK_DISTRIBUTION} />
          </div>

          {/* What-if simulator */}
          <div className="grid grid-cols-1 lg:grid-cols-[1fr_420px] gap-5">
            <div className="panel p-4 flex items-center text-sm text-mist-500">
              Drag the rainfall slider to preview how risk zones, unsafe roads and the
              recommended shelter shift over the next 30 / 60 / 120 minutes.
            </div>
            <RainfallSlider onSimulate={handleSimulate} />
          </div>
        </main>
      </div>
    </div>
  );
}
