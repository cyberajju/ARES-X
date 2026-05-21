'use client';

import StatCard from '@/components/dashboard/StatCard';
import AlertList from '@/components/dashboard/AlertList';
import ThreatLevel from '@/components/dashboard/ThreatLevel';
import StatusIndicator from '@/components/ui/StatusIndicator';

const stats = [
  { label: 'Total Assets', value: '247', trend: '+12', trendUp: true, color: 'cyan' as const },
  { label: 'Active Threats', value: '12', trend: '+3', trendUp: true, color: 'red' as const },
  { label: 'Attack Paths', value: '34', trend: '-2', trendUp: false, color: 'amber' as const },
  { label: 'System Health', value: '94%', trend: '+1%', trendUp: true, color: 'green' as const },
];

const alerts = [
  { id: '1', severity: 'critical' as const, message: 'Unauthorized lateral movement detected on PROD-DB-01', timestamp: '2m ago', source: 'IDS-Alpha' },
  { id: '2', severity: 'high' as const, message: 'Privilege escalation attempt on AD-Controller', timestamp: '8m ago', source: 'EDR-Sentinel' },
  { id: '3', severity: 'medium' as const, message: 'Unusual outbound traffic from WEBSVR-03', timestamp: '15m ago', source: 'NetFlow-Monitor' },
  { id: '4', severity: 'low' as const, message: 'Failed login attempts from external IP range', timestamp: '23m ago', source: 'WAF-Primary' },
  { id: '5', severity: 'medium' as const, message: 'Certificate expiration warning for api.internal', timestamp: '1h ago', source: 'CertWatch' },
  { id: '6', severity: 'high' as const, message: 'Malware signature match on endpoint WKS-042', timestamp: '1h ago', source: 'AV-Engine' },
];

const services = [
  { name: 'Graph Engine', status: 'online' as const },
  { name: 'Asset Service', status: 'online' as const },
  { name: 'Attack Path Engine', status: 'degraded' as const },
  { name: 'API Gateway', status: 'online' as const },
];

export default function DashboardPage() {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-mono font-bold text-text-primary tracking-wider">
          COMMAND CENTER
        </h1>
        <p className="text-text-secondary text-sm mt-1">
          Real-time operational overview
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat) => (
          <StatCard key={stat.label} {...stat} />
        ))}
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Alert List */}
        <div className="lg:col-span-2">
          <AlertList alerts={alerts} />
        </div>

        {/* Right: Threat Level + System Status */}
        <div className="space-y-6">
          <ThreatLevel level={72} label="ELEVATED" />

          {/* System Status */}
          <div className="bg-surface border border-border-subtle rounded-tactical p-4">
            <h3 className="text-sm font-mono text-text-secondary uppercase tracking-wider mb-4">
              System Status
            </h3>
            <div className="space-y-3">
              {services.map((service) => (
                <div key={service.name} className="flex items-center justify-between">
                  <span className="text-sm text-text-primary">{service.name}</span>
                  <StatusIndicator status={service.status} size="sm" label={service.status} />
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
