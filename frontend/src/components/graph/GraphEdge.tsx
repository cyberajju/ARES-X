import type { GraphEdge as GraphEdgeType } from '@/lib/types';

interface GraphEdgeProps {
  edge: GraphEdgeType;
  sourceX: number;
  sourceY: number;
  targetX: number;
  targetY: number;
  isActive: boolean;
}

export default function GraphEdge({
  edge,
  sourceX,
  sourceY,
  targetX,
  targetY,
  isActive,
}: GraphEdgeProps) {
  const isDashed = edge.type === 'authentication';
  const color = isActive ? '#06b6d4' : '#1e3a5f';
  const markerId = isActive ? 'url(#arrowhead-active)' : 'url(#arrowhead)';

  // Shorten line to not overlap with node circles
  const dx = targetX - sourceX;
  const dy = targetY - sourceY;
  const length = Math.sqrt(dx * dx + dy * dy);
  const nodeRadius = 22;
  const startX = sourceX + (dx / length) * nodeRadius;
  const startY = sourceY + (dy / length) * nodeRadius;
  const endX = targetX - (dx / length) * nodeRadius;
  const endY = targetY - (dy / length) * nodeRadius;

  return (
    <g>
      <line
        x1={startX}
        y1={startY}
        x2={endX}
        y2={endY}
        stroke={color}
        strokeWidth={isActive ? 2 : 1}
        strokeDasharray={isDashed ? '6,4' : undefined}
        markerEnd={markerId}
        opacity={isActive ? 1 : 0.6}
      >
        {isActive && isDashed && (
          <animate
            attributeName="stroke-dashoffset"
            values="0;20"
            dur="1s"
            repeatCount="indefinite"
          />
        )}
      </line>
    </g>
  );
}
