import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  BarChart,
  Bar,
  Cell,
} from "recharts";

const RISK_COLORS = {
  low: "#34D399",
  moderate: "#FBBF24",
  high: "#F97316",
  critical: "#EF4444",
};

const tooltipStyle = {
  background: "#111A2C",
  border: "1px solid #1B2740",
  borderRadius: 8,
  fontFamily: "IBM Plex Mono, monospace",
  fontSize: 12,
  color: "#B7C3D9",
};

export function RainfallChart({ data = [] }) {
  return (
    <div className="panel p-4">
      <div className="flex items-center justify-between mb-2">
        <p className="eyebrow">Rainfall timeline</p>
        <div className="flex items-center gap-3 text-[10px] font-mono text-mist-500">
          <span className="flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-tide-500" /> actual
          </span>
          <span className="flex items-center gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-risk-moderate" /> predicted
          </span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data} margin={{ top: 5, right: 8, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="actualFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#2DD4BF" stopOpacity={0.35} />
              <stop offset="95%" stopColor="#2DD4BF" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="predictedFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#FBBF24" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#FBBF24" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#1B2740" vertical={false} />
          <XAxis
            dataKey="minute"
            tickFormatter={(v) => `${v}m`}
            stroke="#7C8AA8"
            fontSize={11}
            fontFamily="IBM Plex Mono, monospace"
            tickLine={false}
          />
          <YAxis stroke="#7C8AA8" fontSize={11} fontFamily="IBM Plex Mono, monospace" tickLine={false} width={30} />
          <Tooltip contentStyle={tooltipStyle} labelFormatter={(v) => `t + ${v} min`} />
          <Area type="monotone" dataKey="actual" stroke="#2DD4BF" strokeWidth={2} fill="url(#actualFill)" connectNulls />
          <Area
            type="monotone"
            dataKey="predicted"
            stroke="#FBBF24"
            strokeWidth={2}
            strokeDasharray="4 3"
            fill="url(#predictedFill)"
            connectNulls
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export function RiskDistributionChart({ data = [] }) {
  return (
    <div className="panel p-4">
      <p className="eyebrow mb-2">Zone risk distribution</p>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 5, right: 8, left: -20, bottom: 0 }}>
          <CartesianGrid stroke="#1B2740" vertical={false} />
          <XAxis
            dataKey="name"
            stroke="#7C8AA8"
            fontSize={11}
            fontFamily="IBM Plex Mono, monospace"
            tickLine={false}
          />
          <YAxis stroke="#7C8AA8" fontSize={11} fontFamily="IBM Plex Mono, monospace" tickLine={false} width={30} />
          <Tooltip contentStyle={tooltipStyle} cursor={{ fill: "rgba(255,255,255,0.03)" }} />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((entry, i) => (
              <Cell key={i} fill={RISK_COLORS[entry.level] || "#2DD4BF"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
