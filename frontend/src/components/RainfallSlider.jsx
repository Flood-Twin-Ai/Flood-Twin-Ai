import { useState } from "react";

const RISK_TEXT = {
  low: "text-risk-low",
  moderate: "text-risk-moderate",
  high: "text-risk-high",
  critical: "text-risk-critical",
};

const RISK_BAR = {
  low: "bg-risk-low w-1/4",
  moderate: "bg-risk-moderate w-2/4",
  high: "bg-risk-high w-3/4",
  critical: "bg-risk-critical w-full",
};

export default function RainfallSlider({ onSimulate = async () => null }) {
  const [rainfall, setRainfall] = useState(45);
  const [horizon, setHorizon] = useState(60);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const runSimulation = async (value = rainfall, horizonValue = horizon) => {
    setLoading(true);
    const res = await onSimulate(value, horizonValue);
    setResult(res);
    setLoading(false);
  };

  return (
    <div className="panel p-4">
      <div className="flex items-center justify-between mb-3">
        <p className="eyebrow">What-if flood simulator</p>
        <span className="text-[10px] font-mono text-mist-500">judges can drag me</span>
      </div>

      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-mist-500 font-mono">Rainfall intensity</span>
        <span className="text-sm font-mono text-tide-400">{rainfall} mm/h</span>
      </div>
      <input
        type="range"
        min="20"
        max="100"
        value={rainfall}
        onChange={(e) => setRainfall(Number(e.target.value))}
        onMouseUp={() => runSimulation()}
        onTouchEnd={() => runSimulation()}
        className="w-full accent-tide-500"
      />

      <div className="flex items-center gap-2 mt-3 mb-4">
        {[30, 60, 120].map((h) => (
          <button
            key={h}
            onClick={() => {
              setHorizon(h);
              runSimulation(rainfall, h);
            }}
            className={`text-xs font-mono px-2.5 py-1 rounded-md border ${
              horizon === h
                ? "border-tide-500 text-tide-400 bg-tide-500/10"
                : "border-basin-700 text-mist-500 hover:text-mist-300"
            }`}
          >
            {h} min
          </button>
        ))}
      </div>

      <button onClick={() => runSimulation()} disabled={loading} className="btn-primary text-sm w-full mb-4">
        {loading ? "Simulating…" : "Simulate"}
      </button>

      {result && (
        <div className="space-y-3 border-t border-basin-700 pt-3">
          <Row label="Prediction window" value={`${result.horizon_minutes} minutes`} />
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-mist-500 font-mono">Risk</span>
              <span className={`text-xs font-mono uppercase ${RISK_TEXT[result.risk_level]}`}>
                {result.risk_level}
              </span>
            </div>
            <div className="h-2 rounded-full bg-basin-700 overflow-hidden">
              <div className={`h-full rounded-full transition-all duration-500 ${RISK_BAR[result.risk_level]}`} />
            </div>
          </div>
          <Row label="Unsafe roads" value={result.unsafe_road_count} />
          <Row label="Recommended shelter" value={result.recommended_shelter} />
        </div>
      )}
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex items-center justify-between">
      <span className="text-xs text-mist-500 font-mono">{label}</span>
      <span className="text-xs text-white font-mono text-right max-w-[60%] truncate">{value}</span>
    </div>
  );
}
