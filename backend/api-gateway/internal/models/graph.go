package models

// NodeType represents the type of a graph node.
type NodeType string

const (
	NodeTypeAsset         NodeType = "asset"
	NodeTypeVulnerability NodeType = "vulnerability"
	NodeTypeIdentity      NodeType = "identity"
	NodeTypePermission    NodeType = "permission"
	NodeTypeNetwork       NodeType = "network"
	NodeTypeProcess       NodeType = "process"
)

// EdgeType represents the type of a graph edge (relationship).
type EdgeType string

const (
	EdgeTypeConnectsTo    EdgeType = "connects_to"
	EdgeTypeHasAccess     EdgeType = "has_access"
	EdgeTypeExploits      EdgeType = "exploits"
	EdgeTypeDependsOn     EdgeType = "depends_on"
	EdgeTypeContains      EdgeType = "contains"
	EdgeTypeTrustsTo      EdgeType = "trusts_to"
	EdgeTypeAuthenticates EdgeType = "authenticates"
)

// GraphNode represents a node in the attack graph.
type GraphNode struct {
	ID         string            `json:"id"`
	Type       NodeType          `json:"type"`
	Label      string            `json:"label"`
	Properties map[string]string `json:"properties,omitempty"`
	RiskScore  float64           `json:"risk_score"`
}

// GraphEdge represents an edge (relationship) in the attack graph.
type GraphEdge struct {
	ID         string            `json:"id"`
	Source     string            `json:"source"`
	Target     string            `json:"target"`
	Type       EdgeType          `json:"type"`
	Weight     float64           `json:"weight"`
	Properties map[string]string `json:"properties,omitempty"`
}

// GraphQuery represents parameters for querying the graph.
type GraphQuery struct {
	NodeTypes  []NodeType `json:"node_types,omitempty"`
	EdgeTypes  []EdgeType `json:"edge_types,omitempty"`
	Limit      int        `json:"limit,omitempty"`
	Offset     int        `json:"offset,omitempty"`
	MinRisk    float64    `json:"min_risk,omitempty"`
	MaxRisk    float64    `json:"max_risk,omitempty"`
	SearchTerm string     `json:"search_term,omitempty"`
}

// PathResult represents a path between two nodes.
type PathResult struct {
	Nodes     []GraphNode `json:"nodes"`
	Edges     []GraphEdge `json:"edges"`
	TotalRisk float64     `json:"total_risk"`
	Length    int         `json:"length"`
}

// BlastRadiusResult represents the blast radius from a given node.
type BlastRadiusResult struct {
	OriginNode     GraphNode   `json:"origin_node"`
	AffectedNodes  []GraphNode `json:"affected_nodes"`
	AffectedEdges  []GraphEdge `json:"affected_edges"`
	TotalImpact    float64     `json:"total_impact"`
	Depth          int         `json:"depth"`
}

// DependencyResult represents the dependencies of a given node.
type DependencyResult struct {
	Node         GraphNode   `json:"node"`
	Dependencies []GraphNode `json:"dependencies"`
	Dependents   []GraphNode `json:"dependents"`
}
