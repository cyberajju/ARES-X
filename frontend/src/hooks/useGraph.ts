'use client';

import { useState, useMemo } from 'react';
import type { GraphNode, GraphEdge } from '@/lib/types';

const mockNodes: GraphNode[] = [
  { id: 'fw-01', label: 'FW-Primary', type: 'firewall', x: 400, y: 80, criticality: 'high' },
  { id: 'lb-01', label: 'LB-External', type: 'load_balancer', x: 400, y: 180, criticality: 'high' },
  { id: 'web-01', label: 'WEBSVR-01', type: 'server', x: 250, y: 280, criticality: 'medium' },
  { id: 'web-02', label: 'WEBSVR-02', type: 'server', x: 550, y: 280, criticality: 'medium' },
  { id: 'app-01', label: 'APPSVR-01', type: 'server', x: 200, y: 400, criticality: 'high' },
  { id: 'app-02', label: 'APPSVR-02', type: 'server', x: 400, y: 400, criticality: 'high' },
  { id: 'app-03', label: 'APPSVR-03', type: 'server', x: 600, y: 400, criticality: 'medium' },
  { id: 'db-01', label: 'PROD-DB-01', type: 'database', x: 250, y: 520, criticality: 'critical' },
  { id: 'db-02', label: 'PROD-DB-02', type: 'database', x: 550, y: 520, criticality: 'critical' },
  { id: 'ad-01', label: 'AD-Controller', type: 'server', x: 100, y: 400, criticality: 'critical' },
  { id: 'dns-01', label: 'DNS-Internal', type: 'server', x: 700, y: 180, criticality: 'medium' },
  { id: 'vpn-01', label: 'VPN-Gateway', type: 'firewall', x: 100, y: 180, criticality: 'high' },
];

const mockEdges: GraphEdge[] = [
  { id: 'e1', source: 'fw-01', target: 'lb-01', type: 'connection' },
  { id: 'e2', source: 'lb-01', target: 'web-01', type: 'connection' },
  { id: 'e3', source: 'lb-01', target: 'web-02', type: 'connection' },
  { id: 'e4', source: 'web-01', target: 'app-01', type: 'connection' },
  { id: 'e5', source: 'web-01', target: 'app-02', type: 'connection' },
  { id: 'e6', source: 'web-02', target: 'app-02', type: 'connection' },
  { id: 'e7', source: 'web-02', target: 'app-03', type: 'connection' },
  { id: 'e8', source: 'app-01', target: 'db-01', type: 'connection' },
  { id: 'e9', source: 'app-02', target: 'db-01', type: 'connection' },
  { id: 'e10', source: 'app-02', target: 'db-02', type: 'connection' },
  { id: 'e11', source: 'app-03', target: 'db-02', type: 'connection' },
  { id: 'e12', source: 'vpn-01', target: 'ad-01', type: 'authentication' },
  { id: 'e13', source: 'ad-01', target: 'app-01', type: 'authentication' },
  { id: 'e14', source: 'fw-01', target: 'dns-01', type: 'connection' },
  { id: 'e15', source: 'dns-01', target: 'web-02', type: 'connection' },
];

interface UseGraphOptions {
  typeFilter?: string;
}

interface UseGraphReturn {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selectedNode: GraphNode | null;
  selectNode: (node: GraphNode | null) => void;
  loading: boolean;
}

export function useGraph(options: UseGraphOptions = {}): UseGraphReturn {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [loading] = useState(false);

  const nodes = useMemo(() => {
    if (!options.typeFilter || options.typeFilter === 'all') return mockNodes;
    return mockNodes.filter((n) => n.type === options.typeFilter);
  }, [options.typeFilter]);

  const edges = useMemo(() => {
    const nodeIds = new Set(nodes.map((n) => n.id));
    return mockEdges.filter((e) => nodeIds.has(e.source) && nodeIds.has(e.target));
  }, [nodes]);

  return {
    nodes,
    edges,
    selectedNode,
    selectNode: setSelectedNode,
    loading,
  };
}

export default useGraph;
