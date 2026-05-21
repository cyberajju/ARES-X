package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
	"time"

	"github.com/cyberajju/ARES-X/backend/api-gateway/internal/models"
	"github.com/cyberajju/ARES-X/backend/api-gateway/internal/services"
)

// Mock assets data
var mockAssets = []models.Asset{
	{
		ID:          "asset-001",
		Name:        "Primary Domain Controller",
		Type:        models.AssetTypeServer,
		Criticality: models.CriticalityCritical,
		Status:      models.AssetStatusActive,
		IPAddress:   "10.0.1.10",
		Hostname:    "dc-primary.ares-x.mil",
		OS:          "Windows Server 2022",
		Owner:       "IT Security",
		Department:  "Infrastructure",
		Location:    "Data Center A",
		Tags:        []string{"active-directory", "authentication", "critical"},
		RiskScore:   9.2,
		CreatedAt:   time.Date(2024, 1, 1, 0, 0, 0, 0, time.UTC),
		UpdatedAt:   time.Date(2024, 3, 15, 0, 0, 0, 0, time.UTC),
	},
	{
		ID:          "asset-002",
		Name:        "Web Application Server",
		Type:        models.AssetTypeServer,
		Criticality: models.CriticalityHigh,
		Status:      models.AssetStatusActive,
		IPAddress:   "10.0.2.20",
		Hostname:    "web-app-01.ares-x.mil",
		OS:          "Ubuntu 22.04",
		Owner:       "DevOps",
		Department:  "Engineering",
		Location:    "Data Center B",
		Tags:        []string{"web", "production", "public-facing"},
		RiskScore:   7.5,
		CreatedAt:   time.Date(2024, 1, 10, 0, 0, 0, 0, time.UTC),
		UpdatedAt:   time.Date(2024, 3, 10, 0, 0, 0, 0, time.UTC),
	},
	{
		ID:          "asset-003",
		Name:        "Core Database Cluster",
		Type:        models.AssetTypeDatabase,
		Criticality: models.CriticalityCritical,
		Status:      models.AssetStatusActive,
		IPAddress:   "10.0.3.30",
		Hostname:    "db-cluster-01.ares-x.mil",
		OS:          "RHEL 9",
		Owner:       "DBA Team",
		Department:  "Data Services",
		Location:    "Data Center A",
		Tags:        []string{"postgresql", "classified", "encrypted"},
		RiskScore:   8.8,
		CreatedAt:   time.Date(2024, 1, 5, 0, 0, 0, 0, time.UTC),
		UpdatedAt:   time.Date(2024, 3, 12, 0, 0, 0, 0, time.UTC),
	},
	{
		ID:          "asset-004",
		Name:        "Edge Firewall",
		Type:        models.AssetTypeNetwork,
		Criticality: models.CriticalityHigh,
		Status:      models.AssetStatusActive,
		IPAddress:   "10.0.0.1",
		Hostname:    "fw-edge-01.ares-x.mil",
		OS:          "Palo Alto PAN-OS 11",
		Owner:       "Network Security",
		Department:  "Security Operations",
		Location:    "DMZ",
		Tags:        []string{"firewall", "perimeter", "network"},
		RiskScore:   6.5,
		CreatedAt:   time.Date(2024, 1, 3, 0, 0, 0, 0, time.UTC),
		UpdatedAt:   time.Date(2024, 2, 28, 0, 0, 0, 0, time.UTC),
	},
	{
		ID:          "asset-005",
		Name:        "Developer Workstation Pool",
		Type:        models.AssetTypeWorkstation,
		Criticality: models.CriticalityMedium,
		Status:      models.AssetStatusActive,
		IPAddress:   "10.0.10.0/24",
		Hostname:    "dev-ws-pool.ares-x.mil",
		OS:          "Windows 11 Enterprise",
		Owner:       "Engineering",
		Department:  "Engineering",
		Location:    "Building 2",
		Tags:        []string{"development", "workstation", "user-endpoint"},
		RiskScore:   5.2,
		CreatedAt:   time.Date(2024, 2, 1, 0, 0, 0, 0, time.UTC),
		UpdatedAt:   time.Date(2024, 3, 1, 0, 0, 0, 0, time.UTC),
	},
}

