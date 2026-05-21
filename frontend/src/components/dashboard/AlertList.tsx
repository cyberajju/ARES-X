import Badge from '@/components/ui/Badge';

interface Alert {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  message: string;
  timestamp: string;
  source: string;
}

interface AlertListProps {
  alerts: Alert[];
}

const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 };

export default function AlertList({ alerts }: AlertListProps) {
  const sortedAlerts = [...alerts].sort(
    (a, b) => severityOrder[a.severity] - severityOrder[b.severity]
  );

  return (
    <div className="bg-surface border border-border-subtle rounded-tactical">
      <div className="p-4 border-b border-border-subtle">
        <h3 className="text-sm font-mono text-text-secondary uppercase tracking-wider flex items-center gap-2">
          <span className="w-1 h-4 bg-threat-red rounded-full" />
          Recent Alerts
          <span className="ml-auto text-xs text-text-muted">{alerts.length} active</span>
        </h3>
      </div>

      <div className="divide-y divide-border-subtle/50 max-h-80 overflow-y-auto">
        {sortedAlerts.map((alert, index) => (
          <div
            key={alert.id}
            className="p-3 hover:bg-elevated/30 transition-colors animate-fade-in"
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <div className="flex items-start gap-3">
              {/* Severity dot */}
              <div className={`
                mt-1 w-2 h-2 rounded-full flex-shrink-0
                ${alert.severity === 'critical' ? 'bg-threat-red animate-threat-pulse' :
                  alert.severity === 'high' ? 'bg-warning-amber' :
                  alert.severity === 'medium' ? 'bg-warning-amber-bright' :
                  'bg-accent-green'}
              `} />

              {/* Content */}
              <div className="flex-1 min-w-0">
                <p className="text-sm text-text-primary leading-tight">{alert.message}</p>
                <div className="mt-1 flex items-center gap-3 text-xs text-text-muted">
                  <span className="font-mono">{alert.source}</span>
                  <span>{alert.timestamp}</span>
                </div>
              </div>

              {/* Badge */}
              <Badge variant={alert.severity} className="flex-shrink-0">
                {alert.severity}
              </Badge>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
