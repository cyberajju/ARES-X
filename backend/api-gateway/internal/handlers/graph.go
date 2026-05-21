package handlers

import (
	"net/http"

	"github.com/cyberajju/ARES-X/backend/api-gateway/internal/models"
)

// Mock graph data
var mockNodes = []models.GraphNode{
	{ID: "node-001", Type: models.NodeTypeAsset, Label: "Domain Controller", Properties: map[string]string{"os": "Windows Server 2022"}, RiskScore: 9.2},
	{ID: "node-002", Type: models.NodeTypeAsset, Label: "Web Server", Properties: map[string]string{"os": "Ubuntu 22.04"}, RiskScore: 7.5},
	{ID: "node-003", Type: models.NodeTypeVulnerability, Label: "CVE-2024-1234", Properties: map[string]string{"cvss": "9.8"}, RiskScore: 9.8},
	{ID: "node-004", Type: models.NodeTypeIdentity, Label: "svc-admin", Properties: map[string]string{"type": "service_account"}, RiskScore: 8.0},
	{ID: "node-005", Type: models.NodeTypeNetwork, Label: "DMZ Subnet", Properties: map[string]string{"cidr": "10.0.0.0/24"}, RiskScore: 6.0},
	{ID: "node-006", Type: models.NodeTypePermission, Label: "Domain Admin", Properties: map[string]string{"scope": "domain"}, RiskScore: 9.5},
}

var mockEdges = []models.GraphEdge{
	{ID: "edge-001", Source: "node-001", Target: "node-003", Type: models.EdgeTypeExploits, Weight: 0.95},
	{ID: "edge-002", Source: "node-004", Target: "node-001", Type: models.EdgeTypeHasAccess, Weight: 0.8},
	{ID: "edge-003", Source: "node-002", Target: "node-005", Type: models.EdgeTypeConnectsTo, Weight: 0.7},
	{ID: "edge-004", Source: "node-004", Target: "node-006", Type: models.EdgeTypeHasAccess, Weight: 0.9},
	{ID: "edge-005", Source: "node-005", Target: "node-002", Type: models.EdgeTypeContains, Weight: 0.6},
}

// GraphHandler handles graph-related endpoints.
type GraphHandler struct{}

// NewGraphHandler creates a new GraphHandler.
func NewGraphHandler() *GraphHandler {
	return &GraphHandler{}
}

// QueryNodes handles GET /api/v1/graph/nodes
func (h *GraphHandler) QueryNodes(w http.ResponseWriter, r *http.Request) {
	nodeType := r.URL.Query().Get("type")
	limit := parseIntParam(r, "limit", 50)
	minRisk := parseFloatParam(r, "min_risk", 0.0)

	var filtered []models.GraphNode
	for _, node := range mockNodes {
		if nodeType != "" && string(node.Type) != nodeType {
			continue
		}
		if node.RiskScore < minRisk {
			continue
		}
		filtered = append(filtered, node)
		if len(filtered) >= limit {
			break
		}
	}

	writeJSON(w, http.StatusOK, models.ApiResponse[[]models.GraphNode]{
		Success: true,
		Data:    filtered,
	})
}

// QueryEdges handles GET /api/v1/graph/edges
func (h *GraphHandler) QueryEdges(w http.ResponseWriter, r *http.Request) {
	edgeType := r.URL.Query().Get("type")
	limit := parseIntParam(r, "limit", 50)

	var filtered []models.GraphEdge
	for _, edge := range mockEdges {
		if edgeType != "" && string(edge.Type) != edgeType {
			continue
		}
		filtered = append(filtered, edge)
		if len(filtered) >= limit {
			break
		}
	}

	writeJSON(w, http.StatusOK, models.ApiResponse[[]models.GraphEdge]{
		Success: true,
		Data:    filtered,
	})
}

