-- ARES-X Asset Service: PostgreSQL Schema
-- Migration 001: Create core tables for assets, relationships, and scoring

BEGIN;

-- Assets table
CREATE TABLE IF NOT EXISTS assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    criticality VARCHAR(20) NOT NULL DEFAULT 'medium',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    ip_address INET,
    mac_address MACADDR,
    os VARCHAR(255),
    version VARCHAR(100),
    owner VARCHAR(255),
    location VARCHAR(255),
    description TEXT,
    metadata JSONB DEFAULT '{}',
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Asset relationships table
CREATE TABLE IF NOT EXISTS asset_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    target_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL DEFAULT 1.0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT no_self_reference CHECK (source_id != target_id)
);

-- Criticality scores table
CREATE TABLE IF NOT EXISTS criticality_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id UUID NOT NULL REFERENCES assets(id) ON DELETE CASCADE,
    overall FLOAT NOT NULL DEFAULT 0.0,
    business_impact FLOAT NOT NULL DEFAULT 0.0,
    exposure FLOAT NOT NULL DEFAULT 0.0,
    vuln_density FLOAT NOT NULL DEFAULT 0.0,
    connectivity FLOAT NOT NULL DEFAULT 0.0,
    calculated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes on assets
CREATE INDEX idx_assets_type ON assets(type);
CREATE INDEX idx_assets_criticality ON assets(criticality);
CREATE INDEX idx_assets_status ON assets(status);
CREATE INDEX idx_assets_ip_address ON assets(ip_address);
CREATE INDEX idx_assets_owner ON assets(owner);
CREATE INDEX idx_assets_tags ON assets USING GIN(tags);
CREATE INDEX idx_assets_metadata ON assets USING GIN(metadata);

-- Indexes on relationships
CREATE INDEX idx_relationships_source_id ON asset_relationships(source_id);
CREATE INDEX idx_relationships_target_id ON asset_relationships(target_id);
CREATE INDEX idx_relationships_type ON asset_relationships(type);

-- Indexes on scoring
CREATE INDEX idx_scores_asset_id ON criticality_scores(asset_id);
CREATE INDEX idx_scores_overall ON criticality_scores(overall);
CREATE INDEX idx_scores_calculated_at ON criticality_scores(calculated_at);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_assets_updated_at
    BEFORE UPDATE ON assets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;
