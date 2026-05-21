package models

import "time"

// AssetType represents the category of an asset.
type AssetType string

const (
	AssetTypeServer     AssetType = "server"
	AssetTypeWorkstation AssetType = "workstation"
	AssetTypeNetwork    AssetType = "network_device"
	AssetTypeDatabase   AssetType = "database"
	AssetTypeApplication AssetType = "application"
	AssetTypeContainer  AssetType = "container"
	AssetTypeCloudResource AssetType = "cloud_resource"
	AssetTypeIoT        AssetType = "iot_device"
)

// Criticality represents the criticality level of an asset.
type Criticality string

const (
	CriticalityCritical Criticality = "critical"
	CriticalityHigh     Criticality = "high"
	CriticalityMedium   Criticality = "medium"
	CriticalityLow      Criticality = "low"
)

// AssetStatus represents the operational status of an asset.
type AssetStatus string

const (
	AssetStatusActive       AssetStatus = "active"
	AssetStatusInactive     AssetStatus = "inactive"
	AssetStatusMaintenance  AssetStatus = "maintenance"
	AssetStatusDecommissioned AssetStatus = "decommissioned"
)

// Asset represents an infrastructure asset in the system.
type Asset struct {
	ID           string      `json:"id"`
	Name         string      `json:"name"`
	Type         AssetType   `json:"type"`
	Criticality  Criticality `json:"criticality"`
	Status       AssetStatus `json:"status"`
	IPAddress    string      `json:"ip_address,omitempty"`
	Hostname     string      `json:"hostname,omitempty"`
	OS           string      `json:"os,omitempty"`
	Owner        string      `json:"owner,omitempty"`
	Department   string      `json:"department,omitempty"`
	Location     string      `json:"location,omitempty"`
	Tags         []string    `json:"tags,omitempty"`
	RiskScore    float64     `json:"risk_score"`
	CreatedAt    time.Time   `json:"created_at"`
	UpdatedAt    time.Time   `json:"updated_at"`
}

// AssetFilter represents query parameters for filtering assets.
type AssetFilter struct {
	Type        AssetType   `json:"type,omitempty"`
	Criticality Criticality `json:"criticality,omitempty"`
	Status      AssetStatus `json:"status,omitempty"`
	Search      string      `json:"search,omitempty"`
	Page        int         `json:"page"`
	PageSize    int         `json:"page_size"`
}

// AssetCreateRequest represents the payload to create a new asset.
type AssetCreateRequest struct {
	Name        string      `json:"name"`
	Type        AssetType   `json:"type"`
	Criticality Criticality `json:"criticality"`
	Status      AssetStatus `json:"status,omitempty"`
	IPAddress   string      `json:"ip_address,omitempty"`
	Hostname    string      `json:"hostname,omitempty"`
	OS          string      `json:"os,omitempty"`
	Owner       string      `json:"owner,omitempty"`
	Department  string      `json:"department,omitempty"`
	Location    string      `json:"location,omitempty"`
	Tags        []string    `json:"tags,omitempty"`
}

// AssetUpdateRequest represents the payload to update an existing asset.
type AssetUpdateRequest struct {
	Name        *string      `json:"name,omitempty"`
	Type        *AssetType   `json:"type,omitempty"`
	Criticality *Criticality `json:"criticality,omitempty"`
	Status      *AssetStatus `json:"status,omitempty"`
	IPAddress   *string      `json:"ip_address,omitempty"`
	Hostname    *string      `json:"hostname,omitempty"`
	OS          *string      `json:"os,omitempty"`
	Owner       *string      `json:"owner,omitempty"`
	Department  *string      `json:"department,omitempty"`
	Location    *string      `json:"location,omitempty"`
	Tags        []string     `json:"tags,omitempty"`
}

// BulkImportRequest represents a request to bulk import assets.
type BulkImportRequest struct {
	Assets []AssetCreateRequest `json:"assets"`
}

// BulkImportResponse represents the result of a bulk import operation.
type BulkImportResponse struct {
	Imported int      `json:"imported"`
	Failed   int      `json:"failed"`
	Errors   []string `json:"errors,omitempty"`
}
