import type { AttackPathStep } from '@/lib/types';
import Badge from '@/components/ui/Badge';

interface PathStepProps {
  step: AttackPathStep;
  stepNumber: number;
  isLast: boolean;
}

export default function PathStep({ step, stepNumber, isLast }: PathStepProps) {
  const getRiskColor = (risk: number) => {
    if (risk >= 80) return 'border-threat-red bg-threat-red/10 text-threat-red';
    if (risk >= 60) return 'border-warning-amber bg-warning-amber/10 text-warning-amber';
    if (risk >= 40) return 'border-warning-amber-bright bg-warning-amber-bright/10 text-warning-amber-bright';
    return 'border-accent-green bg-accent-green/10 text-accent-green';
  };

  const getRiskBadgeVariant = (risk: number): 'critical' | 'high' | 'medium' | 'low' => {
    if (risk >= 80) return 'critical';
    if (risk >= 60) return 'high';
    if (risk >= 40) return 'medium';
    return 'low';
  };

  return (
    <div className={`relative pb-6 ${isLast ? 'pb-2' : ''}`}>
      {/* Step node */}
      <div className="flex items-start gap-4">
        {/* Circular node */}
        <div className={`
          relative -ml-9 w-6 h-6 rounded-full border-2 flex items-center justify-center flex-shrink-0
          ${getRiskColor(step.cumulativeRisk)}
        `}>
          <span className="text-xs font-mono font-bold">{stepNumber}</span>
        </div>

        {/* Step content */}
        <div className="flex-1 bg-elevated border border-border-subtle rounded-tactical p-3 space-y-2">
          <div className="flex items-center justify-between">
            <span className="font-mono text-sm text-text-primary">
              {step.nodeName}
            </span>
            <Badge variant={getRiskBadgeVariant(step.cumulativeRisk)}>
              {step.cumulativeRisk}%
            </Badge>
          </div>

          <div className="flex items-center gap-3 text-xs">
            <span className="text-text-muted capitalize">{step.nodeType}</span>
            <span className="text-text-muted">|</span>
            <span className="text-accent-cyan font-mono">{step.technique}</span>
          </div>

          <div className="flex items-center gap-2 text-xs text-text-muted">
            <span>Step probability: </span>
            <span className="font-mono text-text-secondary">
              {(step.probability * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
