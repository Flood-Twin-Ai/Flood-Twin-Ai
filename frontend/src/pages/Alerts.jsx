import Navbar from "../components/Navbar.jsx";
import Sidebar from "../components/Sidebar.jsx";
import AlertPanel from "../components/AlertPanel.jsx";
import { useLiveData } from "../services/useLiveData.js";
import { getAlerts, getDashboardSummary } from "../services/api.js";
import { MOCK_ALERTS, MOCK_SUMMARY } from "../services/mockData.js";

export default function Alerts() {
  const { data: summary, isMock } = useLiveData(getDashboardSummary, MOCK_SUMMARY);
  const { data: alerts } = useLiveData(getAlerts, MOCK_ALERTS);

  return (
    <div className="h-screen flex flex-col">
      <Navbar riskLevel={summary.risk_level?.toLowerCase()} isMock={isMock} />
      <div className="flex flex-1 min-h-0">
        <Sidebar active="alerts" />
        <main className="flex-1 min-w-0 overflow-y-auto p-5">
          <div className="max-w-2xl mx-auto h-[calc(100vh-8rem)]">
            <AlertPanel alerts={alerts} />
          </div>
        </main>
      </div>
    </div>
  );
}
