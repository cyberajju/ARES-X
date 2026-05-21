interface BadgeProps {
  variant: 'critical' | 'high' | 'medium' | 'low' | 'info';
  pulse?: boolean;
  className?: string;
  children: React.ReactNode;
}

const variantStyles = {
  critical: 'bg-threat-red/20 text-threat-red border-threat-red/40',
  high: 'bg-warning-amber/20 text-warning-amber border-warning-amber/40',
  medium: 'bg-warning-amber-bright/20 text-warning-amber-bright border-warning-amber-bright/40',
  low: 'bg-accent-green/20 text-accent-green border-accent-green/40',
  info: 'bg-accent-cyan/20 text-accent-cyan border-accent-cyan/40',
};

export default function Badge({ variant, pulse = false, className = '', children }: BadgeProps) {
  const shouldPulse = pulse || variant === 'critical';

  return (
    <span
      className={`
        inline-flex items-center gap-1 px-2 py-0.5
        text-xs font-mono font-medium uppercase tracking-wider
        border rounded-tactical
        ${variantStyles[variant]}
        ${shouldPulse ? 'animate-threat-pulse' : ''}
        ${className}
      `}
    >
      {children}
    </span>
  );
}
