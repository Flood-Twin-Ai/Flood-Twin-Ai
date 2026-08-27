import { useState } from "react";

export default function RoutePanel({ onFindRoute = async () => null, defaultTo = "" }) {
  const [from, setFrom] = useState("Current location");
  const [to, setTo] = useState(defaultTo);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [rerouted, setRerouted] = useState(false);

  const handleFind = async () => {
    setLoading(true);
    setRerouted(false);
    const res = await onFindRoute(from, to);
    setResult(res);
    setLoading(false);
  };

  return (
    <div className="panel p-4 flex flex-col gap-3">
      <p className="eyebrow">Safe route</p>

      <div className="space-y-2">
        <Field label="From" value={from} onChange={setFrom} />
        <Field label="To" value={to} onChange={setTo} placeholder="Choose a shelter or address" />
      </div>

      <button onClick={handleFind} disabled={loading || !to} className="btn-primary text-sm disabled:opacity-40">
        {loading ? "Calculating…" : "Find safe route"}
      </button>

      {result && (
        <div className="mt-1 rounded-lg border border-tide-500/30 bg-tide-500/5 p-3.5 space-y-2">
          {rerouted && (
            <p className="text-xs text-risk-moderate font-mono">
              ⚠ Previous route unsafe — new safest route calculated.
            </p>
          )}
          <div className="grid grid-cols-3 gap-2 text-xs font-mono">
            <div>
              <p className="text-mist-500">Distance</p>
              <p className="text-white">{result.distance_km} km</p>
            </div>
            <div>
              <p className="text-mist-500">Time</p>
              <p className="text-white">{result.duration_min} min</p>
            </div>
            <div>
              <p className="text-mist-500">Risk</p>
              <p className="text-risk-low uppercase">{result.risk}</p>
            </div>
          </div>
          <button
            onClick={() => setRerouted((prev) => !prev)}
            className="btn-ghost text-sm w-full"
            title="Demo: simulate a live reroute event"
          >
            Start navigation
          </button>
        </div>
      )}
    </div>
  );
}

function Field({ label, value, onChange, placeholder }) {
  return (
    <label className="block">
      <span className="text-xs text-mist-500 font-mono">{label}</span>
      <input
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full bg-basin-900 border border-basin-700 rounded-lg px-3 py-2 text-sm text-white placeholder:text-mist-500 focus:border-tide-500 outline-none"
      />
    </label>
  );
}
