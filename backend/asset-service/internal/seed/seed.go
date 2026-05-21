package seed

import (
	"time"

	"github.com/cyberajju/ARES-X/backend/asset-service/internal/models"
	"github.com/cyberajju/ARES-X/backend/asset-service/internal/repository"
	"github.com/cyberajju/ARES-X/backend/asset-service/internal/services"
)

// LoadSeedData populates the repository with sample assets, relationships, and scores.
func LoadSeedData(repo repository.AssetRepository, scoring *services.ScoringService, relationship *services.RelationshipService) {
	now := time.Now().UTC()

	assets := []models.Asset{
		{ID: "asset-0001", Name: "prod-db-primary", Type: models.AssetTypeDatabase, Criticality: models.CriticalityCritical, Status: models.AssetStatusActive, IPAddress: "10.0.1.10", OS: "PostgreSQL 15", Owner: "dba-team", Location: "us-east-1", Tags: []string{"production", "database", "critical"}, Metadata: map[string]string{"patch_level": "current"}, LastSeen: now, CreatedAt: now, UpdatedAt: now},
		{ID: "asset-0002", Name: "prod-web-server-01", Type: models.AssetTypeServer, Criticality: models.CriticalityHigh, Status: models.AssetStatusActive, IPAddress: "10.0.1.20", OS: "Ubuntu 22.04", Owner: "platform-team", Location: "us-east-1", Tags: []string{"production", "web", "frontend"}, Metadata: map[string]string{"patch_level": "current"}, LastSeen: now, CreatedAt: now, UpdatedAt: now},
		{ID: "asset-0003", Name: "prod-web-server-02", Type: models.AssetTypeServer, Criticality: models.CriticalityHigh, Status: models.AssetStatusActive, IPAddress: "10.0.1.21", OS: "Ubuntu 22.04", Owner: "platform-team", Location: "us-east-1", Tags: []string{"production", "web", "frontend"}, Metadata: map[string]string{"patch_level": "behind"}, LastSeen: now, CreatedAt: now, UpdatedAt: now},
		{ID: "asset-0004", Name: "core-firewall-01", Type: models.AssetTypeFirewall, Criticality: models.CriticalityCritical, Status: models.AssetStatusActive, IPAddress: "10.0.0.1", OS: "Palo Alto PAN-OS 11", Owner: "security-team", Location: "us-east-1", Tags: []string{"production", "security", "perimeter"}, Metadata: map[string]string{"patch_level": "current"}, LastSeen: now, CreatedAt: now, UpdatedAt: now},
		{ID: "asset-0005", Name: "core-router-01", Type: models.AssetTypeRouter, Criticality: models.CriticalityHigh, Status: models.AssetStatusActive, IPAddress: "10.0.0.2", OS: "Cisco IOS-XE 17", Owner: "network-team", Location: "us-east-1", Tags: []string{"production", "network", "core"}, Metadata: map[string]string{"patch_level": "current"}, LastSeen: now, CreatedAt: now, UpdatedAt: now},
		{ID: "asset-0006", Name: "load-balancer-01", Type: models.AssetTypeLoadBalancer, Criticality: models.CriticalityHigh, Status: models.AssetStatusActive, IPAddress: "10.0.1.5", OS: "HAProxy 2.8", Owner: "platform-team", Location: "us-east-1", Tags: []string{"production", "load-balancer"}, Metadata: map[string]string{"patch_level": "current"}, LastSeen: now, CreatedAt: now, UpdatedAt: now},
		{ID: "asset-0007", Name: "admin-workstation-01", Type: models.AssetTypeWorkstation, Criticality: models.CriticalityMedium, Status: models.AssetStatusActive, IPAddress: "10.0.2.100", OS: "Windows 11 Pro", Owner: "admin-user", Location: "us-east-1", Tags: []string{"workstation", "admin"}, Metadata: map[string]string{"patch_level": "current"}, LastSeen: now, CreatedAt: now, UpdatedAt: now},
		{ID: "asset-0008", Name: "dev-workstation-01", Type: models.AssetTypeWorkstation, Criticality: models.CriticalityLow, Status: models.AssetStatusActive, IPAddress: "10.0.2.101", OS: "macOS Sonoma", Owner: "developer-01", Location: "us-west-2", Tags: []string{"workstation", "development"}, Metadata: map[string]string{"patch_level": "current"}, LastSeen: now, CreatedAt: now, UpdatedAt: now},
		{ID: "asset-0009", Name: "svc-account-deploy", Type: models.AssetTypeIdentity, Criticality: models.CriticalityHigh, Status: models.AssetStatusActive, IPAddress: "", OS: "", Owner: "security-team", Location: "", Tags: []string{"identity", "service-account", "deployment"}, Metadata: map[string]string{}, LastSeen: now, CreatedAt: now, UpdatedAt: now},
		{ID: "asset-0010", Name: "svc-account-monitor", Type: models.AssetTypeIdentity, Criticality: models.CriticalityMedium, Status: models.AssetStatusActive, IPAddress: "", OS: "", Owner: "sre-team", Location: "", Tags: []string{"identity", "service-account", "monitoring"}, Metadata: map[string]string{}, LastSeen: now, CreatedAt: now, UpdatedAt: now},
		{ID: "asset-0011", Name: "aws-ec2-analytics", Type: models.AssetTypeCloudVM, Criticality: models.CriticalityMedium, Status: models.AssetStatusActive, IPAddress: "172.16.0.50", OS: "Amazon Linux 2023", Owner: "data-team", Location: "us-east-1", Tags: []string{"cloud", "aws", "analytics"}, Metadata: map[string]string{"patch_level": "behind", "provider": "aws"}, LastSeen: now, CreatedAt: now, UpdatedAt: now},
		{ID: "asset-0012", Name: "k8s-worker-01", Type: models.AssetTypeContainer, Criticality: models.CriticalityMedium, Status: models.AssetStatusActive, IPAddress: "10.0.3.10", OS: "containerd 1.7", Owner: "platform-team", Location: "us-east-1", Tags: []string{"kubernetes", "container", "production"}, Metadata: map[string]string{"patch_level": "current"}, LastSeen: now, CreatedAt: now, UpdatedAt: now},
		{ID: "asset-0013", Name: "scada-controller-01", Type: models.AssetTypeOTController, Criticality: models.CriticalityCritical, Status: models.AssetStatusActive, IPAddress: "192.168.100.10", OS: "Siemens S7-1500", Owner: "ot-team", Location: "plant-floor-1", Tags: []string{"ot", "scada", "critical-infrastructure"}, Metadata: map[string]string{"patch_level": "outdated", "purdue_level": "2"}, LastSeen: now, CreatedAt: now, UpdatedAt: now},
		{ID: "asset-0014", Name: "temp-sensor-array-01", Type: models.AssetTypeOTSensor, Criticality: models.CriticalityLow, Status: models.AssetStatusActive, IPAddress: "192.168.100.50", OS: "Embedded Linux", Owner: "ot-team", Location: "plant-floor-1", Tags: []string{"ot", "sensor", "temperature"}, Metadata: map[string]string{"patch_level": "outdated"}, LastSeen: now, CreatedAt: now, UpdatedAt: now},
		{ID: "asset-0015", Name: "mobile-exec-01", Type: models.AssetTypeMobileDevice, Criticality: models.CriticalityMedium, Status: models.AssetStatusActive, IPAddress: "", OS: "iOS 17", Owner: "exec-cto", Location: "mobile", Tags: []string{"mobile", "executive"}, Metadata: map[string]string{}, LastSeen: now, CreatedAt: now, UpdatedAt: now},
		{ID: "asset-0016", Name: "iot-camera-lobby", Type: models.AssetTypeIoTDevice, Criticality: models.CriticalityLow, Status: models.AssetStatusActive, IPAddress: "10.0.4.10", OS: "Firmware 3.2.1", Owner: "facilities-team", Location: "building-lobby", Tags: []string{"iot", "camera", "physical-security"}, Metadata: map[string]string{"patch_level": "outdated"}, LastSeen: now, CreatedAt: now, UpdatedAt: now},
		{ID: "asset-0017", Name: "core-switch-01", Type: models.AssetTypeSwitch, Criticality: models.CriticalityHigh, Status: models.AssetStatusActive, IPAddress: "10.0.0.3", OS: "Cisco NX-OS 10", Owner: "network-team", Location: "us-east-1", Tags: []string{"production", "network", "core"}, Metadata: map[string]string{"patch_level": "current"}, LastSeen: now, CreatedAt: now, UpdatedAt: now},
		{ID: "asset-0018", Name: "vpn-gateway", Type: models.AssetTypeApplication, Criticality: models.CriticalityHigh, Status: models.AssetStatusActive, IPAddress: "10.0.0.5", OS: "OpenVPN 2.6", Owner: "security-team", Location: "us-east-1", Tags: []string{"production", "security", "remote-access"}, Metadata: map[string]string{"patch_level": "current", "known_vulns": "2"}, LastSeen: now, CreatedAt: now, UpdatedAt: now},
	}

	for i := range assets {
		_ = repo.Create(&assets[i])
	}

	// Create relationships
	relationships := []models.AssetRelationship{
		{ID: "rel-0001", SourceID: "asset-0006", TargetID: "asset-0002", Type: models.RelConnectsTo, Confidence: 0.95},
		{ID: "rel-0002", SourceID: "asset-0006", TargetID: "asset-0003", Type: models.RelConnectsTo, Confidence: 0.95},
		{ID: "rel-0003", SourceID: "asset-0002", TargetID: "asset-0001", Type: models.RelDependsOn, Confidence: 0.9},
		{ID: "rel-0004", SourceID: "asset-0003", TargetID: "asset-0001", Type: models.RelDependsOn, Confidence: 0.9},
		{ID: "rel-0005", SourceID: "asset-0004", TargetID: "asset-0005", Type: models.RelManages, Confidence: 0.85},
		{ID: "rel-0006", SourceID: "asset-0004", TargetID: "asset-0017", Type: models.RelManages, Confidence: 0.85},
		{ID: "rel-0007", SourceID: "asset-0009", TargetID: "asset-0002", Type: models.RelAuthenticatesTo, Confidence: 0.9},
		{ID: "rel-0008", SourceID: "asset-0009", TargetID: "asset-0003", Type: models.RelAuthenticatesTo, Confidence: 0.9},
		{ID: "rel-0009", SourceID: "asset-0010", TargetID: "asset-0012", Type: models.RelMonitors, Confidence: 0.8},
		{ID: "rel-0010", SourceID: "asset-0013", TargetID: "asset-0014", Type: models.RelContains, Confidence: 0.95},
		{ID: "rel-0011", SourceID: "asset-0005", TargetID: "asset-0006", Type: models.RelConnectsTo, Confidence: 0.9},
		{ID: "rel-0012", SourceID: "asset-0018", TargetID: "asset-0007", Type: models.RelAuthenticatesTo, Confidence: 0.75},
	}

	for i := range relationships {
		_ = repo.CreateRelationship(&relationships[i])
	}

	// Calculate initial criticality scores for all assets
	scoring.RecalculateAll()
}
