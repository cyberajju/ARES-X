interface StatCardProps {
  label: string;
  value: string;
  trend: string;
  trendUp: boolean;
  color: 'cyan' | 'red' | 'amber' | 'green';
}

const colorStyles = {
  cyan: 'border-accent-cyan/30 shadow-glow-cyan',
  red: 'border-threat-red/30 shadow-glow-red',
  amber: 'border-warning-amber/30 shadow-glow-amber',
  green: 'border-accent-green/30 shadow-glow-green',
};

const valueColors = {
  cyan: 'text-accent-cyan',
  red: 'text-threat-red',
  amber: 'text-warning-amber',
  green: 'text-accent-green',
};

export default function StatCard({ label, value, trend, trendUp, color }: StatCardProps) {
  return (
    <div className={`
      bg-surface border rounded-tactical p-4 grid-bg relative overflow-hidden
      ${colorStyles[color]}
    `}>
      {/* Value */}
      <div className={`text-3xl font-mono font-bold ${valueColors[color]}`}>
        {value}
      </div>

      {/* Label */}
      <div className="text-sm text-text-secondary mt-1">{label}</div>

      {/* Trend */}
      <div className="mt-2 flex items-center gap-1">
        <span className={`text-xs font-mono ${trendUp ? 'text-accent-green' : 'text-threat-red'}`}>
          {trendUp ? '\u2191' : '\u2193'} {trend}
        </span>
        <span className="text-xs text-text-muted">vs last hour</span>
      </div>
    </div>
  );
}
