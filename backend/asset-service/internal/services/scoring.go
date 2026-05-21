package services

import (
	"github.com/cyberajju/ARES-X/backend/asset-service/internal/models"
	"github.com/cyberajju/ARES-X/backend/asset-service/internal/repository"
)

// ScoringService computes criticality scores for assets.
type ScoringService struct {
	repo repository.AssetRepository
}

// NewScoringService creates a new scoring service.
func NewScoringService(repo repository.AssetRepository) *ScoringService {
	return &ScoringService{repo: repo}
}

// CalculateCriticality computes the weighted criticality score for an asset.
func (s *ScoringService) CalculateCriticality(asset *models.Asset) *models.CriticalityScore {
	bi := s.calculateBusinessImpact(asset)
	ex := s.calculateExposure(asset)
	vd := s.calculateVulnerabilityDensity(asset)
	cs := s.calculateConnectivity(asset)

	overall := bi*models.BusinessImpactWeight +
		ex*models.ExposureWeight +
		vd*models.VulnDensityWeight +
		cs*models.ConnectivityWeight

	return &models.CriticalityScore{
		AssetID:             asset.ID,
		Overall:             overall,
		BusinessImpact:      bi,
		ExposureLevel:       ex,
		VulnerabilityDensity: vd,
		ConnectivityScore:   cs,
	}
}

// RecalculateAll recalculates criticality scores for every asset.
func (s *ScoringService) RecalculateAll() {
	allAssets := s.repo.GetAllAssets()
	for i := range allAssets {
		score := s.CalculateCriticality(&allAssets[i])
		_ = s.repo.SetScore(score)
	}
}

// calculateBusinessImpact returns a 0-1 score based on asset type.
func (s *ScoringService) calculateBusinessImpact(asset *models.Asset) float64 {
	switch asset.Type {
	case models.AssetTypeDatabase:
		return 0.9
	case models.AssetTypeFirewall:
		return 0.85
	case models.AssetTypeServer:
		return 0.7
	case models.AssetTypeLoadBalancer:
		return 0.75
	case models.AssetTypeRouter:
		return 0.7
	case models.AssetTypeSwitch:
		return 0.6
	case models.AssetTypeCloudVM:
		return 0.65
	case models.AssetTypeApplication:
		return 0.7
	case models.AssetTypeIdentity:
		return 0.8
	case models.AssetTypeOTController:
		return 0.85
	case models.AssetTypeOTSensor:
		return 0.6
	case models.AssetTypeContainer:
		return 0.5
	case models.AssetTypeWorkstation:
		return 0.3
	case models.AssetTypeMobileDevice:
		return 0.25
	case models.AssetTypeIoTDevice:
		return 0.4
	default:
		return 0.5
	}
}

// calculateExposure scores based on the asset status and network presence.
func (s *ScoringService) calculateExposure(asset *models.Asset) float64 {
	score := 0.3 // baseline

	// Public IP presence increases exposure
	if asset.IPAddress != "" {
		score += 0.2
	}

	// Compromised status means high exposure
	if asset.Status == models.AssetStatusCompromised {
		score += 0.4
	}

	// Active assets have more exposure than inactive
	if asset.Status == models.AssetStatusActive {
		score += 0.1
	}

	if score > 1.0 {
		score = 1.0
	}
	return score
}

// calculateVulnerabilityDensity returns a score based on metadata hints.
func (s *ScoringService) calculateVulnerabilityDensity(asset *models.Asset) float64 {
	score := 0.3 // baseline

	// Check metadata for patch level indicators
	if asset.Metadata != nil {
		if patchLevel, ok := asset.Metadata["patch_level"]; ok {
			switch patchLevel {
			case "outdated":
				score += 0.5
			case "behind":
				score += 0.3
			case "current":
				score += 0.0
			}
		}
		if vulnCount, ok := asset.Metadata["known_vulns"]; ok {
			if vulnCount != "0" {
				score += 0.2
			}
		}
	}

	if score > 1.0 {
		score = 1.0
	}
	return score
}

// calculateConnectivity scores based on the number of relationships relative to total assets.
func (s *ScoringService) calculateConnectivity(asset *models.Asset) float64 {
	rels, _ := s.repo.GetRelationships(asset.ID)
	relCount := len(rels)

	totalAssets := s.repo.Count()
	if totalAssets <= 1 {
		return 0.0
	}

	// Ratio of connections to maximum possible
	maxConnections := totalAssets - 1
	ratio := float64(relCount) / float64(maxConnections)
	if ratio > 1.0 {
		ratio = 1.0
	}
	return ratio
}
