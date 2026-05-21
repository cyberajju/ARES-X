'use client';

import GraphNode from './GraphNode';
import GraphEdge from './GraphEdge';
import type { GraphNode as GraphNodeType, GraphEdge as GraphEdgeType } from '@/lib/types';

interface GraphCanvasProps {
  nodes: GraphNodeType[];
  edges: GraphEdgeType[];
  zoom: number;
  onNodeSelect: (node: GraphNodeType | null) => void;
  selectedNodeId: string | null;
}

export default function GraphCanvas({
  nodes,
  edges,
  zoom,
  onNodeSelect,
  selectedNodeId,
}: GraphCanvasProps) {
  const viewBoxWidth = 800 / zoom;
  const viewBoxHeight = 600 / zoom;
  const offsetX = (800 - viewBoxWidth) / 2;
  const offsetY = (600 - viewBoxHeight) / 2;

  const getNodeById = (id: string) => nodes.find((n) => n.id === id);

  return (
    <svg
      viewBox={`${offsetX} ${offsetY} ${viewBoxWidth} ${viewBoxHeight}`}
      className="w-full h-full"
      style={{ background: '#0a0e17' }}
    >
      {/* Grid Pattern */}
      <defs>
        <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
          <path
            d="M 50 0 L 0 0 0 50"
            fill="none"
            stroke="#1e3a5f"
            strokeWidth="0.3"
            opacity="0.3"
          />
        </pattern>
        <marker
          id="arrowhead"
          markerWidth="10"
          markerHeight="7"
          refX="10"
          refY="3.5"
          orient="auto"
        >
          <polygon points="0 0, 10 3.5, 0 7" fill="#1e3a5f" />
        </marker>
        <marker
          id="arrowhead-active"
          markerWidth="10"
          markerHeight="7"
          refX="10"
          refY="3.5"
          orient="auto"
        >
          <polygon points="0 0, 10 3.5, 0 7" fill="#06b6d4" />
        </marker>
      </defs>

      {/* Background Grid */}
      <rect width="800" height="600" fill="url(#grid)" />

      {/* Edges */}
      {edges.map((edge) => {
        const source = getNodeById(edge.source);
        const target = getNodeById(edge.target);
        if (!source || !target) return null;
        const isActive = selectedNodeId === edge.source || selectedNodeId === edge.target;
        return (
          <GraphEdge
            key={edge.id}
            edge={edge}
            sourceX={source.x}
            sourceY={source.y}
            targetX={target.x}
            targetY={target.y}
            isActive={isActive}
          />
        );
      })}

      {/* Nodes */}
      {nodes.map((node) => (
        <GraphNode
          key={node.id}
          node={node}
          isSelected={selectedNodeId === node.id}
          onClick={() => onNodeSelect(selectedNodeId === node.id ? null : node)}
        />
      ))}
    </svg>
  );
}
