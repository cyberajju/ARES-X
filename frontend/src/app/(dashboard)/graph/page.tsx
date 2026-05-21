'use client';

import { useState } from 'react';
import GraphCanvas from '@/components/graph/GraphCanvas';
import Card from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import type { GraphNode as GraphNodeType, GraphEdge as GraphEdgeType } from '@/lib/types';

const mockNodes: GraphNodeType[] = [
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

const mockEdges: GraphEdgeType[] = [
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

export default function GraphPage() {
  const [selectedNode, setSelectedNode] = useState<GraphNodeType | null>(null);
  const [zoom, setZoom] = useState(1);

  const handleZoomIn = () => setZoom((z) => Math.min(z + 0.2, 3));
  const handleZoomOut = () => setZoom((z) => Math.max(z - 0.2, 0.4));
  const handleReset = () => {
    setZoom(1);
    setSelectedNode(null);
  };

  return (
    <div className="space-y-4 animate-fade-in h-full">
      {/* Page Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-mono font-bold text-text-primary tracking-wider">
            INFRASTRUCTURE TOPOLOGY
          </h1>
          <p className="text-text-secondary text-sm mt-1">
            Network infrastructure visualization
          </p>
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2">
          <Button variant="secondary" size="sm" onClick={handleZoomIn}>+</Button>
          <Button variant="secondary" size="sm" onClick={handleZoomOut}>-</Button>
          <Button variant="ghost" size="sm" onClick={handleReset}>Reset</Button>
        </div>
      </div>

      {/* Graph Area */}
      <div className="flex gap-4 h-[calc(100vh-220px)]">
        {/* Canvas */}
        <div className="flex-1 bg-surface border border-border-subtle rounded-tactical overflow-hidden">
          <GraphCanvas
            nodes={mockNodes}
            edges={mockEdges}
            zoom={zoom}
            onNodeSelect={setSelectedNode}
            selectedNodeId={selectedNode?.id || null}
          />
        </div>

        {/* Side Panel */}
        {selectedNode && (
          <div className="w-80 animate-slide-up">
            <Card title="NODE DETAILS" glow>
              <div className="space-y-3">
                <div>
                  <span className="text-text-muted text-xs uppercase">Name</span>
                  <p className="font-mono text-accent-cyan">{selectedNode.label}</p>
                </div>
                <div>
                  <span className="text-text-muted text-xs uppercase">Type</span>
                  <p className="text-text-primary capitalize">{selectedNode.type.replace('_', ' ')}</p>
                </div>
                <div>
                  <span className="text-text-muted text-xs uppercase">Criticality</span>
                  <p className={`font-mono uppercase ${
                    selectedNode.criticality === 'critical' ? 'text-threat-red' :
                    selectedNode.criticality === 'high' ? 'text-warning-amber' :
                    'text-accent-green'
                  }`}>
                    {selectedNode.criticality}
                  </p>
                </div>
                <div>
                  <span className="text-text-muted text-xs uppercase">ID</span>
                  <p className="font-mono text-text-secondary text-sm">{selectedNode.id}</p>
                </div>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}
