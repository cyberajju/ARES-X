package models

import "time"

// AlertSeverity represents the severity level of an alert.
type AlertSeverity string

const (
	AlertSeverityCritical AlertSeverity = "critical"
	AlertSeverityHigh     AlertSeverity = "high"
	AlertSeverityMedium   AlertSeverity = "medium"
	AlertSeverityLow      AlertSeverity = "low"
	AlertSeverityInfo     AlertSeverity = "info"
)

// DashboardStats represents the overall dashboard statistics.
type DashboardStats struct {
	TotalAssets       int     `json:"total_assets"`
	CriticalAssets    int     `json:"critical_assets"`
	TotalThreats      int     `json:"total_threats"`
	ActiveAttackPaths int     `json:"active_attack_paths"`
	HealthScore       float64 `json:"health_score"`
	RiskScore         float64 `json:"risk_score"`
	OpenAlerts        int     `json:"open_alerts"`
	ResolvedToday     int     `json:"resolved_today"`
}

// Alert represents a security alert.
type Alert struct {
	ID          string        `json:"id"`
	Title       string        `json:"title"`
	Description string        `json:"description"`
	Severity    AlertSeverity `json:"severity"`
	Source      string        `json:"source"`
	Status      string        `json:"status"`
	AssetID     string        `json:"asset_id,omitempty"`
	CreatedAt   time.Time     `json:"created_at"`
	UpdatedAt   time.Time     `json:"updated_at"`
}

// ServiceHealth represents the health status of a service.
type ServiceHealth struct {
	Name      string  `json:"name"`
	Status    string  `json:"status"`
	Uptime    float64 `json:"uptime_percentage"`
	Latency   int     `json:"latency_ms"`
	LastCheck time.Time `json:"last_check"`
}

// SystemStatus represents the overall system status.
type SystemStatus struct {
	Overall  string          `json:"overall"`
	Services []ServiceHealth `json:"services"`
}

// RecentActivity represents a recent activity event.
type RecentActivity struct {
	ID        string    `json:"id"`
	Type      string    `json:"type"`
	Message   string    `json:"message"`
	UserID    string    `json:"user_id,omitempty"`
	UserName  string    `json:"user_name,omitempty"`
	Timestamp time.Time `json:"timestamp"`
}
