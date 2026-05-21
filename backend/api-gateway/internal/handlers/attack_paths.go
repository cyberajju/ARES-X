package handlers

import (
	"encoding/json"
	"net/http"
	"time"

	"github.com/cyberajju/ARES-X/backend/api-gateway/internal/models"
	"github.com/cyberajju/ARES-X/backend/api-gateway/internal/services"
)

// Mock attack paths
var mockAttackPaths = []models.AttackPath{
	{
		ID:          "ap-001",
		Name:        "Lateral Movement via Service Account",
		Description: "Attack path exploiting over-privileged service account to reach domain controller",
		RiskScore:   9.1,
		Likelihood:  0.75,
		Impact:      9.8,
		SourceNode:  "node-002",
		TargetNode:  "node-001",
		Status:      "active",
		Steps: []models.PathStep{
			{Order: 1, NodeID: "node-002", NodeLabel: "Web Server", Action: "Initial Access", Technique: models.Technique{ID: "T1190", Name: "Exploit Public-Facing Application", MitreRef: "T1190"}, Probability: 0.8, Impact: 5.0},
			{Order: 2, NodeID: "node-004", NodeLabel: "svc-admin", Action: "Credential Theft", Technique: models.Technique{ID: "T1003", Name: "OS Credential Dumping", MitreRef: "T1003"}, Probability: 0.7, Impact: 7.0},
			{Order: 3, NodeID: "node-001", NodeLabel: "Domain Controller", Action: "Lateral Movement", Technique: models.Technique{ID: "T1021", Name: "Remote Services", MitreRef: "T1021"}, Probability: 0.6, Impact: 9.8},
		},
		TTPs: []models.TTP{
			{TacticID: "TA0001", TacticName: "Initial Access", TechniqueID: "T1190", Name: "Exploit Public-Facing Application", Description: "Exploiting vulnerabilities in internet-facing applications"},
			{TacticID: "TA0006", TacticName: "Credential Access", TechniqueID: "T1003", Name: "OS Credential Dumping", Description: "Dumping credentials from operating system"},
			{TacticID: "TA0008", TacticName: "Lateral Movement", TechniqueID: "T1021", Name: "Remote Services", Description: "Using remote services to move laterally"},
		},
		ComputedAt: time.Date(2024, 3, 15, 10, 30, 0, 0, time.UTC),
	},
	{
		ID:          "ap-002",
		Name:        "Privilege Escalation via Misconfigured Permissions",
		Description: "Attack path leveraging misconfigured AD permissions to escalate to domain admin",
		RiskScore:   8.5,
		Likelihood:  0.6,
		Impact:      9.5,
		SourceNode:  "node-005",
		TargetNode:  "node-006",
		Status:      "active",
		Steps: []models.PathStep{
			{Order: 1, NodeID: "node-005", NodeLabel: "DMZ Subnet", Action: "Network Discovery", Technique: models.Technique{ID: "T1046", Name: "Network Service Discovery", MitreRef: "T1046"}, Probability: 0.9, Impact: 3.0},
			{Order: 2, NodeID: "node-004", NodeLabel: "svc-admin", Action: "Account Manipulation", Technique: models.Technique{ID: "T1098", Name: "Account Manipulation", MitreRef: "T1098"}, Probability: 0.5, Impact: 8.0},
			{Order: 3, NodeID: "node-006", NodeLabel: "Domain Admin", Action: "Privilege Escalation", Technique: models.Technique{ID: "T1078", Name: "Valid Accounts", MitreRef: "T1078"}, Probability: 0.4, Impact: 9.5},
		},
		TTPs: []models.TTP{
			{TacticID: "TA0007", TacticName: "Discovery", TechniqueID: "T1046", Name: "Network Service Discovery", Description: "Discovering network services for lateral movement"},
			{TacticID: "TA0003", TacticName: "Persistence", TechniqueID: "T1098", Name: "Account Manipulation", Description: "Manipulating accounts for persistent access"},
			{TacticID: "TA0004", TacticName: "Privilege Escalation", TechniqueID: "T1078", Name: "Valid Accounts", Description: "Using valid accounts for privilege escalation"},
		},
		ComputedAt: time.Date(2024, 3, 14, 14, 0, 0, 0, time.UTC),
	},
}

