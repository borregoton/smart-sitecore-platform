-- Add v1.0 compatibility tables alongside v2.0 schema
-- These tables are needed for EnhancedPhase1Extractor to work

-- v1.0 Sites table
CREATE TABLE IF NOT EXISTS sites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    url VARCHAR(500) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- v1.0 Scans table
CREATE TABLE IF NOT EXISTS scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    site_id UUID REFERENCES sites(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'running',
    subscription_tier VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    finished_at TIMESTAMPTZ,
    error TEXT
);

-- v1.0 Scan modules table
CREATE TABLE IF NOT EXISTS scan_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES scans(id) ON DELETE CASCADE,
    module VARCHAR(100) NOT NULL,
    data_source VARCHAR(100) NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 0.0,
    requires_credentials BOOLEAN DEFAULT FALSE,
    duration_ms INTEGER DEFAULT 0,
    error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- v1.0 Analysis results table
CREATE TABLE IF NOT EXISTS analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_module_id UUID REFERENCES scan_modules(id) ON DELETE CASCADE,
    result JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_sites_url ON sites(url);
CREATE INDEX IF NOT EXISTS idx_scans_site_id ON scans(site_id);
CREATE INDEX IF NOT EXISTS idx_scans_status ON scans(status);
CREATE INDEX IF NOT EXISTS idx_scan_modules_scan_id ON scan_modules(scan_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_scan_module_id ON analysis_results(scan_module_id);

-- Success message
SELECT 'v1.0 compatibility tables created successfully' as result;