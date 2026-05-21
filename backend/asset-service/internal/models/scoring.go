package models

import (
	"time"
)

// Scoring weight constants for the criticality algorithm.
const (
	BusinessImpactWeight = 0.30
	ExposureWeight       = 0.25
	VulnDensityWeight    = 0.25
	ConnectivityWeight   = 0.20
)

// CriticalityScore holds the computed criticality breakdown for an asset.
type CriticalityScore struct {
	AssetID             string  `json:"asset_id"`
	Overall             float64 `json:"overall"`
	BusinessImpact      float64 `json:"business_impact"`
	ExposureLevel       float64 `json:"exposure_level"`
	VulnerabilityDensity float64 `json:"vulnerability_density"`
	ConnectivityScore   float64 `json:"connectivity_score"`
}

// ScoreHistory records a criticality score at a point in time.
type ScoreHistory struct {
	ID          string           `json:"id"`
	AssetID     string           `json:"asset_id"`
	Score       CriticalityScore `json:"score"`
	CalculatedAt time.Time       `json:"calculated_at"`
}
