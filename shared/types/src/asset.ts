/**
 * Asset management types for the ARES-X platform.
 * @module asset
 */

/** Type classification for infrastructure assets. */
export enum AssetType {
  Server = 'server',
  Workstation = 'workstation',
  NetworkDevice = 'network_device',
  Database = 'database',
  Application = 'application',
  CloudInstance = 'cloud_instance',
  Container = 'container',
  IoTDevice = 'iot_device',
  MobileDevice = 'mobile_device',
  VirtualMachine = 'virtual_machine',
}

/** Criticality level of an asset to the organization. */
export enum Criticality {
  Low = 'low',
  Medium = 'medium',
  High = 'high',
  Critical = 'critical',
}

/** Represents an infrastructure asset in the system. */
export interface Asset {
  /** Unique asset identifier. */
  id: string;
  /** Human-readable asset name. */
  name: string;
  /** Network hostname of the asset. */
  hostname: string;
  /** IP address of the asset. */
  ipAddress: string;
  /** Type classification of the asset. */
  type: AssetType;
  /** Criticality level to the organization. */
  criticality: Criticality;
  /** Owner of the asset (person or team). */
  owner: string;
  /** Department responsible for the asset. */
  department: string;
  /** Physical or logical location. */
  location: string;
  /** Operating system name. */
  os: string;
  /** Operating system version. */
  osVersion: string;
  /** Key-value tags for categorization. */
  tags: Record<string, string>;
  /** Additional metadata. */
  metadata: Record<string, string>;
  /** Current status of the asset. */
  status: 'active' | 'inactive' | 'pending' | 'decommissioned';
  /** Timestamp when the asset was first registered. */
  createdAt: string;
  /** Timestamp of last update. */
  updatedAt: string;
  /** Timestamp when the asset was last seen on the network. */
  lastSeen: string;
}

/** Filter criteria for querying assets. */
export interface AssetFilter {
  /** Filter by asset types. */
  types?: AssetType[];
  /** Filter by criticality levels. */
  criticalities?: Criticality[];
  /** Filter by status. */
  status?: Asset['status'];
  /** Free-text search query. */
  searchQuery?: string;
  /** Filter by owner. */
  owner?: string;
  /** Filter by department. */
  department?: string;
  /** Filter by tags. */
  tags?: Record<string, string>;
}

/** Request body for creating a new asset. */
export interface AssetCreateRequest {
  /** Human-readable asset name. */
  name: string;
  /** Network hostname. */
  hostname: string;
  /** IP address. */
  ipAddress: string;
  /** Type classification. */
  type: AssetType;
  /** Criticality level. */
  criticality: Criticality;
  /** Owner of the asset. */
  owner: string;
  /** Responsible department. */
  department: string;
  /** Physical or logical location. */
  location: string;
  /** Operating system. */
  os: string;
  /** OS version. */
  osVersion: string;
  /** Categorization tags. */
  tags?: Record<string, string>;
  /** Additional metadata. */
  metadata?: Record<string, string>;
}

/** Request body for bulk importing assets. */
export interface BulkImportRequest {
  /** Array of assets to import. */
  assets: AssetCreateRequest[];
  /** Whether to update existing assets matched by hostname. */
  upsert: boolean;
  /** Source system identifier. */
  source: string;
}
