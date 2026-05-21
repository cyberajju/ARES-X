package handlers

import (
	"net/http"
	"time"

	"github.com/cyberajju/ARES-X/backend/api-gateway/internal/models"
)

// DashboardHandler handles dashboard-related endpoints.
type DashboardHandler struct{}

// NewDashboardHandler creates a new DashboardHandler.
func NewDashboardHandler() *DashboardHandler {
	return &DashboardHandler{}
}

// GetStats handles GET /api/v1/dashboard/stats
func (h *DashboardHandler) GetStats(w http.ResponseWriter, r *http.Request) {
	stats := models.DashboardStats{
		TotalAssets:       1247,
		CriticalAssets:    89,
		TotalThreats:      342,
		ActiveAttackPaths: 23,
		HealthScore:       78.5,
		RiskScore:         6.8,
		OpenAlerts:        17,
		ResolvedToday:     8,
	}

	writeJSON(w, http.StatusOK, models.ApiResponse[models.DashboardStats]{
		Success: true,
		Data:    stats,
	})
}

// GetAlerts handles GET /api/v1/dashboard/alerts
func (h *DashboardHandler) GetAlerts(w http.ResponseWriter, r *http.Request) {
	now := time.Now().UTC()
	alerts := []models.Alert{
		{
			ID:          "alert-001",
			Title:       "Critical Vulnerability Detected on Domain Controller",
			Description: "CVE-2024-1234 (CVSS 9.8) detected on dc-primary.ares-x.mil",
			Severity:    models.AlertSeverityCritical,
			Source:      "vulnerability-scanner",
			Status:      "open",
			AssetID:     "asset-001",
			CreatedAt:   now.Add(-2 * time.Hour),
			UpdatedAt:   now.Add(-2 * time.Hour),
		},
		{
			ID:          "alert-002",
			Title:       "Unusual Lateral Movement Detected",
			Description: "Service account svc-admin accessing 15 systems in 5 minutes",
			Severity:    models.AlertSeverityHigh,
			Source:      "behavior-analytics",
			Status:      "investigating",
			AssetID:     "asset-002",
			CreatedAt:   now.Add(-4 * time.Hour),
			UpdatedAt:   now.Add(-1 * time.Hour),
		},
		{
			ID:          "alert-003",
			Title:       "Failed Login Attempts Threshold Exceeded",
			Description: "50 failed login attempts from IP 192.168.1.100 in last 10 minutes",
			Severity:    models.AlertSeverityMedium,
			Source:      "auth-monitor",
			Status:      "open",
			CreatedAt:   now.Add(-30 * time.Minute),
			UpdatedAt:   now.Add(-30 * time.Minute),
		},
		{
			ID:          "alert-004",
			Title:       "Certificate Expiring Soon",
			Description: "TLS certificate for web-app-01.ares-x.mil expires in 7 days",
			Severity:    models.AlertSeverityLow,
			Source:      "certificate-monitor",
			Status:      "open",
			AssetID:     "asset-002",
			CreatedAt:   now.Add(-24 * time.Hour),
			UpdatedAt:   now.Add(-24 * time.Hour),
		},
		{
			ID:          "alert-005",
			Title:       "New Attack Path Discovered",
			Description: "High-risk attack path from DMZ to Domain Admin identified",
			Severity:    models.AlertSeverityHigh,
			Source:      "attack-path-engine",
			Status:      "open",
			CreatedAt:   now.Add(-6 * time.Hour),
			UpdatedAt:   now.Add(-6 * time.Hour),
		},
	}

	writeJSON(w, http.StatusOK, models.ApiResponse[[]models.Alert]{
		Success: true,
		Data:    alerts,
	})
}

// GetStatus handles GET /api/v1/dashboard/status
func (h *DashboardHandler) GetStatus(w http.ResponseWriter, r *http.Request) {
	now := time.Now().UTC()
	status := models.SystemStatus{
		Overall: "operational",
		Services: []models.ServiceHealth{
			{Name: "api-gateway", Status: "healthy", Uptime: 99.9, Latency: 12, LastCheck: now},
			{Name: "graph-engine", Status: "healthy", Uptime: 99.8, Latency: 45, LastCheck: now},
			{Name: "asset-service", Status: "healthy", Uptime: 99.7, Latency: 23, LastCheck: now},
			{Name: "attack-path-engine", Status: "healthy", Uptime: 99.5, Latency: 150, LastCheck: now},
			{Name: "postgresql", Status: "healthy", Uptime: 99.99, Latency: 5, LastCheck: now},
			{Name: "redis", Status: "healthy", Uptime: 99.95, Latency: 2, LastCheck: now},
		},
	}

	writeJSON(w, http.StatusOK, models.ApiResponse[models.SystemStatus]{
		Success: true,
		Data:    status,
	})
}

// GetActivity handles GET /api/v1/dashboard/activity
func (h *DashboardHandler) GetActivity(w http.ResponseWriter, r *http.Request) {
	now := time.Now().UTC()
	activities := []models.RecentActivity{
		{ID: "act-001", Type: "login", Message: "Admin user logged in", UserID: "usr-001", UserName: "Admin User", Timestamp: now.Add(-10 * time.Minute)},
		{ID: "act-002", Type: "asset_scan", Message: "Vulnerability scan completed on 247 assets", UserID: "usr-002", UserName: "Security Analyst", Timestamp: now.Add(-30 * time.Minute)},
		{ID: "act-003", Type: "path_compute", Message: "Attack path analysis completed, 3 new paths found", UserID: "usr-002", UserName: "Security Analyst", Timestamp: now.Add(-1 * time.Hour)},
		{ID: "act-004", Type: "alert_resolve", Message: "Alert resolved: Expired TLS certificate renewed", UserID: "usr-003", UserName: "Network Operator", Timestamp: now.Add(-2 * time.Hour)},
		{ID: "act-005", Type: "asset_create", Message: "New asset added: monitoring-server-02", UserID: "usr-001", UserName: "Admin User", Timestamp: now.Add(-3 * time.Hour)},
		{ID: "act-006", Type: "config_change", Message: "RBAC policy updated: new analyst role permissions", UserID: "usr-001", UserName: "Admin User", Timestamp: now.Add(-5 * time.Hour)},
		{ID: "act-007", Type: "simulation", Message: "Monte Carlo simulation completed: 1000 iterations", UserID: "usr-002", UserName: "Security Analyst", Timestamp: now.Add(-6 * time.Hour)},
	}

	writeJSON(w, http.StatusOK, models.ApiResponse[[]models.RecentActivity]{
		Success: true,
		Data:    activities,
	})
}
