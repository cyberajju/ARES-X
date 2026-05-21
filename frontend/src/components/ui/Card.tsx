interface CardProps {
  title?: string;
  glow?: boolean;
  className?: string;
  children: React.ReactNode;
}

export default function Card({ title, glow = false, className = '', children }: CardProps) {
  return (
    <div
      className={`
        bg-surface border rounded-tactical p-4
        ${glow ? 'border-accent-cyan/30 shadow-glow-cyan' : 'border-border-subtle'}
        ${className}
      `}
    >
      {title && (
        <div className="mb-4 pb-3 border-b border-border-subtle">
          <h3 className="text-sm font-mono text-text-secondary uppercase tracking-wider flex items-center gap-2">
            <span className="w-1 h-4 bg-accent-cyan rounded-full" />
            {title}
          </h3>
        </div>
      )}
      <div>{children}</div>
    </div>
  );
}
