const RISK_STYLES = {
  low: { text: "text-risk-low", ring: "ring-risk-low/30", bg: "bg-risk-low/10" },
  moderate: { text: "text-risk-moderate", ring: "ring-risk-moderate/30", bg: "bg-risk-moderate/10" },
  high: { text: "text-risk-high", ring: "ring-risk-high/30", bg: "bg-risk-high/10" },
  critical: { text: "text-risk-critical", ring: "ring-risk-critical/30", bg: "bg-risk-critical/10" },
};

export default function RiskCard({ label, value, unit, icon, tone = "neutral" }) {
  const riskStyle = RISK_STYLES[String(value).toLowerCase()];

  return (
    <div className="panel p-4 flex items-center gap-4">
      <div
        className={`h-11 w-11 rounded-lg flex items-center justify-center text-lg shrink-0 ${
          riskStyle ? `${riskStyle.bg} ring-1 ${riskStyle.ring}` : "bg-basin-700"
        }`}
      >
        {icon}
      </div>
      <div className="min-w-0">
        <p className="eyebrow">{label}</p>
        <p
          className={`stat-value text-xl leading-tight truncate ${
            riskStyle ? riskStyle.text : "text-white"
          }`}
        >
          {value}
          {unit && <span className="text-sm text-mist-500 font-normal ml-1">{unit}</span>}
        </p>
      </div>
    </div>
  );
}
