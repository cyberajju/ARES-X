package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"
	"strings"

	"github.com/cyberajju/ARES-X/backend/asset-service/internal/models"
	"github.com/cyberajju/ARES-X/backend/asset-service/internal/repository"
	"github.com/cyberajju/ARES-X/backend/asset-service/internal/services"
)

// RelationshipHandler manages HTTP endpoints for asset relationships.
type RelationshipHandler struct {
	repo            repository.AssetRepository
	relationshipSvc *services.RelationshipService
}

// NewRelationshipHandler creates a new relationship handler.
func NewRelationshipHandler(repo repository.AssetRepository, relationshipSvc *services.RelationshipService) *RelationshipHandler {
	return &RelationshipHandler{
		repo:            repo,
		relationshipSvc: relationshipSvc,
	}
}

// GetRelationships handles GET /api/v1/relationships/{assetId}.
func (h *RelationshipHandler) GetRelationships(w http.ResponseWriter, r *http.Request) {
	assetID := extractRelPathParam(r.URL.Path, "/api/v1/relationships/")
	if assetID == "" {
		writeError(w, http.StatusBadRequest, "asset ID is required")
		return
	}

	depthStr := r.URL.Query().Get("depth")
	depth := 1
	if depthStr != "" {
		if d, err := strconv.Atoi(depthStr); err == nil && d > 0 {
			depth = d
		}
	}

	var rels []models.AssetRelationship
	var err error

	if depth > 1 {
		rels, err = h.relationshipSvc.GetRelationshipGraph(assetID, depth)
	} else {
		rels, err = h.relationshipSvc.GetRelationships(assetID)
	}

	if err != nil {
		writeError(w, http.StatusInternalServerError, err.Error())
		return
	}

	if rels == nil {
		rels = []models.AssetRelationship{}
	}

	writeJSON(w, http.StatusOK, map[string]interface{}{
		"asset_id":      assetID,
		"relationships": rels,
		"count":         len(rels),
		"depth":         depth,
	})
}

// CreateRelationship handles POST /api/v1/relationships.
func (h *RelationshipHandler) CreateRelationship(w http.ResponseWriter, r *http.Request) {
	var rel models.AssetRelationship
	if err := json.NewDecoder(r.Body).Decode(&rel); err != nil {
		writeError(w, http.StatusBadRequest, "invalid request body: "+err.Error())
		return
	}

	if err := h.relationshipSvc.CreateRelationship(&rel); err != nil {
		writeError(w, http.StatusBadRequest, err.Error())
		return
	}

	writeJSON(w, http.StatusCreated, rel)
}

// DeleteRelationship handles DELETE /api/v1/relationships/{id}.
func (h *RelationshipHandler) DeleteRelationship(w http.ResponseWriter, r *http.Request) {
	id := extractRelPathParam(r.URL.Path, "/api/v1/relationships/")
	if id == "" {
		writeError(w, http.StatusBadRequest, "relationship ID is required")
		return
	}

	if err := h.repo.DeleteRelationship(id); err != nil {
		writeError(w, http.StatusNotFound, err.Error())
		return
	}

	writeJSON(w, http.StatusOK, map[string]string{"status": "deleted", "id": id})
}

func extractRelPathParam(path, prefix string) string {
	trimmed := strings.TrimPrefix(path, prefix)
	trimmed = strings.TrimSuffix(trimmed, "/")
	// Take only the first segment
	if idx := strings.Index(trimmed, "/"); idx >= 0 {
		trimmed = trimmed[:idx]
	}
	return trimmed
}
