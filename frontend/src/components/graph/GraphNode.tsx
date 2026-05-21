'use client';

import type { GraphNode as GraphNodeType } from '@/lib/types';

interface GraphNodeProps {
  node: GraphNodeType;
  isSelected: boolean;
  onClick: () => void;
}

const typeColors: Record<string, string> = {
  server: '#06b6d4',
  database: '#a855f7',
  firewall: '#f97316',
  load_balancer: '#3b82f6',
  workstation: '#6b7280',
  storage: '#8b5cf6',
};

const criticalityRadius: Record<string, number> = {
  critical: 22,
  high: 20,
  medium: 18,
  low: 16,
};

export default function GraphNode({ node, isSelected, onClick }: GraphNodeProps) {
  const color = typeColors[node.type] || '#06b6d4';
  const radius = criticalityRadius[node.criticality] || 18;

  return (
    <g
      onClick={onClick}
      className="cursor-pointer"
      style={{ transition: 'transform 0.2s' }}
    >
      {/* Glow effect for selected */}
      {isSelected && (
        <circle
          cx={node.x}
          cy={node.y}
          r={radius + 8}
          fill="none"
          stroke={color}
          strokeWidth="2"
          opacity="0.4"
        >
          <animate
            attributeName="r"
            values={`${radius + 6};${radius + 10};${radius + 6}`}
            dur="2s"
            repeatCount="indefinite"
          />
          <animate
            attributeName="opacity"
            values="0.4;0.1;0.4"
            dur="2s"
            repeatCount="indefinite"
          />
        </circle>
      )}

      {/* Outer ring - criticality indicator */}
      <circle
        cx={node.x}
        cy={node.y}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth={node.criticality === 'critical' ? 3 : 2}
        opacity={isSelected ? 1 : 0.7}
      />

      {/* Inner circle */}
      <circle
        cx={node.x}
        cy={node.y}
        r={radius - 5}
        fill="#0f1623"
        stroke={color}
        strokeWidth="1"
        opacity="0.9"
      />

      {/* Type icon/label (first letter) */}
      <text
        x={node.x}
        y={node.y}
        textAnchor="middle"
        dominantBaseline="central"
        fill={color}
        fontSize="10"
        fontFamily="monospace"
        fontWeight="bold"
      >
        {node.type.charAt(0).toUpperCase()}
      </text>

      {/* Label below */}
      <text
        x={node.x}
        y={node.y + radius + 14}
        textAnchor="middle"
        fill="#94a3b8"
        fontSize="9"
        fontFamily="monospace"
      >
        {node.label}
      </text>
    </g>
  );
}