// AssetHandler handles asset-related endpoints.
type AssetHandler struct {
	auditService *services.AuditService
}

// NewAssetHandler creates a new AssetHandler.
func NewAssetHandler(auditService *services.AuditService) *AssetHandler {
	return &AssetHandler{auditService: auditService}
}

// ListAssets handles GET /api/v1/assets
func (h *AssetHandler) ListAssets(w http.ResponseWriter, r *http.Request) {
	page := parseIntParam(r, "page", 1)
	pageSize := parseIntParam(r, "page_size", 20)
	assetType := r.URL.Query().Get("type")
	criticality := r.URL.Query().Get("criticality")
	status := r.URL.Query().Get("status")

	// Filter assets
	filtered := filterAssets(mockAssets, assetType, criticality, status)

	// Paginate
	total := len(filtered)
	start := (page - 1) * pageSize
	end := start + pageSize
	if start > total {
		start = total
	}
	if end > total {
		end = total
	}

	totalPages := (total + pageSize - 1) / pageSize

	writeJSON(w, http.StatusOK, models.PaginatedResponse[models.Asset]{
		Success:    true,
		Data:       filtered[start:end],
		Total:      total,
		Page:       page,
		PageSize:   pageSize,
		TotalPages: totalPages,
	})
}

// GetAsset handles GET /api/v1/assets/{id}
func (h *AssetHandler) GetAsset(w http.ResponseWriter, r *http.Request) {
	id := extractPathParam(r, "id")
	if id == "" {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "asset id is required",
			Code:    "BAD_REQUEST",
		})
		return
	}

	for _, asset := range mockAssets {
		if asset.ID == id {
			writeJSON(w, http.StatusOK, models.ApiResponse[models.Asset]{
				Success: true,
				Data:    asset,
			})
			return
		}
	}

	writeJSON(w, http.StatusNotFound, models.ErrorResponse{
		Success: false,
		Error:   "asset not found",
		Code:    "NOT_FOUND",
	})
}

// CreateAsset handles POST /api/v1/assets
func (h *AssetHandler) CreateAsset(w http.ResponseWriter, r *http.Request) {
	var req models.AssetCreateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "invalid request body",
			Code:    "BAD_REQUEST",
		})
		return
	}

	// Validation
	var validationErrors []models.ValidationError
	if req.Name == "" {
		validationErrors = append(validationErrors, models.ValidationError{Field: "name", Message: "name is required"})
	}
	if req.Type == "" {
		validationErrors = append(validationErrors, models.ValidationError{Field: "type", Message: "type is required"})
	}
	if req.Criticality == "" {
		validationErrors = append(validationErrors, models.ValidationError{Field: "criticality", Message: "criticality is required"})
	}

	if len(validationErrors) > 0 {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "validation failed",
			Code:    "VALIDATION_ERROR",
			Details: validationErrors,
		})
		return
	}

	now := time.Now().UTC()
	asset := models.Asset{
		ID:          fmt.Sprintf("asset-%s", generateRandomHex(4)),
		Name:        req.Name,
		Type:        req.Type,
		Criticality: req.Criticality,
		Status:      req.Status,
		IPAddress:   req.IPAddress,
		Hostname:    req.Hostname,
		OS:          req.OS,
		Owner:       req.Owner,
		Department:  req.Department,
		Location:    req.Location,
		Tags:        req.Tags,
		RiskScore:   0.0,
		CreatedAt:   now,
		UpdatedAt:   now,
	}

	if asset.Status == "" {
		asset.Status = models.AssetStatusActive
	}

	h.auditService.LogEvent(services.EventAssetCreate, "", fmt.Sprintf("asset created: %s", asset.ID), clientIP(r))

	writeJSON(w, http.StatusCreated, models.ApiResponse[models.Asset]{
		Success: true,
		Data:    asset,
		Message: "asset created successfully",
	})
}

