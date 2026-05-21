'use client';

import { useState } from 'react';
import PathVisualization from '@/components/attack-path/PathVisualization';
import Card from '@/components/ui/Card';
import Badge from '@/components/ui/Badge';
import type { AttackPath } from '@/lib/types';

const mockPaths: AttackPath[] = [
  {
    id: 'path-1',
    name: 'External to Domain Admin',
    riskScore: 94,
    entryPoint: 'FW-Primary',
    target: 'AD-Controller',
    steps: [
      { id: 's1', nodeName: 'FW-Primary', nodeType: 'firewall', technique: 'T1190 - Exploit Public-Facing App', probability: 0.35, cumulativeRisk: 35 },
      { id: 's2', nodeName: 'WEBSVR-01', nodeType: 'server', technique: 'T1059 - Command Execution', probability: 0.60, cumulativeRisk: 56 },
      { id: 's3', nodeName: 'APPSVR-01', nodeType: 'server', technique: 'T1078 - Valid Accounts', probability: 0.45, cumulativeRisk: 72 },
      { id: 's4', nodeName: 'AD-Controller', nodeType: 'server', technique: 'T1003 - Credential Dumping', probability: 0.70, cumulativeRisk: 94 },
    ],
    simulationResults: { iterations: 10000, meanTime: 4.2, successRate: 0.34 },
  },
  {
    id: 'path-2',
    name: 'VPN to Database Exfil',
    riskScore: 87,
    entryPoint: 'VPN-Gateway',
    target: 'PROD-DB-01',
    steps: [
      { id: 's1', nodeName: 'VPN-Gateway', nodeType: 'firewall', technique: 'T1133 - External Remote Services', probability: 0.25, cumulativeRisk: 25 },
      { id: 's2', nodeName: 'AD-Controller', nodeType: 'server', technique: 'T1078 - Valid Accounts', probability: 0.55, cumulativeRisk: 52 },
      { id: 's3', nodeName: 'APPSVR-01', nodeType: 'server', technique: 'T1021 - Remote Services', probability: 0.50, cumulativeRisk: 71 },
      { id: 's4', nodeName: 'PROD-DB-01', nodeType: 'database', technique: 'T1005 - Data from Local System', probability: 0.65, cumulativeRisk: 87 },
    ],
    simulationResults: { iterations: 10000, meanTime: 6.8, successRate: 0.28 },
  },
  {
    id: 'path-3',
    name: 'Workstation Pivot to DB',
    riskScore: 72,
    entryPoint: 'WKS-042',
    target: 'PROD-DB-02',
    steps: [
      { id: 's1', nodeName: 'WKS-042', nodeType: 'workstation', technique: 'T1566 - Phishing', probability: 0.40, cumulativeRisk: 40 },
      { id: 's2', nodeName: 'APPSVR-02', nodeType: 'server', technique: 'T1570 - Lateral Tool Transfer', probability: 0.35, cumulativeRisk: 58 },
      { id: 's3', nodeName: 'PROD-DB-02', nodeType: 'database', technique: 'T1048 - Exfiltration Over Alternative Protocol', probability: 0.45, cumulativeRisk: 72 },
    ],
    simulationResults: { iterations: 10000, meanTime: 8.1, successRate: 0.19 },
  },
  {
    id: 'path-4',
    name: 'DNS Tunneling Path',
    riskScore: 58,
    entryPoint: 'DNS-Internal',
    target: 'PROD-DB-01',
    steps: [
      { id: 's1', nodeName: 'DNS-Internal', nodeType: 'server', technique: 'T1071 - Application Layer Protocol', probability: 0.20, cumulativeRisk: 20 },
      { id: 's2', nodeName: 'WEBSVR-02', nodeType: 'server', technique: 'T1105 - Ingress Tool Transfer', probability: 0.40, cumulativeRisk: 42 },
      { id: 's3', nodeName: 'APPSVR-02', nodeType: 'server', technique: 'T1021 - Remote Services', probability: 0.35, cumulativeRisk: 58 },
    ],
    simulationResults: { iterations: 10000, meanTime: 12.4, successRate: 0.12 },
  },
  {
    id: 'path-5',
    name: 'Supply Chain Compromise',
    riskScore: 45,
    entryPoint: 'MAIL-SVR-01',
    target: 'AD-Controller',
    steps: [
      { id: 's1', nodeName: 'MAIL-SVR-01', nodeType: 'server', technique: 'T1195 - Supply Chain Compromise', probability: 0.15, cumulativeRisk: 15 },
      { id: 's2', nodeName: 'APPSVR-03', nodeType: 'server', technique: 'T1059 - Command Execution', probability: 0.30, cumulativeRisk: 35 },
      { id: 's3', nodeName: 'AD-Controller', nodeType: 'server', technique: 'T1068 - Exploitation for Privilege Escalation', probability: 0.25, cumulativeRisk: 45 },
    ],
    simulationResults: { iterations: 10000, meanTime: 18.6, successRate: 0.07 },
  },
];

