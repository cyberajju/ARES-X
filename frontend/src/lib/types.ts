// Frontend-specific types for ARES-X

export interface NavItem {
  label: string;
  href: string;
  icon: string;
  disabled?: boolean;
}

export interface GraphNode {
  id: string;
  label: string;
  type: 'server' | 'database' | 'firewall' | 'load_balancer' | 'workstation' | 'storage';
  x: number;
  y: number;
  criticality: 'critical' | 'high' | 'medium' | 'low';
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: 'connection' | 'authentication';
}

export interface Asset {
  id: string;
  name: string;
  type: string;
  criticality: 'critical' | 'high' | 'medium' | 'low';
  status: 'online' | 'offline' | 'degraded';
  ip: string;
  lastSeen: string;
}

export interface ColumnDef<T> {
  header: string;
  accessor: string;
  render?: (value: unknown, row: T) => React.ReactNode;
}

export interface AttackPathStep {
  id: string;
  nodeName: string;
  nodeType: string;
  technique: string;
  probability: number;
  cumulativeRisk: number;
}

export interface AttackPath {
  id: string;
  name: string;
  riskScore: number;
  entryPoint: string;
  target: string;
  steps: AttackPathStep[];
  simulationResults: {
    iterations: number;
    meanTime: number;
    successRate: number;
  };
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  clearanceLevel: number;
}

export interface Alert {
  id: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  message: string;
  timestamp: string;
  source: string;
}

export interface ServiceStatus {
  name: string;
  status: 'online' | 'offline' | 'degraded' | 'unknown';
}
