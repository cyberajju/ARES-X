package repository

import (
	"fmt"
	"strings"
	"sync"
	"time"

	"github.com/cyberajju/ARES-X/backend/asset-service/internal/models"
)

// AssetRepository defines the interface for asset persistence operations.
type AssetRepository interface {
	List(filter models.AssetFilter, pagination models.Pagination) (*models.PaginatedResult, error)
	GetByID(id string) (*models.Asset, error)
	Create(asset *models.Asset) error
	Update(asset *models.Asset) error
	Delete(id string) error
	Search(query string) ([]models.Asset, error)
	BulkCreate(assets []models.Asset) (int, []error)
	Count() int
	GetByType(assetType models.AssetType) ([]models.Asset, error)

	// Relationship methods
	CreateRelationship(rel *models.AssetRelationship) error
	GetRelationships(assetID string) ([]models.AssetRelationship, error)
	GetAllRelationships() []models.AssetRelationship
	DeleteRelationship(id string) error

	// Scoring methods
	SetScore(score *models.CriticalityScore) error
	GetScore(assetID string) (*models.CriticalityScore, error)
	GetAllAssets() []models.Asset
}

// InMemoryRepo implements AssetRepository using in-memory maps with mutex protection.
type InMemoryRepo struct {
	mu            sync.RWMutex
	assets        map[string]models.Asset
	relationships map[string]models.AssetRelationship
	scores        map[string]models.CriticalityScore
	nextID        int
}

// NewInMemoryRepo creates a new in-memory repository.
func NewInMemoryRepo() *InMemoryRepo {
	return &InMemoryRepo{
		assets:        make(map[string]models.Asset),
		relationships: make(map[string]models.AssetRelationship),
		scores:        make(map[string]models.CriticalityScore),
		nextID:        1,
	}
}

// GenerateID creates a unique ID for new entities.
func (r *InMemoryRepo) GenerateID() string {
	r.mu.Lock()
	defer r.mu.Unlock()
	id := fmt.Sprintf("asset-%04d", r.nextID)
	r.nextID++
	return id
}

// List returns a paginated, filtered list of assets.
func (r *InMemoryRepo) List(filter models.AssetFilter, pagination models.Pagination) (*models.PaginatedResult, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	var filtered []models.Asset
	for _, a := range r.assets {
		if matchesFilter(a, filter) {
			filtered = append(filtered, a)
		}
	}

	total := len(filtered)

	// Apply pagination
	start := pagination.Offset
	if start > total {
		start = total
	}
	end := start + pagination.Limit
	if end > total {
		end = total
	}
	if pagination.Limit <= 0 {
		end = total
	}

	return &models.PaginatedResult{
		Assets: filtered[start:end],
		Total:  total,
		Offset: pagination.Offset,
		Limit:  pagination.Limit,
	}, nil
}

// GetByID retrieves a single asset by its ID.
func (r *InMemoryRepo) GetByID(id string) (*models.Asset, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	asset, ok := r.assets[id]
	if !ok {
		return nil, fmt.Errorf("asset not found: %s", id)
	}
	return &asset, nil
}

// Create adds a new asset to the repository.
func (r *InMemoryRepo) Create(asset *models.Asset) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if asset.ID == "" {
		return fmt.Errorf("asset ID is required")
	}
	if _, exists := r.assets[asset.ID]; exists {
		return fmt.Errorf("asset already exists: %s", asset.ID)
	}

	now := time.Now().UTC()
	asset.CreatedAt = now
	asset.UpdatedAt = now
	if asset.LastSeen.IsZero() {
		asset.LastSeen = now
	}

	r.assets[asset.ID] = *asset
	return nil
}

// Update modifies an existing asset.
func (r *InMemoryRepo) Update(asset *models.Asset) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if _, exists := r.assets[asset.ID]; !exists {
		return fmt.Errorf("asset not found: %s", asset.ID)
	}

	asset.UpdatedAt = time.Now().UTC()
	r.assets[asset.ID] = *asset
	return nil
}

// Delete removes an asset by ID.
func (r *InMemoryRepo) Delete(id string) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if _, exists := r.assets[id]; !exists {
		return fmt.Errorf("asset not found: %s", id)
	}
	delete(r.assets, id)
	return nil
}