export default function AttackPathsPage() {
  const [selectedPath, setSelectedPath] = useState<AttackPath>(mockPaths[0]);

  const getRiskColor = (score: number) => {
    if (score >= 80) return 'text-threat-red';
    if (score >= 60) return 'text-warning-amber';
    if (score >= 40) return 'text-warning-amber-bright';
    return 'text-accent-green';
  };

  const getRiskBadge = (score: number): 'critical' | 'high' | 'medium' | 'low' => {
    if (score >= 80) return 'critical';
    if (score >= 60) return 'high';
    if (score >= 40) return 'medium';
    return 'low';
  };

  return (
    <div className="space-y-4 animate-fade-in">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-mono font-bold text-text-primary tracking-wider">
          ATTACK PATH ANALYSIS
        </h1>
        <p className="text-text-secondary text-sm mt-1">
          Monte Carlo simulation-based path risk assessment
        </p>
      </div>

      {/* Split View */}
      <div className="flex gap-4 h-[calc(100vh-200px)]">
        {/* Path List (1/3) */}
        <div className="w-1/3 overflow-y-auto space-y-2">
          {mockPaths.map((path) => (
            <button
              key={path.id}
              onClick={() => setSelectedPath(path)}
              className={`w-full text-left p-4 rounded-tactical border transition-all ${
                selectedPath.id === path.id
                  ? 'bg-elevated border-accent-cyan shadow-glow-cyan'
                  : 'bg-surface border-border-subtle hover:border-border-active hover:bg-elevated'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-text-primary">{path.name}</span>
                <Badge variant={getRiskBadge(path.riskScore)}>{path.riskScore}</Badge>
              </div>
              <div className="text-xs text-text-muted font-mono">
                {path.entryPoint} → {path.target}
              </div>
              <div className="mt-2 flex items-center gap-3 text-xs text-text-muted">
                <span>{path.steps.length} steps</span>
                <span>Success: {(path.simulationResults.successRate * 100).toFixed(0)}%</span>
              </div>
            </button>
          ))}
        </div>

        {/* Path Detail (2/3) */}
        <div className="flex-1 overflow-y-auto">
          <Card title={selectedPath.name} glow>
            <div className="space-y-6">
              {/* Risk Summary */}
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center">
                  <p className="text-text-muted text-xs uppercase">Risk Score</p>
                  <p className={`text-3xl font-mono font-bold ${getRiskColor(selectedPath.riskScore)}`}>
                    {selectedPath.riskScore}
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-text-muted text-xs uppercase">Success Rate</p>
                  <p className="text-3xl font-mono font-bold text-warning-amber">
                    {(selectedPath.simulationResults.successRate * 100).toFixed(0)}%
                  </p>
                </div>
                <div className="text-center">
                  <p className="text-text-muted text-xs uppercase">Mean Time (hrs)</p>
                  <p className="text-3xl font-mono font-bold text-text-primary">
                    {selectedPath.simulationResults.meanTime}
                  </p>
                </div>
              </div>

              {/* Simulation Info */}
              <div className="bg-abyss border border-border-subtle rounded-tactical p-3">
                <p className="text-xs text-text-muted font-mono">
                  Monte Carlo: {selectedPath.simulationResults.iterations.toLocaleString()} iterations
                </p>
              </div>

              {/* Path Visualization */}
              <PathVisualization steps={selectedPath.steps} />
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
