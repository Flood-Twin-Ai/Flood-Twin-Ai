const RISK_TEXT = {
  low: "text-risk-low",
  moderate: "text-risk-moderate",
  high: "text-risk-high",
  critical: "text-risk-critical",
};

export default function ShelterCard({ shelter, rank, onViewRoute = () => {} }) {
  const occupancyPct = Math.round(
    ((shelter.capacity - shelter.available) / shelter.capacity) * 100
  );

  return (
    <div className="panel p-4 flex flex-col gap-2.5">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          {rank && (
            <span className="shrink-0 h-6 w-6 rounded-full bg-tide-500/15 text-tide-400 text-xs font-mono flex items-center justify-center">
              {rank}
            </span>
          )}
          <p className="text-sm font-semibold text-white truncate">{shelter.name}</p>
        </div>
        <span className={`text-[10px] font-mono uppercase shrink-0 ${RISK_TEXT[shelter.risk] || "text-mist-500"}`}>
          {shelter.risk}
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2 text-xs font-mono">
        <div>
          <p className="text-mist-500">Distance</p>
          <p className="text-mist-300">{shelter.distance_km} km</p>
        </div>
        <div>
          <p className="text-mist-500">Capacity</p>
          <p className="text-mist-300">{shelter.capacity}</p>
        </div>
        <div>
          <p className="text-mist-500">Available</p>
          <p className="text-tide-400">{shelter.available}</p>
        </div>
      </div>

      <div className="w-full h-1.5 rounded-full bg-basin-700 overflow-hidden">
        <div
          className="h-full bg-tide-500"
          style={{ width: `${occupancyPct}%` }}
          title={`${occupancyPct}% occupied`}
        />
      </div>

      <button onClick={() => onViewRoute(shelter)} className="btn-primary text-sm mt-1 w-full">
        View route
      </button>
    </div>
  );
}
