package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"strings"

	"github.com/cyberajju/ARES-X/backend/asset-service/internal/models"
	"github.com/cyberajju/ARES-X/backend/asset-service/internal/repository"
	"github.com/cyberajju/ARES-X/backend/asset-service/internal/services"
)

// AssetHandler manages HTTP endpoints for asset CRUD operations.
type AssetHandler struct {
	repo        repository.AssetRepository
	ingestion   *services.IngestionService
	scoring     *services.ScoringService
}

// NewAssetHandler creates a new asset handler.
func NewAssetHandler(repo repository.AssetRepository, ingestion *services.IngestionService, scoring *services.ScoringService) *AssetHandler {
	return &AssetHandler{
		repo:      repo,
		ingestion: ingestion,
		scoring:   scoring,
	}
}

// ListAssets handles GET /api/v1/assets with filtering and pagination.
func (h *AssetHandler) ListAssets(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()

	filter := models.AssetFilter{
		Type:        models.AssetType(q.Get("type")),
		Criticality: models.Criticality(q.Get("criticality")),
		Status:      models.AssetStatus(q.Get("status")),
		Owner:       q.Get("owner"),
	}
	if tags := q.Get("tags"); tags != "" {
		filter.Tags = strings.Split(tags, ",")
	}

	offset, _ := strconv.Atoi(q.Get("offset"))
	limit, _ := strconv.Atoi(q.Get("limit"))
	if limit <= 0 {
		limit = 50
	}

	pagination := models.Pagination{Offset: offset, Limit: limit}

	result, err := h.repo.List(filter, pagination)
	if err != nil {
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}

	writeJSON(w, http.StatusOK, result)
}

// GetAsset handles GET /api/v1/assets/{id}.
func (h *AssetHandler) GetAsset(w http.ResponseWriter, r *http.Request) {
	id := extractPathParam(r.URL.Path, "/api/v1/assets/")
	if id == "" || strings.Contains(id, "/") {
		writeError(w, http.StatusBadRequest, "invalid asset ID")
		return
	}

	asset, err := h.repo.GetByID(id)
	if err != nil {
		writeError(w, http.StatusNotFound, err.Error())
		return
	}

	writeJSON(w, http.StatusOK, asset)
}

// CreateAsset handles POST /api/v1/assets.
func (h *AssetHandler) CreateAsset(w http.ResponseWriter, r *http.Request) {
	var asset models.Asset
	if err := json.NewDecoder(r.Body).Decode(&asset); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body: "+err.Error())
		return
	}

	if asset.ID == "" {
		asset.ID = fmt.Sprintf("asset-%04d", h.repo.Count()+1)
	}

	if err := h.ingestion.IngestAsset(&asset); err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}

	writeJSON(w, http.StatusCreated, asset)
}

// UpdateAsset handles PUT /api/v1/assets/{id}.
func (h *AssetHandler) UpdateAsset(w http.ResponseWriter, r *http.Request) {
	id := extractPathParam(r.URL.Path, "/api/v1/assets/")
	if id == "" || strings.Contains(id, "/") {
		writeError(w, http.StatusBadRequest, "invalid asset ID")
		return
	}

	existing, err := h.repo.GetByID(id)
	if err != nil {
		writeError(w, http.StatusNotFound, err.Error())
		return
	}

	var updated models.Asset
	if err := json.NewDecoder(r.Body).Decode(&updated); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body: "+err.Error())
		return
	}

	updated.ID = existing.ID
	updated.CreatedAt = existing.CreatedAt

	if err := h.repo.Update(&updated); err != nil {
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}

	// Recalculate score
	score := h.scoring.CalculateCriticality(&updated)
	_ = h.repo.SetScore(score)

	writeJSON(w, http.StatusOK, updated)
}

// DeleteAsset handles DELETE /api/v1/assets/{id}.
func (h *AssetHandler) DeleteAsset(w http.ResponseWriter, r *http.Request) {
	id := extractPathParam(r.URL.Path, "/api/v1/assets/")
	if id == "" || strings.Contains(id, "/") {
		writeError(w, http.StatusBadRequest, "invalid asset ID")
		return
	}

	if err := h.repo.Delete(id); err != nil {
		writeError(w, http.StatusNotFound, err.Error())
		return
	}

	writeJSON(w, http.StatusOK, map[string]string{"status": "deleted", "id": id})
}

// SearchAssets handles GET /api/v1/assets/search?q=query.
func (h *AssetHandler) SearchAssets(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query().Get("q")
	if query == "" {
		writeError(w, http.StatusBadRequest, "query parameter 'q' is required")
		return
	}

	results, err := h.repo.Search(query)
	if err != nil {
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"query":   query,
		"results": results,
		"count":   len(results),
	})
}

// BulkImport handles POST /api/v1/assets/bulk-import.
func (h *AssetHandler) BulkImport(w http.ResponseWriter, r *http.Request) {
	var assets []models.Asset
	if err := json.NewDecoder(r.Body).Decode(&assets); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body: "+err.Error())
		return
	}

	// Assign IDs to assets that lack them
	baseCount := h.repo.Count()
	for i := range assets {
		if assets[i].ID == "" {
			assets[i].ID = fmt.Sprintf("asset-%04d", baseCount+i+1)
		}
	}

	created, errs := h.ingestion.IngestBulk(assets)

	var errMsgs []string
	for _, e := range errs {
		errMsgs = append(errMsgs, e.Error())
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"created": created,
		"errors":  errMsgs,
		"total":   len(assets),
	})
}

// GetStats handles GET /api/v1/assets/stats.
func (h *AssetHandler) GetStats(w http.ResponseWriter, r *http.Request) {
	allAssets := h.repo.GetAllAssets()

	typeCount := make(map[string]int)
	critCount := make(map[string]int)
	statusCount := make(map[string]int)

	for _, a := range allAssets {
		typeCount[string(a.Type)]++
		critCount[string(a.Criticality)]++
		statusCount[string(a.Status)]++
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"total":            len(allAssets),
		"by_type":          typeCount,
		"by_criticality":   critCount,
		"by_status":        statusCount,
	})
}

func extractPathParam(path, prefix string) string {
	trimmed := strings.TrimPrefix(path, prefix)
	// Remove trailing slash
	trimmed = strings.TrimSuffix(trimmed, "/")
	return trimmed
}

func writeJSON(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}

func writeError(w http.ResponseWriter, status int, message string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(map[string]interface{}{
		"error":  message,
		"status": status,
	})
}
