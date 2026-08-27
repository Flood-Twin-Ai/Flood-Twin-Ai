const ITEMS = [
  { key: "map", label: "Live Map", icon: "🗺️" },
  { key: "alerts", label: "Alerts", icon: "🚨" },
  { key: "routes", label: "Routes", icon: "🛣️" },
  { key: "shelters", label: "Shelters", icon: "🏠" },
];

export default function Sidebar({ active = "map", onSelect = () => {} }) {
  return (
    <aside className="hidden lg:flex w-56 shrink-0 flex-col border-r border-basin-700 bg-basin-900/60 py-6 px-3 gap-1">
      <p className="eyebrow px-3 mb-2">Navigate</p>
      {ITEMS.map((item) => (
        <button
          key={item.key}
          onClick={() => onSelect(item.key)}
          className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-left transition-colors ${
            active === item.key
              ? "bg-tide-500/10 text-tide-400 border border-tide-500/30"
              : "text-mist-500 hover:bg-basin-800 hover:text-mist-300 border border-transparent"
          }`}
        >
          <span className="text-base leading-none">{item.icon}</span>
          {item.label}
        </button>
      ))}

      <div className="mt-auto pt-6 px-3">
        <div className="panel p-3">
          <p className="eyebrow mb-2">Map legend</p>
          <LegendRow color="bg-risk-low" label="Low risk" />
          <LegendRow color="bg-risk-moderate" label="Moderate" />
          <LegendRow color="bg-risk-high" label="High" />
          <LegendRow color="bg-risk-critical" label="Critical" />
        </div>
      </div>
    </aside>
  );
}

function LegendRow({ color, label }) {
  return (
    <div className="flex items-center gap-2 py-0.5">
      <span className={`h-2 w-2 rounded-full ${color}`} />
      <span className="text-xs text-mist-500">{label}</span>
    </div>
  );
}
