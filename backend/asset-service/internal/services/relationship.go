package services

import (
	"fmt"
	"net"
	"strings"

	"github.com/cyberajju/ARES-X/backend/asset-service/internal/models"
	"github.com/cyberajju/ARES-X/backend/asset-service/internal/repository"
)

// RelationshipService manages asset relationship inference and queries.
type RelationshipService struct {
	repo   repository.AssetRepository
	nextID int
}

// NewRelationshipService creates a new relationship service.
func NewRelationshipService(repo repository.AssetRepository) *RelationshipService {
	return &RelationshipService{repo: repo, nextID: 1}
}

// InferRelationships discovers relationships for a given asset based on heuristics.
func (s *RelationshipService) InferRelationships(asset *models.Asset) {
	allAssets := s.repo.GetAllAssets()

	for _, other := range allAssets {
		if other.ID == asset.ID {
			continue
		}

		// Network proximity: same subnet
		if asset.IPAddress != "" && other.IPAddress != "" {
			if sameSubnet(asset.IPAddress, other.IPAddress) {
				s.createRelationshipIfNotExists(asset.ID, other.ID, models.RelConnectsTo, 0.7)
			}
		}

		// Shared services: if both have matching tags
		if hasSharedTags(asset.Tags, other.Tags) {
			s.createRelationshipIfNotExists(asset.ID, other.ID, models.RelDependsOn, 0.5)
		}

		// Authentication flows: identity assets authenticate to servers/applications
		if asset.Type == models.AssetTypeIdentity &&
			(other.Type == models.AssetTypeServer || other.Type == models.AssetTypeApplication) {
			s.createRelationshipIfNotExists(asset.ID, other.ID, models.RelAuthenticatesTo, 0.8)
		}

		// Firewall manages network assets
		if asset.Type == models.AssetTypeFirewall &&
			(other.Type == models.AssetTypeRouter || other.Type == models.AssetTypeSwitch) {
			s.createRelationshipIfNotExists(asset.ID, other.ID, models.RelManages, 0.6)
		}
	}
}

// GetRelationships returns direct relationships for an asset.
func (s *RelationshipService) GetRelationships(assetID string) ([]models.AssetRelationship, error) {
	return s.repo.GetRelationships(assetID)
}

// GetRelationshipGraph returns transitive relationships up to a specified depth.
func (s *RelationshipService) GetRelationshipGraph(assetID string, depth int) ([]models.AssetRelationship, error) {
	if depth <= 0 {
		depth = 1
	}

	visited := make(map[string]bool)
	var allRels []models.AssetRelationship

	queue := []string{assetID}
	visited[assetID] = true

	for currentDepth := 0; currentDepth < depth && len(queue) > 0; currentDepth++ {
		var nextQueue []string
		for _, id := range queue {
			rels, err := s.repo.GetRelationships(id)
			if err != nil {
				continue
			}
			for _, rel := range rels {
				allRels = append(allRels, rel)
				neighbor := rel.TargetID
				if rel.TargetID == id {
					neighbor = rel.SourceID
				}
				if !visited[neighbor] {
					visited[neighbor] = true
					nextQueue = append(nextQueue, neighbor)
				}
			}
		}
		queue = nextQueue
	}

	return allRels, nil
}

// CreateRelationship creates a new relationship with validation.
func (s *RelationshipService) CreateRelationship(rel *models.AssetRelationship) error {
	if rel.SourceID == "" || rel.TargetID == "" {
		return fmt.Errorf("source_id and target_id are required")
	}
	if rel.SourceID == rel.TargetID {
		return fmt.Errorf("cannot create self-referencing relationship")
	}

	// Verify both assets exist
	if _, err := s.repo.GetByID(rel.SourceID); err != nil {
		return fmt.Errorf("source asset not found: %s", rel.SourceID)
	}
	if _, err := s.repo.GetByID(rel.TargetID); err != nil {
		return fmt.Errorf("target asset not found: %s", rel.TargetID)
	}

	if rel.ID == "" {
		rel.ID = fmt.Sprintf("rel-%04d", s.nextID)
		s.nextID++
	}
	if rel.Confidence == 0 {
		rel.Confidence = 1.0
	}

	return s.repo.CreateRelationship(rel)
}

func (s *RelationshipService) createRelationshipIfNotExists(sourceID, targetID string, relType models.RelationshipType, confidence float64) {
	// Check if relationship already exists
	existing, _ := s.repo.GetRelationships(sourceID)
	for _, rel := range existing {
		if rel.TargetID == targetID && rel.Type == relType {
			return
		}
		if rel.SourceID == targetID && rel.Type == relType {
			return
		}
	}

	rel := &models.AssetRelationship{
		ID:         fmt.Sprintf("rel-%04d", s.nextID),
		SourceID:   sourceID,
		TargetID:   targetID,
		Type:       relType,
		Confidence: confidence,
	}
	s.nextID++
	_ = s.repo.CreateRelationship(rel)
}

// sameSubnet checks if two IPs are in the same /24 subnet.
func sameSubnet(ip1, ip2 string) bool {
	a := net.ParseIP(ip1)
	b := net.ParseIP(ip2)
	if a == nil || b == nil {
		return false
	}
	a4 := a.To4()
	b4 := b.To4()
	if a4 == nil || b4 == nil {
		return false
	}
	// Compare first 3 octets (/24)
	return a4[0] == b4[0] && a4[1] == b4[1] && a4[2] == b4[2]
}

// hasSharedTags checks if two tag lists share any common element.
func hasSharedTags(tags1, tags2 []string) bool {
	set := make(map[string]bool)
	for _, t := range tags1 {
		set[strings.ToLower(t)] = true
	}
	for _, t := range tags2 {
		if set[strings.ToLower(t)] {
			return true
		}
	}
	return false
}
