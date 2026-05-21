interface StatusIndicatorProps {
  status: 'online' | 'offline' | 'degraded' | 'unknown';
  size?: 'sm' | 'md' | 'lg';
  label?: string;
}

const statusColors = {
  online: 'bg-accent-green',
  offline: 'bg-threat-red',
  degraded: 'bg-warning-amber',
  unknown: 'bg-text-muted',
};

const statusRingColors = {
  online: 'bg-accent-green/40',
  offline: 'bg-threat-red/40',
  degraded: 'bg-warning-amber/40',
  unknown: 'bg-text-muted/40',
};

const sizeStyles = {
  sm: 'w-2 h-2',
  md: 'w-3 h-3',
  lg: 'w-4 h-4',
};

const ringSizeStyles = {
  sm: 'w-3 h-3',
  md: 'w-4 h-4',
  lg: 'w-5 h-5',
};

export default function StatusIndicator({ status, size = 'md', label }: StatusIndicatorProps) {
  const shouldPulse = status === 'online' || status === 'degraded';

  return (
    <div className="inline-flex items-center gap-2">
      <span className="relative inline-flex">
        <span className={`${sizeStyles[size]} rounded-full ${statusColors[status]}`} />
        {shouldPulse && (
          <span
            className={`
              absolute inset-0 rounded-full
              ${statusRingColors[status]}
              ${status === 'online' ? 'animate-ping' : 'animate-pulse'}
            `}
            style={{ animationDuration: status === 'degraded' ? '2s' : '1.5s' }}
          />
        )}
      </span>
      {label && (
        <span className="text-xs text-text-secondary capitalize">{label}</span>
      )}
    </div>
  );
}
