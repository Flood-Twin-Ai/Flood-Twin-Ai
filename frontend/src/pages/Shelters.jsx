import { useState } from "react";
import Navbar from "../components/Navbar.jsx";
import Sidebar from "../components/Sidebar.jsx";
import MapView from "../components/MapView.jsx";
import ShelterCard from "../components/ShelterCard.jsx";
import RoutePanel from "../components/RoutePanel.jsx";
import { useLiveData } from "../services/useLiveData.js";
import { getShelters, getDashboardSummary, getSafeRoute } from "../services/api.js";
import { MOCK_SHELTERS, MOCK_SUMMARY } from "../services/mockData.js";

export default function Shelters() {
  const { data: summary, isMock } = useLiveData(getDashboardSummary, MOCK_SUMMARY);
  const { data: shelters } = useLiveData(getShelters, MOCK_SHELTERS);
  const [selectedShelter, setSelectedShelter] = useState(null);

  // Rank: safety (low risk first) -> distance -> availability
  const ranked = [...shelters].sort((a, b) => {
    const riskOrder = { low: 0, moderate: 1, high: 2, critical: 3 };
    if (riskOrder[a.risk] !== riskOrder[b.risk]) return riskOrder[a.risk] - riskOrder[b.risk];
    if (a.distance_km !== b.distance_km) return a.distance_km - b.distance_km;
    return b.available - a.available;
  });

  const handleFindRoute = async (from, to) => {
    try {
      const res = await getSafeRoute(from, to);
      return res.data;
    } catch {
      return { distance_km: 2.4, duration_min: 9, risk: "low" };
    }
  };

  return (
    <div className="h-screen flex flex-col">
      <Navbar riskLevel={summary.risk_level?.toLowerCase()} isMock={isMock} />
      <div className="flex flex-1 min-h-0">
        <Sidebar active="shelters" />
        <main className="flex-1 min-w-0 overflow-y-auto p-5 space-y-5">
          <div className="grid grid-cols-1 xl:grid-cols-[1fr_380px] gap-5">
            <div className="panel p-2 h-[420px]">
              <MapView shelters={shelters} height="100%" />
            </div>
            <RoutePanel
              onFindRoute={handleFindRoute}
              defaultTo={selectedShelter?.name || ""}
            />
          </div>

          <div>
            <p className="eyebrow mb-3">Shelters near you</p>
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
              {ranked.map((s, i) => (
                <ShelterCard
                  key={s.id}
                  shelter={s}
                  rank={i + 1}
                  onViewRoute={setSelectedShelter}
                />
              ))}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
