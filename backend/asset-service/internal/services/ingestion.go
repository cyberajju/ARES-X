package services

import (
	"fmt"
	"net"
	"regexp"
	"strings"

	"github.com/cyberajju/ARES-X/backend/asset-service/internal/models"
	"github.com/cyberajju/ARES-X/backend/asset-service/internal/repository"
)

var macRegex = regexp.MustCompile(`^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$`)

// IngestionService handles asset ingestion with validation, normalization, and deduplication.
type IngestionService struct {
	repo            repository.AssetRepository
	scoring         *ScoringService
	relationship    *RelationshipService
	maxBulkSize     int
}

// NewIngestionService creates a new ingestion service.
func NewIngestionService(repo repository.AssetRepository, scoring *ScoringService, relationship *RelationshipService, maxBulkSize int) *IngestionService {
	return &IngestionService{
		repo:         repo,
		scoring:      scoring,
		relationship: relationship,
		maxBulkSize:  maxBulkSize,
	}
}

// IngestAsset validates, normalizes, deduplicates, and stores a single asset.
func (s *IngestionService) IngestAsset(asset *models.Asset) error {
	if err := s.Validate(asset); err != nil {
		return fmt.Errorf("validation failed: %w", err)
	}

	s.Normalize(asset)

	if duplicate := s.FindDuplicate(asset); duplicate != nil {
		return fmt.Errorf("duplicate asset found: %s (name=%s, ip=%s)", duplicate.ID, duplicate.Name, duplicate.IPAddress)
	}

	if err := s.repo.Create(asset); err != nil {
		return fmt.Errorf("failed to store asset: %w", err)
	}

	// Calculate criticality score
	score := s.scoring.CalculateCriticality(asset)
	_ = s.repo.SetScore(score)

	// Infer relationships
	s.relationship.InferRelationships(asset)

	return nil
}

// IngestBulk processes multiple assets, collecting errors per item.
func (s *IngestionService) IngestBulk(assets []models.Asset) (int, []error) {
	if len(assets) > s.maxBulkSize {
		return 0, []error{fmt.Errorf("bulk import exceeds maximum size of %d", s.maxBulkSize)}
	}

	var errs []error
	created := 0

	for i := range assets {
		if err := s.IngestAsset(&assets[i]); err != nil {
			errs = append(errs, fmt.Errorf("asset[%d] (%s): %w", i, assets[i].Name, err))
		} else {
			created++
		}
	}
	return created, errs
}

// Validate checks required fields and format correctness.
func (s *IngestionService) Validate(asset *models.Asset) error {
	if asset.Name == "" {
		return fmt.Errorf("name is required")
	}
	if asset.Type == "" {
		return fmt.Errorf("type is required")
	}
	if !isValidAssetType(asset.Type) {
		return fmt.Errorf("invalid asset type: %s", asset.Type)
	}

	if asset.IPAddress != "" {
		if ip := net.ParseIP(asset.IPAddress); ip == nil {
			return fmt.Errorf("invalid IP address: %s", asset.IPAddress)
		}
	}

	if asset.MACAddress != "" {
		if !macRegex.MatchString(asset.MACAddress) {
			return fmt.Errorf("invalid MAC address: %s", asset.MACAddress)
		}
	}

	return nil
}

// Normalize standardizes asset field formats.
func (s *IngestionService) Normalize(asset *models.Asset) {
	asset.Name = strings.TrimSpace(asset.Name)
	asset.Description = strings.TrimSpace(asset.Description)
	asset.Owner = strings.TrimSpace(asset.Owner)
	asset.Location = strings.TrimSpace(asset.Location)
	asset.IPAddress = strings.TrimSpace(asset.IPAddress)
	asset.MACAddress = strings.ToUpper(strings.TrimSpace(asset.MACAddress))

	// Lowercase tags
	for i, tag := range asset.Tags {
		asset.Tags[i] = strings.ToLower(strings.TrimSpace(tag))
	}

	// Default status
	if asset.Status == "" {
		asset.Status = models.AssetStatusActive
	}
	// Default criticality
	if asset.Criticality == "" {
		asset.Criticality = models.CriticalityMedium
	}
}

// FindDuplicate checks if an asset with the same name and IP already exists.
func (s *IngestionService) FindDuplicate(asset *models.Asset) *models.Asset {
	allAssets := s.repo.GetAllAssets()
	for _, existing := range allAssets {
		if existing.ID == asset.ID {
			continue
		}
		if existing.Name == asset.Name && existing.IPAddress == asset.IPAddress && asset.IPAddress != "" {
			return &existing
		}
	}
	return nil
}

func isValidAssetType(t models.AssetType) bool {
	switch t {
	case models.AssetTypeServer, models.AssetTypeWorkstation, models.AssetTypeRouter,
		models.AssetTypeSwitch, models.AssetTypeFirewall, models.AssetTypeLoadBalancer,
		models.AssetTypeDatabase, models.AssetTypeApplication, models.AssetTypeCloudVM,
		models.AssetTypeContainer, models.AssetTypeIdentity, models.AssetTypeOTController,
		models.AssetTypeOTSensor, models.AssetTypeMobileDevice, models.AssetTypeIoTDevice:
		return true
	}
	return false
}
