/**
 * Dashboard and monitoring types for the ARES-X platform.
 * @module dashboard
 */

/** Overall threat level classification. */
export enum ThreatLevel {
  Critical = 'critical',
  High = 'high',
  Elevated = 'elevated',
  Moderate = 'moderate',
  Low = 'low',
}

/** Alert severity levels. */
export enum AlertSeverity {
  Critical = 'critical',
  High = 'high',
  Medium = 'medium',
  Low = 'low',
  Informational = 'informational',
}

/** Health status of a service. */
export enum ServiceHealth {
  Healthy = 'healthy',
  Degraded = 'degraded',
  Unhealthy = 'unhealthy',
  Unknown = 'unknown',
}

/** Aggregated dashboard statistics. */
export interface DashboardStats {
  /** Total number of monitored assets. */
  totalAssets: number;
  /** Number of currently active assets. */
  activeAssets: number;
  /** Total number of identified attack paths. */
  totalAttackPaths: number;
  /** Number of critical-severity attack paths. */
  criticalPaths: number;
  /** Total number of active alerts. */
  activeAlerts: number;
  /** Current overall threat level. */
  threatLevel: ThreatLevel;
  /** Average risk score across all assets (0.0 - 10.0). */
  averageRiskScore: number;
  /** Number of assets with high criticality or above. */
  highCriticalityAssets: number;
  /** Number of simulations run in the last 24 hours. */
  recentSimulations: number;
  /** Timestamp when stats were last computed. */
  lastUpdated: string;
}

/** Represents a security alert. */
export interface Alert {
  /** Unique alert identifier. */
  id: string;
  /** Alert title. */
  title: string;
  /** Detailed alert description. */
  description: string;
  /** Alert severity level. */
  severity: AlertSeverity;
  /** Source service that generated the alert. */
  source: string;
  /** IDs of related assets. */
  affectedAssetIds: string[];
  /** IDs of related attack paths. */
  relatedPathIds: string[];
  /** Whether the alert has been acknowledged. */
  acknowledged: boolean;
  /** ID of the user who acknowledged the alert. */
  acknowledgedBy?: string;
  /** Timestamp when the alert was acknowledged. */
  acknowledgedAt?: string;
  /** Whether the alert has been resolved. */
  resolved: boolean;
  /** Timestamp when the alert was generated. */
  createdAt: string;
  /** Timestamp of last update. */
  updatedAt: string;
}

/** Overall system status including all services. */
export interface SystemStatus {
  /** Overall system health status. */
  overallHealth: ServiceHealth;
  /** Individual service health statuses. */
  services: ServiceStatus[];
  /** Current system uptime in seconds. */
  uptimeSeconds: number;
  /** System version string. */
  version: string;
  /** Timestamp when status was last checked. */
  lastChecked: string;
}

/** Health status of an individual service. */
export interface ServiceStatus {
  /** Service name. */
  name: string;
  /** Current health status. */
  health: ServiceHealth;
  /** Service version. */
  version: string;
  /** Response latency in milliseconds. */
  latencyMs: number;
  /** Timestamp when the service was last checked. */
  lastChecked: string;
  /** Error message if unhealthy. */
  error?: string;
}
