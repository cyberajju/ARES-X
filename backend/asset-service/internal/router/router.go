package router

import (
	"net/http"
	"strings"

	"github.com/cyberajju/ARES-X/backend/asset-service/internal/config"
	"github.com/cyberajju/ARES-X/backend/asset-service/internal/handlers"
	"github.com/cyberajju/ARES-X/backend/asset-service/internal/middleware"
	"github.com/cyberajju/ARES-X/backend/asset-service/internal/repository"
	"github.com/cyberajju/ARES-X/backend/asset-service/internal/services"
)

// New creates and configures the HTTP router with all asset service routes.
func New(cfg *config.Config, repo repository.AssetRepository, ingestionSvc *services.IngestionService, scoringSvc *services.ScoringService, relationshipSvc *services.RelationshipService) http.Handler {
	assetHandler := handlers.NewAssetHandler(repo, ingestionSvc, scoringSvc)
	relHandler := handlers.NewRelationshipHandler(repo, relationshipSvc)

	mux := http.NewServeMux()

	// Health check
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status":"healthy","service":"asset-service"}`))
	})

	// Asset routes
	mux.HandleFunc("/api/v1/assets", func(w http.ResponseWriter, r *http.Request) {
		// Exact path match for collection endpoints
		path := strings.TrimSuffix(r.URL.Path, "/")
		if path != "/api/v1/assets" {
			http.NotFound(w, r)
			return
		}
		switch r.Method {
		case http.MethodGet:
			assetHandler.ListAssets(w, r)
		case http.MethodPost:
			assetHandler.CreateAsset(w, r)
		default:
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		}
	})

	mux.HandleFunc("/api/v1/assets/search", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		assetHandler.SearchAssets(w, r)
	})

	mux.HandleFunc("/api/v1/assets/bulk-import", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		assetHandler.BulkImport(w, r)
	})

	mux.HandleFunc("/api/v1/assets/stats", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		assetHandler.GetStats(w, r)
	})

	// Individual asset routes - use prefix matching
	mux.HandleFunc("/api/v1/assets/", func(w http.ResponseWriter, r *http.Request) {
		// Check if this is search/bulk-import/stats (already handled)
		path := r.URL.Path
		if strings.HasPrefix(path, "/api/v1/assets/search") ||
			strings.HasPrefix(path, "/api/v1/assets/bulk-import") ||
			strings.HasPrefix(path, "/api/v1/assets/stats") {
			return
		}
		switch r.Method {
		case http.MethodGet:
			assetHandler.GetAsset(w, r)
		case http.MethodPut:
			assetHandler.UpdateAsset(w, r)
		case http.MethodDelete:
			assetHandler.DeleteAsset(w, r)
		default:
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		}
	})

	// Relationship routes
	mux.HandleFunc("/api/v1/relationships", func(w http.ResponseWriter, r *http.Request) {
		path := strings.TrimSuffix(r.URL.Path, "/")
		if path != "/api/v1/relationships" {
			http.NotFound(w, r)
			return
		}
		if r.Method == http.MethodPost {
			relHandler.CreateRelationship(w, r)
		} else {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		}
	})

	mux.HandleFunc("/api/v1/relationships/", func(w http.ResponseWriter, r *http.Request) {
		switch r.Method {
		case http.MethodGet:
			relHandler.GetRelationships(w, r)
		case http.MethodDelete:
			relHandler.DeleteRelationship(w, r)
		default:
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		}
	})

	// Apply middleware
	handler := middleware.Logging(mux)

	return handler
}
