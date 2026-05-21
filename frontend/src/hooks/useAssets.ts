'use client';

import { useState, useMemo } from 'react';
import type { Asset } from '@/lib/types';

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

interface Filters {
  type: string;
  criticality: string;
  status: string;
}

interface Pagination {
  page: number;
  pageSize: number;
  totalPages: number;
  totalItems: number;
}

interface UseAssetsReturn {
  assets: Asset[];
  loading: boolean;
  filters: Filters;
  setFilters: (filters: Filters) => void;
  pagination: Pagination;
  setPage: (page: number) => void;
  search: (query: string) => void;
  searchQuery: string;
}

export function useAssets(): UseAssetsReturn {
  const [loading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<Filters>({
    type: 'all',
    criticality: 'all',
    status: 'all',
  });
  const [page, setPage] = useState(1);
  const pageSize = 10;

  const filteredAssets = useMemo(() => {
    return mockAssets.filter((asset) => {
      if (searchQuery && !asset.name.toLowerCase().includes(searchQuery.toLowerCase()) && !asset.ip.includes(searchQuery)) {
        return false;
      }
      if (filters.type !== 'all' && asset.type !== filters.type) return false;
      if (filters.criticality !== 'all' && asset.criticality !== filters.criticality) return false;
      if (filters.status !== 'all' && asset.status !== filters.status) return false;
      return true;
    });
  }, [searchQuery, filters]);

  const paginatedAssets = filteredAssets.slice((page - 1) * pageSize, page * pageSize);
  const totalPages = Math.ceil(filteredAssets.length / pageSize);

  return {
    assets: paginatedAssets,
    loading,
    filters,
    setFilters,
    pagination: {
      page,
      pageSize,
      totalPages,
      totalItems: filteredAssets.length,
    },
    setPage,
    search: setSearchQuery,
    searchQuery,
  };
}

export default useAssets;
