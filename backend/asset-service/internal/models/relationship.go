package models

import (
	"time"
)

// RelationshipType defines the nature of a connection between two assets.
type RelationshipType string

const (
	RelConnectsTo       RelationshipType = "connects_to"
	RelDependsOn        RelationshipType = "depends_on"
	RelAuthenticatesTo  RelationshipType = "authenticates_to"
	RelContains         RelationshipType = "contains"
	RelManages          RelationshipType = "manages"
	RelMonitors         RelationshipType = "monitors"
	RelBacksUp          RelationshipType = "backs_up"
)

// AssetRelationship represents a directional link between two assets.
type AssetRelationship struct {
	ID         string            `json:"id"`
	SourceID   string            `json:"source_id"`
	TargetID   string            `json:"target_id"`
	Type       RelationshipType  `json:"type"`
	Confidence float64           `json:"confidence"`
	Metadata   map[string]string `json:"metadata,omitempty"`
	CreatedAt  time.Time         `json:"created_at"`
}

// RelationshipFilter holds filtering criteria for relationship queries.
type RelationshipFilter struct {
	SourceID string           `json:"source_id,omitempty"`
	TargetID string           `json:"target_id,omitempty"`
	Type     RelationshipType `json:"type,omitempty"`
}
