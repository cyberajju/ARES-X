/**
 * Attack path analysis types for the ARES-X platform.
 * @module attack-path
 */

/** MITRE ATT&CK tactic categories. */
export enum Tactic {
  Reconnaissance = 'reconnaissance',
  ResourceDevelopment = 'resource_development',
  InitialAccess = 'initial_access',
  Execution = 'execution',
  Persistence = 'persistence',
  PrivilegeEscalation = 'privilege_escalation',
  DefenseEvasion = 'defense_evasion',
  CredentialAccess = 'credential_access',
  Discovery = 'discovery',
  LateralMovement = 'lateral_movement',
  Collection = 'collection',
  CommandAndControl = 'command_and_control',
  Exfiltration = 'exfiltration',
  Impact = 'impact',
}

/** Represents a specific MITRE ATT&CK technique. */
export interface Technique {
  /** Technique identifier (e.g., T1059). */
  id: string;
  /** Human-readable technique name. */
  name: string;
  /** Detailed description of the technique. */
  description: string;
  /** Associated tactic category. */
  tactic: Tactic;
  /** Severity rating (0.0 - 10.0). */
  severity: number;
  /** Known mitigations for this technique. */
  mitigations: string[];
  /** Data sources that can detect this technique. */
  dataSources: string[];
}

/** Tactics, Techniques, and Procedures - adversary behavior description. */
export interface TTP {
  /** Unique TTP identifier. */
  id: string;
  /** Associated tactic. */
  tactic: Tactic;
  /** The specific technique used. */
  technique: Technique;
  /** Description of the procedure. */
  procedure: string;
  /** Likelihood of this TTP being used (0.0 - 1.0). */
  likelihood: number;
  /** Potential impact if successful (0.0 - 10.0). */
  impact: number;
}

/** Represents a single step in an attack path. */
export interface PathStep {
  /** Order of this step in the path (1-based). */
  order: number;
  /** ID of the node at this step. */
  nodeId: string;
  /** Name of the node at this step. */
  nodeName: string;
  /** TTP used at this step. */
  ttp: TTP;
  /** Probability of success for this step (0.0 - 1.0). */
  successProbability: number;
  /** Cumulative risk score up to this step. */
  cumulativeRisk: number;
  /** Human-readable description of this step. */
  description: string;
  /** Prerequisites that must be satisfied. */
  prerequisites: string[];
  /** Evidence supporting this step. */
  evidence: Record<string, string>;
}

/** Scoring details for an attack path. */
export interface PathScore {
  /** Overall composite score (0.0 - 10.0). */
  overallScore: number;
  /** Likelihood component of the score. */
  likelihoodScore: number;
  /** Impact component of the score. */
  impactScore: number;
  /** Complexity component (inverse - higher means easier). */
  complexityScore: number;
  /** Human-readable risk level classification. */
  riskLevel: 'critical' | 'high' | 'medium' | 'low' | 'informational';
}

/** Represents a complete attack path through the infrastructure. */
export interface AttackPath {
  /** Unique path identifier. */
  id: string;
  /** Human-readable path name. */
  name: string;
  /** Description of the attack path. */
  description: string;
  /** Ordered steps in the path. */
  steps: PathStep[];
  /** Computed path score. */
  score: PathScore;
  /** Starting node ID. */
  sourceNodeId: string;
  /** Target node ID. */
  targetNodeId: string;
  /** Total number of steps. */
  totalSteps: number;
  /** IDs of affected assets. */
  affectedAssets: string[];
  /** Recommended mitigations. */
  recommendedMitigations: string[];
  /** Timestamp when the path was computed. */
  computedAt: string;
  /** Timestamp when the computation expires. */
  expiresAt: string;
}

/** Configuration for running an attack simulation. */
export interface SimulationConfig {
  /** Simulation name. */
  name: string;
  /** Description of the simulation scenario. */
  description: string;
  /** Starting node for the simulation. */
  sourceNodeId: string;
  /** Target nodes to reach. */
  targetNodeIds: string[];
  /** Tactics to include in the simulation. */
  tactics: Tactic[];
  /** Maximum number of iterations. */
  maxIterations: number;
  /** Time limit in seconds. */
  timeLimitSeconds: number;
  /** Whether to assume initial breach. */
  assumeBreach: boolean;
  /** Additional simulation parameters. */
  parameters: Record<string, string>;
}

/** Result of an attack simulation run. */
export interface SimulationResult {
  /** Unique result identifier. */
  id: string;
  /** Configuration used for this simulation. */
  config: SimulationConfig;
  /** Attack paths discovered during simulation. */
  discoveredPaths: AttackPath[];
  /** Total number of paths found. */
  totalPathsFound: number;
  /** Number of nodes visited during simulation. */
  nodesVisited: number;
  /** Number of edges traversed during simulation. */
  edgesTraversed: number;
  /** Execution time in milliseconds. */
  executionTimeMs: number;
  /** Key findings from the simulation. */
  findings: string[];
  /** Security recommendations based on results. */
  recommendations: string[];
  /** Timestamp when the simulation started. */
  startedAt: string;
  /** Timestamp when the simulation completed. */
  completedAt: string;
}
