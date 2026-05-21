interface ThreatLevelProps {
  level: number; // 0-100
  label: string;
}

export default function ThreatLevel({ level, label }: ThreatLevelProps) {
  const getColor = () => {
    if (level >= 80) return { bar: 'bg-threat-red', text: 'text-threat-red', glow: 'shadow-glow-red' };
    if (level >= 60) return { bar: 'bg-warning-amber', text: 'text-warning-amber', glow: 'shadow-glow-amber' };
    if (level >= 40) return { bar: 'bg-warning-amber-bright', text: 'text-warning-amber-bright', glow: '' };
    return { bar: 'bg-accent-green', text: 'text-accent-green', glow: 'shadow-glow-green' };
  };

  const colors = getColor();
  const shouldPulse = level >= 70;

  return (
    <div className={`bg-surface border border-border-subtle rounded-tactical p-4 ${colors.glow}`}>
      <h3 className="text-sm font-mono text-text-secondary uppercase tracking-wider mb-4 flex items-center gap-2">
        <span className="w-1 h-4 bg-warning-amber rounded-full" />
        Threat Level
      </h3>

      {/* Level Label */}
      <div className="text-center mb-3">
        <span className={`text-lg font-mono font-bold ${colors.text} ${shouldPulse ? 'animate-pulse-glow' : ''}`}>
          THREAT LEVEL: {label}
        </span>
      </div>

      {/* Gauge Bar */}
      <div className="relative h-3 bg-abyss rounded-full overflow-hidden border border-border-subtle">
        {/* Gradient background */}
        <div
          className={`absolute inset-y-0 left-0 ${colors.bar} rounded-full transition-all duration-1000`}
          style={{ width: `${level}%` }}
        />
        {/* Tick marks */}
        <div className="absolute inset-0 flex justify-between px-0.5">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="w-px h-full bg-abyss/50" />
          ))}
        </div>
      </div>

      {/* Score */}
      <div className="mt-3 flex items-center justify-between">
        <span className="text-xs text-text-muted font-mono">0</span>
        <span className={`text-2xl font-mono font-bold ${colors.text}`}>{level}</span>
        <span className="text-xs text-text-muted font-mono">100</span>
      </div>
    </div>
  );
}
