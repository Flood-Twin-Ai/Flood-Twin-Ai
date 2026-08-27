import { Link, useLocation } from "react-router-dom";

const RISK_STYLES = {
  low: "bg-risk-low/15 text-risk-low border-risk-low/30",
  moderate: "bg-risk-moderate/15 text-risk-moderate border-risk-moderate/30",
  high: "bg-risk-high/15 text-risk-high border-risk-high/30",
  critical: "bg-risk-critical/15 text-risk-critical border-risk-critical/30",
};

export default function Navbar({ riskLevel = "high", isMock = true }) {
  const location = useLocation();

  const links = [
    { to: "/", label: "Authority" },
    { to: "/citizen", label: "Citizen" },
    { to: "/alerts", label: "Alerts" },
    { to: "/shelters", label: "Shelters" },
  ];

  return (
    <header className="h-16 shrink-0 border-b border-basin-700 bg-basin-900/90 backdrop-blur px-6 flex items-center justify-between">
      <div className="flex items-center gap-8">
        <Link to="/" className="flex items-center gap-2.5">
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-pulseDot absolute inline-flex h-full w-full rounded-full bg-tide-500" />
          </span>
          <span className="font-mono font-semibold tracking-wide text-white text-[15px]">
            JAL-DRISHTI
          </span>
          <span className="hidden sm:inline text-[11px] text-mist-500 font-mono">
            AI URBAN FLOOD DECISION SYSTEM
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-1">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                location.pathname === l.to
                  ? "bg-basin-700 text-white"
                  : "text-mist-500 hover:text-mist-300 hover:bg-basin-800"
              }`}
            >
              {l.label}
            </Link>
          ))}
        </nav>
      </div>

      <div className="flex items-center gap-3">
        {isMock && (
          <span className="hidden sm:inline text-[10px] font-mono uppercase tracking-wider text-mist-500 border border-basin-700 rounded-full px-2 py-1">
            demo data
          </span>
        )}
        <span
          className={`text-xs font-mono uppercase tracking-wider border rounded-full px-3 py-1 ${RISK_STYLES[riskLevel] || RISK_STYLES.moderate}`}
        >
          Flood status: {riskLevel}
        </span>
        <div className="h-8 w-8 rounded-full bg-basin-700 flex items-center justify-center text-mist-300 text-xs font-mono">
          AU
        </div>
      </div>
    </header>
  );
}
