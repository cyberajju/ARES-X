import PathStep from './PathStep';
import type { AttackPathStep } from '@/lib/types';

interface PathVisualizationProps {
  steps: AttackPathStep[];
}

export default function PathVisualization({ steps }: PathVisualizationProps) {
  return (
    <div className="relative">
      {/* Start marker */}
      <div className="flex items-center gap-3 mb-2">
        <div className="w-6 h-6 rounded-full bg-accent-green/20 border-2 border-accent-green flex items-center justify-center">
          <span className="text-xs text-accent-green">{'\u25B6'}</span>
        </div>
        <span className="text-xs font-mono text-accent-green uppercase tracking-wider">
          Entry Point
        </span>
      </div>

      {/* Steps */}
      <div className="ml-3 border-l-2 border-border-subtle pl-6 space-y-0">
        {steps.map((step, index) => (
          <PathStep
            key={step.id}
            step={step}
            stepNumber={index + 1}
            isLast={index === steps.length - 1}
          />
        ))}
      </div>

      {/* End marker */}
      <div className="flex items-center gap-3 mt-2 ml-0">
        <div className="w-6 h-6 rounded-full bg-threat-red/20 border-2 border-threat-red flex items-center justify-center">
          <span className="text-xs text-threat-red">{'\u2716'}</span>
        </div>
        <span className="text-xs font-mono text-threat-red uppercase tracking-wider">
          Target Compromised
        </span>
      </div>

      {/* Animated flow indicator */}
      <div className="absolute left-[11px] top-8 bottom-8 w-0.5 overflow-hidden">
        <div className="w-full h-8 bg-gradient-to-b from-transparent via-accent-cyan to-transparent animate-data-stream" />
      </div>
    </div>
  );
}
