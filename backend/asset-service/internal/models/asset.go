package models

import (
	"time"
)

// AssetType represents the category of an asset.
type AssetType string

const (
	AssetTypeServer       AssetType = "server"
	AssetTypeWorkstation  AssetType = "workstation"
	AssetTypeRouter       AssetType = "router"
	AssetTypeSwitch       AssetType = "switch"
	AssetTypeFirewall     AssetType = "firewall"
	AssetTypeLoadBalancer AssetType = "load_balancer"
	AssetTypeDatabase     AssetType = "database"
	AssetTypeApplication  AssetType = "application"
	AssetTypeCloudVM      AssetType = "cloud_vm"
	AssetTypeContainer    AssetType = "container"
	AssetTypeIdentity     AssetType = "identity"
	AssetTypeOTController AssetType = "ot_controller"
	AssetTypeOTSensor     AssetType = "ot_sensor"
	AssetTypeMobileDevice AssetType = "mobile_device"
	AssetTypeIoTDevice    AssetType = "iot_device"
)

// Criticality represents the importance level of an asset.
type Criticality string

const (
	CriticalityCritical      Criticality = "critical"
	CriticalityHigh          Criticality = "high"
	CriticalityMedium        Criticality = "medium"
	CriticalityLow           Criticality = "low"
	CriticalityInformational Criticality = "informational"
)

// AssetStatus represents the current state of an asset.
type AssetStatus string

const (
	AssetStatusActive          AssetStatus = "active"
	AssetStatusInactive        AssetStatus = "inactive"
	AssetStatusDecommissioned  AssetStatus = "decommissioned"
	AssetStatusMaintenance     AssetStatus = "maintenance"
	AssetStatusCompromised     AssetStatus = "compromised"
	AssetStatusUnknown         AssetStatus = "unknown"
)

// Asset is the base model for all asset types.
type Asset struct {
	ID          string            `json:"id"`
	Name        string            `json:"name"`
	Type        AssetType         `json:"type"`
	Criticality Criticality       `json:"criticality"`
	Status      AssetStatus       `json:"status"`
	Description string            `json:"description,omitempty"`
	Owner       string            `json:"owner,omitempty"`
	Location    string            `json:"location,omitempty"`
	IPAddress   string            `json:"ip_address,omitempty"`
	MACAddress  string            `json:"mac_address,omitempty"`
	OS          string            `json:"os,omitempty"`
	Version     string            `json:"version,omitempty"`
	LastSeen    time.Time         `json:"last_seen"`
	CreatedAt   time.Time         `json:"created_at"`
	UpdatedAt   time.Time         `json:"updated_at"`
	Tags        []string          `json:"tags,omitempty"`
	Metadata    map[string]string `json:"metadata,omitempty"`
}

// ServerAsset extends Asset with server-specific fields.
type ServerAsset struct {
	Asset
	CPUs       int      `json:"cpus"`
	MemoryGB   int      `json:"memory_gb"`
	DiskGB     int      `json:"disk_gb"`
	Services   []string `json:"services,omitempty"`
	OpenPorts  []int    `json:"open_ports,omitempty"`
	PatchLevel string   `json:"patch_level,omitempty"`
}

// NetworkAsset extends Asset with network-specific fields.
type NetworkAsset struct {
	Asset
	CIDR      string `json:"cidr,omitempty"`
	VLAN      int    `json:"vlan,omitempty"`
	Zone      string `json:"zone,omitempty"`
	Protocol  string `json:"protocol,omitempty"`
	Bandwidth string `json:"bandwidth,omitempty"`
}

// IdentityAsset extends Asset with identity-specific fields.
type IdentityAsset struct {
	Asset
	IdentityType      string   `json:"identity_type,omitempty"`
	Privileges        []string `json:"privileges,omitempty"`
	LastAuthenticated time.Time `json:"last_authenticated"`
	MFAEnabled        bool     `json:"mfa_enabled"`
	ServiceAccount    bool     `json:"service_account"`
}

// CloudAsset extends Asset with cloud-specific fields.
type CloudAsset struct {
	Asset
	Provider       string   `json:"provider,omitempty"`
	Region         string   `json:"region,omitempty"`
	ServiceType    string   `json:"service_type,omitempty"`
	AccountID      string   `json:"account_id,omitempty"`
	VPC            string   `json:"vpc,omitempty"`
	SecurityGroups []string `json:"security_groups,omitempty"`
}

// OTAsset extends Asset with operational technology fields.
type OTAsset struct {
	Asset
	Protocol        string `json:"protocol,omitempty"`
	FirmwareVersion string `json:"firmware_version,omitempty"`
	SafetyLevel     string `json:"safety_level,omitempty"`
	PurdueLevel     int    `json:"purdue_level"`
	Vendor          string `json:"vendor,omitempty"`
}

// AssetFilter holds filtering criteria for listing assets.
type AssetFilter struct {
	Type        AssetType   `json:"type,omitempty"`
	Criticality Criticality `json:"criticality,omitempty"`
	Status      AssetStatus `json:"status,omitempty"`
	Owner       string      `json:"owner,omitempty"`
	Tags        []string    `json:"tags,omitempty"`
}

// Pagination holds pagination parameters.
type Pagination struct {
	Offset int `json:"offset"`
	Limit  int `json:"limit"`
}

// PaginatedResult wraps a list result with total count.
type PaginatedResult struct {
	Assets []Asset `json:"assets"`
	Total  int     `json:"total"`
	Offset int     `json:"offset"`
	Limit  int     `json:"limit"`
}
