package models

import "time"

// AttackPath represents a computed attack path through the infrastructure graph.
type AttackPath struct {
	ID          string     `json:"id"`
	Name        string     `json:"name"`
	Description string     `json:"description"`
	RiskScore   float64    `json:"risk_score"`
	Likelihood  float64    `json:"likelihood"`
	Impact      float64    `json:"impact"`
	Steps       []PathStep `json:"steps"`
	TTPs        []TTP      `json:"ttps"`
	SourceNode  string     `json:"source_node"`
	TargetNode  string     `json:"target_node"`
	Status      string     `json:"status"`
	ComputedAt  time.Time  `json:"computed_at"`
}

// PathStep represents a single step in an attack path.
type PathStep struct {
	Order       int       `json:"order"`
	NodeID      string    `json:"node_id"`
	NodeLabel   string    `json:"node_label"`
	Action      string    `json:"action"`
	Technique   Technique `json:"technique"`
	Probability float64   `json:"probability"`
	Impact      float64   `json:"impact"`
}

// TTP represents a MITRE ATT&CK Tactic, Technique, and Procedure.
type TTP struct {
	TacticID    string `json:"tactic_id"`
	TacticName  string `json:"tactic_name"`
	TechniqueID string `json:"technique_id"`
	Name        string `json:"name"`
	Description string `json:"description"`
}

// Technique represents an attack technique.
type Technique struct {
	ID          string `json:"id"`
	Name        string `json:"name"`
	Description string `json:"description"`
	MitreRef    string `json:"mitre_ref,omitempty"`
}

// SimulationConfig represents configuration for a Monte Carlo simulation.
type SimulationConfig struct {
	Iterations     int      `json:"iterations"`
	SourceNodeID   string   `json:"source_node_id"`
	TargetNodeID   string   `json:"target_node_id"`
	AttackBudget   float64  `json:"attack_budget,omitempty"`
	DefenderConfig []string `json:"defender_config,omitempty"`
}

// SimulationResult represents the result of an attack path simulation.
type SimulationResult struct {
	ID                string    `json:"id"`
	Config            SimulationConfig `json:"config"`
	SuccessRate       float64   `json:"success_rate"`
	AverageSteps      float64   `json:"average_steps"`
	AverageDuration   float64   `json:"average_duration_hours"`
	MostLikelyPath    []string  `json:"most_likely_path"`
	CriticalNodes     []string  `json:"critical_nodes"`
	Recommendations   []string  `json:"recommendations"`
	CompletedAt       time.Time `json:"completed_at"`
}

// ComputeAttackPathRequest represents a request to compute attack paths.
type ComputeAttackPathRequest struct {
	SourceNodeID string `json:"source_node_id"`
	TargetNodeID string `json:"target_node_id"`
	MaxDepth     int    `json:"max_depth,omitempty"`
	MinRisk      float64 `json:"min_risk,omitempty"`
}