// AttackPathHandler handles attack path-related endpoints.
type AttackPathHandler struct {
	auditService *services.AuditService
}

// NewAttackPathHandler creates a new AttackPathHandler.
func NewAttackPathHandler(auditService *services.AuditService) *AttackPathHandler {
	return &AttackPathHandler{auditService: auditService}
}

// ComputeAttackPaths handles POST /api/v1/attack-paths/compute
func (h *AttackPathHandler) ComputeAttackPaths(w http.ResponseWriter, r *http.Request) {
	var req models.ComputeAttackPathRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "invalid request body",
			Code:    "BAD_REQUEST",
		})
		return
	}

	if req.SourceNodeID == "" || req.TargetNodeID == "" {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "source_node_id and target_node_id are required",
			Code:    "VALIDATION_ERROR",
		})
		return
	}

	h.auditService.LogEvent(services.EventPathCompute, "", "attack path computation triggered", "")

	// Return mock computed path
	result := mockAttackPaths[0]
	result.SourceNode = req.SourceNodeID
	result.TargetNode = req.TargetNodeID
	result.ComputedAt = time.Now().UTC()

	writeJSON(w, http.StatusAccepted, models.ApiResponse[models.AttackPath]{
		Success: true,
		Data:    result,
		Message: "attack path computation initiated",
	})
}

// ListAttackPaths handles GET /api/v1/attack-paths
func (h *AttackPathHandler) ListAttackPaths(w http.ResponseWriter, r *http.Request) {
	page := parseIntParam(r, "page", 1)
	pageSize := parseIntParam(r, "page_size", 20)

	total := len(mockAttackPaths)
	totalPages := (total + pageSize - 1) / pageSize

	start := (page - 1) * pageSize
	end := start + pageSize
	if start > total {
		start = total
	}
	if end > total {
		end = total
	}

	writeJSON(w, http.StatusOK, models.PaginatedResponse[models.AttackPath]{
		Success:    true,
		Data:       mockAttackPaths[start:end],
		Total:      total,
		Page:       page,
		PageSize:   pageSize,
		TotalPages: totalPages,
	})
}

// GetAttackPathDetails handles GET /api/v1/attack-paths/{id}
func (h *AttackPathHandler) GetAttackPathDetails(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	if id == "" {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "attack path ID is required",
			Code:    "BAD_REQUEST",
		})
		return
	}

	for _, ap := range mockAttackPaths {
		if ap.ID == id {
			writeJSON(w, http.StatusOK, models.ApiResponse[models.AttackPath]{
				Success: true,
				Data:    ap,
			})
			return
		}
	}

	writeJSON(w, http.StatusNotFound, models.ErrorResponse{
		Success: false,
		Error:   "attack path not found",
		Code:    "NOT_FOUND",
	})
}

// Simulate handles POST /api/v1/attack-paths/simulate
func (h *AttackPathHandler) Simulate(w http.ResponseWriter, r *http.Request) {
	var cfg models.SimulationConfig
	if err := json.NewDecoder(r.Body).Decode(&cfg); err != nil {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "invalid request body",
			Code:    "BAD_REQUEST",
		})
		return
	}

	if cfg.SourceNodeID == "" || cfg.TargetNodeID == "" {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "source_node_id and target_node_id are required",
			Code:    "VALIDATION_ERROR",
		})
		return
	}

	if cfg.Iterations <= 0 {
		cfg.Iterations = 1000
	}

	result := models.SimulationResult{
		ID:     "sim-" + generateRandomHex(4),
		Config: cfg,
		SuccessRate:     0.68,
		AverageSteps:    3.2,
		AverageDuration: 4.5,
		MostLikelyPath:  []string{cfg.SourceNodeID, "node-004", cfg.TargetNodeID},
		CriticalNodes:   []string{"node-004", "node-006"},
		Recommendations: []string{
			"Restrict service account privileges for svc-admin",
			"Implement network segmentation between DMZ and internal network",
			"Enable MFA for all administrative accounts",
			"Deploy endpoint detection on critical servers",
		},
		CompletedAt: time.Now().UTC(),
	}

	writeJSON(w, http.StatusOK, models.ApiResponse[models.SimulationResult]{
		Success: true,
		Data:    result,
		Message: "simulation completed",
	})
}