// GetPaths handles GET /api/v1/graph/paths
func (h *GraphHandler) GetPaths(w http.ResponseWriter, r *http.Request) {
	source := r.URL.Query().Get("source")
	target := r.URL.Query().Get("target")

	if source == "" || target == "" {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "source and target parameters are required",
			Code:    "BAD_REQUEST",
		})
		return
	}

	// Return mock path result
	result := models.PathResult{
		Nodes: []models.GraphNode{
			{ID: source, Type: models.NodeTypeAsset, Label: "Source Node", RiskScore: 7.0},
			{ID: "node-intermediate", Type: models.NodeTypeVulnerability, Label: "CVE-2024-1234", RiskScore: 9.8},
			{ID: target, Type: models.NodeTypeAsset, Label: "Target Node", RiskScore: 9.2},
		},
		Edges: []models.GraphEdge{
			{ID: "path-edge-1", Source: source, Target: "node-intermediate", Type: models.EdgeTypeExploits, Weight: 0.9},
			{ID: "path-edge-2", Source: "node-intermediate", Target: target, Type: models.EdgeTypeConnectsTo, Weight: 0.85},
		},
		TotalRisk: 8.8,
		Length:    2,
	}

	writeJSON(w, http.StatusOK, models.ApiResponse[models.PathResult]{
		Success: true,
		Data:    result,
	})
}

// GetBlastRadius handles GET /api/v1/graph/blast-radius/{nodeId}
func (h *GraphHandler) GetBlastRadius(w http.ResponseWriter, r *http.Request) {
	nodeID := r.PathValue("nodeId")
	if nodeID == "" {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "node ID is required",
			Code:    "BAD_REQUEST",
		})
		return
	}

	result := models.BlastRadiusResult{
		OriginNode: models.GraphNode{
			ID:        nodeID,
			Type:      models.NodeTypeAsset,
			Label:     "Compromised Node",
			RiskScore: 8.5,
		},
		AffectedNodes: []models.GraphNode{
			{ID: "node-002", Type: models.NodeTypeAsset, Label: "Web Server", RiskScore: 7.5},
			{ID: "node-004", Type: models.NodeTypeIdentity, Label: "svc-admin", RiskScore: 8.0},
			{ID: "node-006", Type: models.NodeTypePermission, Label: "Domain Admin", RiskScore: 9.5},
		},
		AffectedEdges: []models.GraphEdge{
			{ID: "blast-edge-1", Source: nodeID, Target: "node-002", Type: models.EdgeTypeConnectsTo, Weight: 0.8},
			{ID: "blast-edge-2", Source: nodeID, Target: "node-004", Type: models.EdgeTypeHasAccess, Weight: 0.9},
		},
		TotalImpact: 8.3,
		Depth:       3,
	}

	writeJSON(w, http.StatusOK, models.ApiResponse[models.BlastRadiusResult]{
		Success: true,
		Data:    result,
	})
}

// GetDependencies handles GET /api/v1/graph/dependencies/{nodeId}
func (h *GraphHandler) GetDependencies(w http.ResponseWriter, r *http.Request) {
	nodeID := r.PathValue("nodeId")
	if nodeID == "" {
		writeJSON(w, http.StatusBadRequest, models.ErrorResponse{
			Success: false,
			Error:   "node ID is required",
			Code:    "BAD_REQUEST",
		})
		return
	}

	result := models.DependencyResult{
		Node: models.GraphNode{
			ID:        nodeID,
			Type:      models.NodeTypeAsset,
			Label:     "Target Node",
			RiskScore: 7.5,
		},
		Dependencies: []models.GraphNode{
			{ID: "node-005", Type: models.NodeTypeNetwork, Label: "DMZ Subnet", RiskScore: 6.0},
			{ID: "node-004", Type: models.NodeTypeIdentity, Label: "svc-admin", RiskScore: 8.0},
		},
		Dependents: []models.GraphNode{
			{ID: "node-001", Type: models.NodeTypeAsset, Label: "Domain Controller", RiskScore: 9.2},
		},
	}

	writeJSON(w, http.StatusOK, models.ApiResponse[models.DependencyResult]{
		Success: true,
		Data:    result,
	})
}