// Search performs a case-insensitive search across name, description, IP, and tags.
func (r *InMemoryRepo) Search(query string) ([]models.Asset, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	q := strings.ToLower(query)
	var results []models.Asset

	for _, a := range r.assets {
		if strings.Contains(strings.ToLower(a.Name), q) ||
			strings.Contains(strings.ToLower(a.Description), q) ||
			strings.Contains(strings.ToLower(a.IPAddress), q) ||
			containsTag(a.Tags, q) {
			results = append(results, a)
		}
	}
	return results, nil
}

// BulkCreate adds multiple assets and returns the count of successful inserts and any errors.
func (r *InMemoryRepo) BulkCreate(assets []models.Asset) (int, []error) {
	var errs []error
	created := 0
	for i := range assets {
		if err := r.Create(&assets[i]); err != nil {
			errs = append(errs, fmt.Errorf("asset[%d]: %w", i, err))
		} else {
			created++
		}
	}
	return created, errs
}

// Count returns the total number of assets.
func (r *InMemoryRepo) Count() int {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return len(r.assets)
}

// GetByType returns all assets of a given type.
func (r *InMemoryRepo) GetByType(assetType models.AssetType) ([]models.Asset, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	var results []models.Asset
	for _, a := range r.assets {
		if a.Type == assetType {
			results = append(results, a)
		}
	}
	return results, nil
}

// CreateRelationship adds a relationship to the repository.
func (r *InMemoryRepo) CreateRelationship(rel *models.AssetRelationship) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if rel.ID == "" {
		return fmt.Errorf("relationship ID is required")
	}
	rel.CreatedAt = time.Now().UTC()
	r.relationships[rel.ID] = *rel
	return nil
}

// GetRelationships returns all relationships involving the given asset (as source or target).
func (r *InMemoryRepo) GetRelationships(assetID string) ([]models.AssetRelationship, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	var results []models.AssetRelationship
	for _, rel := range r.relationships {
		if rel.SourceID == assetID || rel.TargetID == assetID {
			results = append(results, rel)
		}
	}
	return results, nil
}

// GetAllRelationships returns all relationships.
func (r *InMemoryRepo) GetAllRelationships() []models.AssetRelationship {
	r.mu.RLock()
	defer r.mu.RUnlock()

	results := make([]models.AssetRelationship, 0, len(r.relationships))
	for _, rel := range r.relationships {
		results = append(results, rel)
	}
	return results
}

// DeleteRelationship removes a relationship by ID.
func (r *InMemoryRepo) DeleteRelationship(id string) error {
	r.mu.Lock()
	defer r.mu.Unlock()

	if _, exists := r.relationships[id]; !exists {
		return fmt.Errorf("relationship not found: %s", id)
	}
	delete(r.relationships, id)
	return nil
}

// SetScore stores or updates a criticality score for an asset.
func (r *InMemoryRepo) SetScore(score *models.CriticalityScore) error {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.scores[score.AssetID] = *score
	return nil
}

// GetScore retrieves the criticality score for an asset.
func (r *InMemoryRepo) GetScore(assetID string) (*models.CriticalityScore, error) {
	r.mu.RLock()
	defer r.mu.RUnlock()

	score, ok := r.scores[assetID]
	if !ok {
		return nil, fmt.Errorf("score not found for asset: %s", assetID)
	}
	return &score, nil
}

// GetAllAssets returns all assets as a slice.
func (r *InMemoryRepo) GetAllAssets() []models.Asset {
	r.mu.RLock()
	defer r.mu.RUnlock()

	results := make([]models.Asset, 0, len(r.assets))
	for _, a := range r.assets {
		results = append(results, a)
	}
	return results
}

func matchesFilter(a models.Asset, f models.AssetFilter) bool {
	if f.Type != "" && a.Type != f.Type {
		return false
	}
	if f.Criticality != "" && a.Criticality != f.Criticality {
		return false
	}
	if f.Status != "" && a.Status != f.Status {
		return false
	}
	if f.Owner != "" && a.Owner != f.Owner {
		return false
	}
	if len(f.Tags) > 0 {
		for _, tag := range f.Tags {
			if !containsTag(a.Tags, tag) {
				return false
			}
		}
	}
	return true
}

func containsTag(tags []string, tag string) bool {
	for _, t := range tags {
		if strings.ToLower(t) == tag {
			return true
		}
	}
	return false
}
