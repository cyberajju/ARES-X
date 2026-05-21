'use client';

import { useState, useMemo } from 'react';
import Table from '@/components/ui/Table';
import Badge from '@/components/ui/Badge';
import Input from '@/components/ui/Input';
import Button from '@/components/ui/Button';
import StatusIndicator from '@/components/ui/StatusIndicator';
import type { Asset, ColumnDef } from '@/lib/types';

const mockAssets: Asset[] = [
  { id: '1', name: 'PROD-DB-01', type: 'database', criticality: 'critical', status: 'online', ip: '10.0.1.50', lastSeen: '1m ago' },
  { id: '2', name: 'PROD-DB-02', type: 'database', criticality: 'critical', status: 'online', ip: '10.0.1.51', lastSeen: '1m ago' },
  { id: '3', name: 'WEBSVR-01', type: 'server', criticality: 'high', status: 'online', ip: '10.0.2.10', lastSeen: '30s ago' },
  { id: '4', name: 'WEBSVR-02', type: 'server', criticality: 'high', status: 'online', ip: '10.0.2.11', lastSeen: '30s ago' },
  { id: '5', name: 'WEBSVR-03', type: 'server', criticality: 'medium', status: 'degraded', ip: '10.0.2.12', lastSeen: '5m ago' },
  { id: '6', name: 'APPSVR-01', type: 'server', criticality: 'high', status: 'online', ip: '10.0.3.20', lastSeen: '1m ago' },
  { id: '7', name: 'APPSVR-02', type: 'server', criticality: 'high', status: 'online', ip: '10.0.3.21', lastSeen: '1m ago' },
  { id: '8', name: 'APPSVR-03', type: 'server', criticality: 'medium', status: 'online', ip: '10.0.3.22', lastSeen: '2m ago' },
  { id: '9', name: 'AD-Controller', type: 'server', criticality: 'critical', status: 'online', ip: '10.0.0.5', lastSeen: '10s ago' },
  { id: '10', name: 'FW-Primary', type: 'firewall', criticality: 'critical', status: 'online', ip: '10.0.0.1', lastSeen: '5s ago' },
  { id: '11', name: 'FW-Secondary', type: 'firewall', criticality: 'high', status: 'online', ip: '10.0.0.2', lastSeen: '5s ago' },
  { id: '12', name: 'LB-External', type: 'load_balancer', criticality: 'high', status: 'online', ip: '10.0.0.10', lastSeen: '15s ago' },
  { id: '13', name: 'DNS-Internal', type: 'server', criticality: 'medium', status: 'online', ip: '10.0.0.53', lastSeen: '1m ago' },
  { id: '14', name: 'VPN-Gateway', type: 'firewall', criticality: 'high', status: 'online', ip: '10.0.0.100', lastSeen: '30s ago' },
  { id: '15', name: 'WKS-042', type: 'workstation', criticality: 'low', status: 'offline', ip: '10.0.10.42', lastSeen: '2h ago' },
  { id: '16', name: 'MAIL-SVR-01', type: 'server', criticality: 'high', status: 'online', ip: '10.0.4.10', lastSeen: '1m ago' },
  { id: '17', name: 'BACKUP-NAS', type: 'storage', criticality: 'medium', status: 'online', ip: '10.0.5.100', lastSeen: '5m ago' },
  { id: '18', name: 'MONITOR-01', type: 'server', criticality: 'low', status: 'online', ip: '10.0.6.10', lastSeen: '30s ago' },
];

export default function AssetsPage() {
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [criticalityFilter, setCriticalityFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const filteredAssets = useMemo(() => {
    return mockAssets.filter((asset) => {
      if (search && !asset.name.toLowerCase().includes(search.toLowerCase()) && !asset.ip.includes(search)) {
        return false;
      }
      if (typeFilter !== 'all' && asset.type !== typeFilter) return false;
      if (criticalityFilter !== 'all' && asset.criticality !== criticalityFilter) return false;
      if (statusFilter !== 'all' && asset.status !== statusFilter) return false;
      return true;
    });
  }, [search, typeFilter, criticalityFilter, statusFilter]);

  const paginatedAssets = filteredAssets.slice((page - 1) * pageSize, page * pageSize);
  const totalPages = Math.ceil(filteredAssets.length / pageSize);

  const columns: ColumnDef<Asset>[] = [
    {
      header: 'Name',
      accessor: 'name',
      render: (value) => <span className="font-mono text-accent-cyan">{value}</span>,
    },
    {
      header: 'Type',
      accessor: 'type',
      render: (value) => <span className="capitalize text-text-secondary">{String(value).replace('_', ' ')}</span>,
    },
    {
      header: 'Criticality',
      accessor: 'criticality',
      render: (value) => {
        const variant = value === 'critical' ? 'critical' : value === 'high' ? 'high' : value === 'medium' ? 'medium' : 'low';
        return <Badge variant={variant as 'critical' | 'high' | 'medium' | 'low'}>{String(value).toUpperCase()}</Badge>;
      },
    },
    {
      header: 'Status',
      accessor: 'status',
      render: (value) => <StatusIndicator status={value as 'online' | 'offline' | 'degraded'} size="sm" label={value as string} />,
    },
    {
      header: 'IP Address',
      accessor: 'ip',
      render: (value) => <span className="font-mono text-text-secondary">{value}</span>,
    },
    {
      header: 'Last Seen',
      accessor: 'lastSeen',
      render: (value) => <span className="text-text-muted text-sm">{value}</span>,
    },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Page Title */}
      <div>
        <h1 className="text-2xl font-mono font-bold text-text-primary tracking-wider">
          ASSET INVENTORY
        </h1>
        <p className="text-text-secondary text-sm mt-1">
          {filteredAssets.length} assets tracked
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-end gap-4 bg-surface border border-border-subtle rounded-tactical p-4">
        <div className="flex-1 min-w-[200px]">
          <Input
            label="Search"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search by name or IP..."
          />
        </div>
        <div>
          <label className="block text-xs text-text-secondary uppercase tracking-wider mb-1.5">Type</label>
          <select
            value={typeFilter}
            onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
            className="bg-elevated border border-border-subtle rounded-tactical px-3 py-2 text-sm text-text-primary focus:border-accent-cyan focus:outline-none"
          >
            <option value="all">All Types</option>
            <option value="server">Server</option>
            <option value="database">Database</option>
            <option value="firewall">Firewall</option>
            <option value="load_balancer">Load Balancer</option>
            <option value="workstation">Workstation</option>
            <option value="storage">Storage</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-text-secondary uppercase tracking-wider mb-1.5">Criticality</label>
          <select
            value={criticalityFilter}
            onChange={(e) => { setCriticalityFilter(e.target.value); setPage(1); }}
            className="bg-elevated border border-border-subtle rounded-tactical px-3 py-2 text-sm text-text-primary focus:border-accent-cyan focus:outline-none"
          >
            <option value="all">All</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-text-secondary uppercase tracking-wider mb-1.5">Status</label>
          <select
            value={statusFilter}
            onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
            className="bg-elevated border border-border-subtle rounded-tactical px-3 py-2 text-sm text-text-primary focus:border-accent-cyan focus:outline-none"
          >
            <option value="all">All</option>
            <option value="online">Online</option>
            <option value="offline">Offline</option>
            <option value="degraded">Degraded</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <Table<Asset> columns={columns} data={paginatedAssets} />

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-text-muted text-sm">
            Page {page} of {totalPages}
          </span>
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              Previous
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
            >
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
