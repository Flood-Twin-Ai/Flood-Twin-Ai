const LEVEL_STYLES = {
  low: "border-risk-low/40 bg-risk-low/5",
  moderate: "border-risk-moderate/40 bg-risk-moderate/5",
  high: "border-risk-high/40 bg-risk-high/5",
  critical: "border-risk-critical/40 bg-risk-critical/5",
};

const LEVEL_DOT = {
  low: "bg-risk-low",
  moderate: "bg-risk-moderate",
  high: "bg-risk-high",
  critical: "bg-risk-critical",
};

export default function AlertPanel({ alerts = [], compact = false }) {
  return (
    <div className="panel p-4 h-full flex flex-col">
      <div className="flex items-center justify-between mb-3">
        <p className="eyebrow">Explainable alerts</p>
        <span className="text-xs font-mono text-mist-500">{alerts.length} active</span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
        {alerts.length === 0 && (
          <p className="text-sm text-mist-500 py-6 text-center">No active alerts right now.</p>
        )}
        {alerts.map((a) => (
          <div
            key={a.id}
            className={`rounded-lg border px-3.5 py-3 ${LEVEL_STYLES[a.level] || LEVEL_STYLES.moderate}`}
          >
            <div className="flex items-center gap-2 mb-1.5">
              <span className={`h-1.5 w-1.5 rounded-full ${LEVEL_DOT[a.level]} animate-pulseDot`} />
              <p className="text-sm font-semibold text-white">{a.zone}</p>
              <span className="ml-auto text-[10px] font-mono uppercase text-mist-500">
                {a.level}
              </span>
            </div>
            <p className="text-xs text-mist-300 mb-1">
              <span className="text-mist-500">Cause — </span>
              {a.cause}
            </p>
            {!compact && (
              <p className="text-xs text-mist-300">
                <span className="text-mist-500">Action — </span>
                {a.action}
              </p>
            )}
            <p className="text-[10px] text-mist-500 font-mono mt-1.5">
              Updated {a.updated_minutes_ago} min ago
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