// UpdateAsset handles PUT /api/v1/assets/{id}
func (h *AssetHandler) UpdateAsset(w http.ResponseWriter, r *http.Request) {
	id := extractPathParam(r, "id")
	if id == "" {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "asset id is required",
			Code:    "BAD_REQUEST",
		})
		return
	}

	var req models.AssetUpdateRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "invalid request body",
			Code:    "BAD_REQUEST",
		})
		return
	}

	// Find existing asset
	for _, asset := range mockAssets {
		if asset.ID == id {
			// Apply updates
			if req.Name != nil {
				asset.Name = *req.Name
			}
			if req.Type != nil {
				asset.Type = *req.Type
			}
			if req.Criticality != nil {
				asset.Criticality = *req.Criticality
			}
			if req.Status != nil {
				asset.Status = *req.Status
			}
			asset.UpdatedAt = time.Now().UTC()

			writeJSON(w, http.StatusOK, models.ApiResponse[models.Asset]{
				Success: true,
				Data:    asset,
				Message: "asset updated successfully",
			})
			return
		}
	}

	writeJSON(w, http.StatusNotFound, models.ErrorResponse{
		Success: false,
		Error:   "asset not found",
		Code:    "NOT_FOUND",
	})
}

// DeleteAsset handles DELETE /api/v1/assets/{id}
func (h *AssetHandler) DeleteAsset(w http.ResponseWriter, r *http.Request) {
	id := extractPathParam(r, "id")
	if id == "" {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "asset id is required",
			Code:    "BAD_REQUEST",
		})
		return
	}

	for _, asset := range mockAssets {
		if asset.ID == id {
			h.auditService.LogEvent(services.EventAssetDelete, "", fmt.Sprintf("asset deleted: %s", id), clientIP(r))
			writeJSON(w, http.StatusOK, models.ApiResponse[any]{
				Success: true,
				Message: "asset deleted successfully",
			})
			return
		}
	}

	writeJSON(w, http.StatusNotFound, models.ErrorResponse{
		Success: false,
		Error:   "asset not found",
		Code:    "NOT_FOUND",
	})
}

// SearchAssets handles GET /api/v1/assets/search
func (h *AssetHandler) SearchAssets(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query().Get("q")
	if query == "" {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "search query 'q' is required",
			Code:    "BAD_REQUEST",
		})
		return
	}

	query = strings.ToLower(query)
	var results []models.Asset
	for _, asset := range mockAssets {
		if strings.Contains(strings.ToLower(asset.Name), query) ||
			strings.Contains(strings.ToLower(asset.Hostname), query) ||
			strings.Contains(strings.ToLower(asset.IPAddress), query) {
			results = append(results, asset)
		}
	}

	writeJSON(w, http.StatusOK, models.PaginatedResponse[models.Asset]{
		Success:    true,
		Data:       results,
		Total:      len(results),
		Page:       1,
		PageSize:   len(results),
		TotalPages: 1,
	})
}

// BulkImport handles POST /api/v1/assets/bulk-import
func (h *AssetHandler) BulkImport(w http.ResponseWriter, r *http.Request) {
	var req models.BulkImportRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "invalid request body",
			Code:    "BAD_REQUEST",
		})
		return
	}

	if len(req.Assets) == 0 {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "at least one asset is required",
			Code:    "VALIDATION_ERROR",
		})
		return
	}

	imported := 0
	failed := 0
	var errors []string

	for i, asset := range req.Assets {
		if asset.Name == "" || asset.Type == "" {
			failed++
			errors = append(errors, fmt.Sprintf("asset at index %d: name and type are required", i))
			continue
		}
		imported++
	}

	writeJSON(w, http.StatusOK, models.ApiResponse[models.BulkImportResponse]{
		Success: true,
		Data: models.BulkImportResponse{
			Imported: imported,
			Failed:   failed,
			Errors:   errors,
		},
		Message: fmt.Sprintf("bulk import completed: %d imported, %d failed", imported, failed),
	})
}

func filterAssets(assets []models.Asset, assetType, criticality, status string) []models.Asset {
	if assetType == "" && criticality == "" && status == "" {
		return assets
	}

	var filtered []models.Asset
	for _, asset := range assets {
		if assetType != "" && string(asset.Type) != assetType {
			continue
		}
		if criticality != "" && string(asset.Criticality) != criticality {
			continue
		}
		if status != "" && string(asset.Status) != status {
			continue
		}
		filtered = append(filtered, asset)
	}
	return filtered
}

// extractPathParam extracts a named path parameter from the URL.
// Expects the path parameter to be stored in the request context by the router.
func extractPathParam(r *http.Request, name string) string {
	if val := r.PathValue(name); val != "" {
		return val
	}
	return ""
}
