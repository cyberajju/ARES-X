package services

import (
	"encoding/json"
	"fmt"
	"os"
	"sync"
	"time"
)

// EventType represents the type of an audit event.
type EventType string

const (
	EventLogin        EventType = "LOGIN"
	EventLogout       EventType = "LOGOUT"
	EventAuthFailure  EventType = "AUTH_FAILURE"
	EventAssetCreate  EventType = "ASSET_CREATE"
	EventAssetDelete  EventType = "ASSET_DELETE"
	EventPathCompute  EventType = "PATH_COMPUTE"
	EventConfigChange EventType = "CONFIG_CHANGE"
)

// AuditEvent represents a single audit log entry.
type AuditEvent struct {
	Timestamp time.Time `json:"timestamp"`
	EventType EventType `json:"event_type"`
	UserID    string    `json:"user_id"`
	IPAddress string    `json:"ip_address"`
	Details   string    `json:"details"`
}

// AuditService handles security audit logging.
type AuditService struct {
	mu     sync.Mutex
	writer *json.Encoder
}

// NewAuditService creates a new AuditService that writes to stdout.
func NewAuditService() *AuditService {
	return &AuditService{
		writer: json.NewEncoder(os.Stdout),
	}
}

// LogEvent logs a security audit event.
func (s *AuditService) LogEvent(eventType EventType, userID, details, ipAddress string) {
	event := AuditEvent{
		Timestamp: time.Now().UTC(),
		EventType: eventType,
		UserID:    userID,
		IPAddress: ipAddress,
		Details:   details,
	}

	s.mu.Lock()
	defer s.mu.Unlock()

	// Output as structured JSON log
	data, err := json.Marshal(map[string]interface{}{
		"level":      "info",
		"component":  "audit",
		"timestamp":  event.Timestamp.Format(time.RFC3339),
		"event_type": event.EventType,
		"user_id":    event.UserID,
		"ip_address": event.IPAddress,
		"details":    event.Details,
	})
	if err != nil {
		return
	}
	fmt.Fprintln(os.Stdout, string(data))
}
