package router

import (
	"net/http"

	"github.com/cyberajju/ARES-X/backend/api-gateway/internal/config"
	"github.com/cyberajju/ARES-X/backend/api-gateway/internal/handlers"
	"github.com/cyberajju/ARES-X/backend/api-gateway/internal/middleware"
	"github.com/cyberajju/ARES-X/backend/api-gateway/internal/models"
	"github.com/cyberajju/ARES-X/backend/api-gateway/internal/services"
)

// New creates and configures the HTTP router with all routes and middleware.
func New(cfg *config.Config) http.Handler {
	mux := http.NewServeMux()

	// Initialize services
	jwtService := services.NewJWTService(cfg)
	auditService := services.NewAuditService()

	// Initialize handlers
	authHandler := handlers.NewAuthHandler(jwtService, auditService)
	assetHandler := handlers.NewAssetHandler(auditService)
	graphHandler := handlers.NewGraphHandler()
	attackPathHandler := handlers.NewAttackPathHandler(auditService)
	dashboardHandler := handlers.NewDashboardHandler()

	// Middleware factories
	authMiddleware := middleware.Auth(jwtService)
	corsConfig := middleware.CORSConfig{
		AllowedOrigins: cfg.AllowedOrigins,
		AllowedMethods: []string{"GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"},
		AllowedHeaders: []string{"Accept", "Authorization", "Content-Type", "X-Request-ID", "X-Requested-With"},
		MaxAge:         "86400",
	}
	corsMiddleware := middleware.CORS(corsConfig)

	// --- Public routes (no auth required) ---
	mux.HandleFunc("POST /api/v1/auth/login", authHandler.Login)
	mux.HandleFunc("POST /api/v1/auth/refresh", authHandler.RefreshToken)

	// --- Health check ---
	mux.HandleFunc("GET /api/v1/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte(`{"status":"healthy","service":"api-gateway"}`))
	})

	// --- Protected routes (require valid JWT) ---
	// Auth routes
	mux.Handle("POST /api/v1/auth/logout", authMiddleware(http.HandlerFunc(authHandler.Logout)))
	mux.Handle("POST /api/v1/auth/mfa/setup", authMiddleware(http.HandlerFunc(authHandler.InitMFA)))
	mux.Handle("POST /api/v1/auth/mfa/verify", authMiddleware(http.HandlerFunc(authHandler.VerifyMFA)))

	// Asset routes - read (any authenticated user)
	mux.Handle("GET /api/v1/assets", authMiddleware(http.HandlerFunc(assetHandler.ListAssets)))
	mux.Handle("GET /api/v1/assets/search", authMiddleware(http.HandlerFunc(assetHandler.SearchAssets)))
	mux.Handle("GET /api/v1/assets/{id}", authMiddleware(http.HandlerFunc(assetHandler.GetAsset)))

	// Asset routes - write (Analyst+)
	mux.Handle("POST /api/v1/assets", authMiddleware(middleware.RequireRole(models.RoleAnalyst)(http.HandlerFunc(assetHandler.CreateAsset))))
	mux.Handle("PUT /api/v1/assets/{id}", authMiddleware(middleware.RequireRole(models.RoleAnalyst)(http.HandlerFunc(assetHandler.UpdateAsset))))

	// Asset routes - admin only
	mux.Handle("DELETE /api/v1/assets/{id}", authMiddleware(middleware.RequireRole(models.RoleAdmin)(http.HandlerFunc(assetHandler.DeleteAsset))))
	mux.Handle("POST /api/v1/assets/bulk-import", authMiddleware(middleware.RequireRole(models.RoleAdmin)(http.HandlerFunc(assetHandler.BulkImport))))

	// Graph routes (any authenticated user)
	mux.Handle("GET /api/v1/graph/nodes", authMiddleware(http.HandlerFunc(graphHandler.QueryNodes)))
	mux.Handle("GET /api/v1/graph/edges", authMiddleware(http.HandlerFunc(graphHandler.QueryEdges)))
	mux.Handle("GET /api/v1/graph/paths", authMiddleware(http.HandlerFunc(graphHandler.GetPaths)))
	mux.Handle("GET /api/v1/graph/blast-radius/{nodeId}", authMiddleware(http.HandlerFunc(graphHandler.GetBlastRadius)))
	mux.Handle("GET /api/v1/graph/dependencies/{nodeId}", authMiddleware(http.HandlerFunc(graphHandler.GetDependencies)))

	// Attack path routes
	mux.Handle("GET /api/v1/attack-paths", authMiddleware(http.HandlerFunc(attackPathHandler.ListAttackPaths)))
	mux.Handle("GET /api/v1/attack-paths/{id}", authMiddleware(http.HandlerFunc(attackPathHandler.GetAttackPathDetails)))
	mux.Handle("POST /api/v1/attack-paths/compute", authMiddleware(middleware.RequireRole(models.RoleAnalyst)(http.HandlerFunc(attackPathHandler.ComputeAttackPaths))))
	mux.Handle("POST /api/v1/attack-paths/simulate", authMiddleware(middleware.RequireRole(models.RoleAnalyst)(http.HandlerFunc(attackPathHandler.Simulate))))

	// Dashboard routes (any authenticated user)
	mux.Handle("GET /api/v1/dashboard/stats", authMiddleware(http.HandlerFunc(dashboardHandler.GetStats)))
	mux.Handle("GET /api/v1/dashboard/alerts", authMiddleware(http.HandlerFunc(dashboardHandler.GetAlerts)))
	mux.Handle("GET /api/v1/dashboard/status", authMiddleware(http.HandlerFunc(dashboardHandler.GetStatus)))
	mux.Handle("GET /api/v1/dashboard/activity", authMiddleware(http.HandlerFunc(dashboardHandler.GetActivity)))

	// Apply global middleware: Logging -> CORS -> routes
	var handler http.Handler = mux
	handler = corsMiddleware(handler)
	handler = middleware.Logging(handler)

	return handler
}
