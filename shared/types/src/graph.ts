/**
 * Graph engine types for the ARES-X platform.
 * @module graph
 */

/** Type classification for graph nodes. */
export enum NodeType {
  Server = 'server',
  Workstation = 'workstation',
  NetworkDevice = 'network_device',
  Database = 'database',
  Application = 'application',
  User = 'user',
  ServiceAccount = 'service_account',
  CloudResource = 'cloud_resource',
  Container = 'container',
  Identity = 'identity',
}

/** Type classification for graph edges (relationships). */
export enum EdgeType {
  NetworkAccess = 'network_access',
  CredentialAccess = 'credential_access',
  PrivilegeEscalation = 'privilege_escalation',
  LateralMovement = 'lateral_movement',
  DataFlow = 'data_flow',
  TrustRelationship = 'trust_relationship',
  Membership = 'membership',
  Dependency = 'dependency',
}

/** Represents a node (vertex) in the attack graph. */
export interface GraphNode {
  /** Unique node identifier. */
  id: string;
  /** Display name for the node. */
  name: string;
  /** Node type classification. */
  type: NodeType;
  /** Key-value properties associated with the node. */
  properties: Record<string, string>;
  /** Computed risk score (0.0 - 10.0). */
  riskScore: number;
  /** Current status of the node. */
  status: 'active' | 'inactive' | 'compromised' | 'unknown';
  /** Timestamp when the node was created. */
  createdAt: string;
  /** Timestamp of last update. */
  updatedAt: string;
}

/** Represents a directed edge (relationship) between two nodes. */
export interface GraphEdge {
  /** Unique edge identifier. */
  id: string;
  /** Source node identifier. */
  sourceId: string;
  /** Target node identifier. */
  targetId: string;
  /** Relationship type. */
  type: EdgeType;
  /** Edge weight representing traversal cost/difficulty. */
  weight: number;
  /** Key-value properties associated with the edge. */
  properties: Record<string, string>;
  /** Timestamp when the edge was created. */
  createdAt: string;
}

/** Query parameters for fetching graph data. */
export interface GraphQuery {
  /** Filter by node types. */
  nodeTypes?: NodeType[];
  /** Filter by edge types. */
  edgeTypes?: EdgeType[];
  /** Custom property filters. */
  filters?: Record<string, string>;
  /** Minimum risk score threshold. */
  minRiskScore?: number;
  /** Maximum depth for traversal queries. */
  maxDepth?: number;
  /** Maximum number of results. */
  limit?: number;
}

/** Response containing graph data. */
export interface GraphResponse {
  /** Returned nodes. */
  nodes: GraphNode[];
  /** Returned edges. */
  edges: GraphEdge[];
  /** Total count of matching nodes. */
  totalNodes: number;
  /** Total count of matching edges. */
  totalEdges: number;
}

/** Result of a path-finding operation. */
export interface PathResult {
  /** Ordered list of nodes in the path. */
  nodes: GraphNode[];
  /** Ordered list of edges in the path. */
  edges: GraphEdge[];
  /** Total weight (cost) of the path. */
  totalWeight: number;
  /** Number of hops in the path. */
  hopCount: number;
}

/** Result of a blast radius computation. */
export interface BlastRadius {
  /** The origin node from which blast radius was computed. */
  originId: string;
  /** Nodes affected within the blast radius. */
  affectedNodes: GraphNode[];
  /** Edges traversed during computation. */
  traversedEdges: GraphEdge[];
  /** Total number of affected nodes. */
  totalAffected: number;
  /** Aggregate risk score across all affected nodes. */
  aggregateRiskScore: number;
  /** Count of affected nodes by type. */
  affectedByType: Record<string, number>;
}
