-- =====================================================
-- MULTI-SITE/MULTI-CUSTOMER ARCHITECTURE
-- =====================================================
-- Enhanced schema for scalable multi-customer analysis
-- Enables portfolio analysis, benchmarking, and comparison
--
-- Version: Phase 2 Multi-Site Enhancement
-- Created: 2025-01-22
-- Purpose: Support multiple customers and sites with
--          isolated data and cross-site analysis
-- =====================================================

-- =============================
-- CUSTOMER & ORGANIZATION MANAGEMENT
-- =============================

-- Store customer organizations/companies
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255) NOT NULL,
    -- Customer identification
    customer_code VARCHAR(50) UNIQUE NOT NULL, -- Short code like 'ACME', 'CONTOSO'
    domain VARCHAR(255), -- Primary domain for the organization
    -- Customer details
    industry VARCHAR(100),
    company_size VARCHAR(50), -- SMB, Enterprise, etc.
    region VARCHAR(100),
    -- Contact information
    primary_contact_name VARCHAR(255),
    primary_contact_email VARCHAR(255),
    -- Customer status
    is_active BOOLEAN DEFAULT TRUE,
    subscription_tier VARCHAR(50) DEFAULT 'Standard', -- Free, Standard, Premium, Enterprise
    -- Analysis preferences
    analysis_frequency VARCHAR(50) DEFAULT 'Monthly', -- Weekly, Monthly, Quarterly
    retention_period INTEGER DEFAULT 365, -- Days to retain data
    -- Security and access
    api_key_hash VARCHAR(255), -- For customer API access
    access_restrictions JSONB DEFAULT '{}'::jsonb, -- IP restrictions, etc.
    -- Metadata
    notes TEXT,
    tags JSONB DEFAULT '[]'::jsonb, -- For categorization
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_analysis_at TIMESTAMP WITH TIME ZONE
);

-- Store individual Sitecore sites/instances for each customer
CREATE TABLE IF NOT EXISTS customer_sites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    -- Site identification
    name VARCHAR(255) NOT NULL, -- Friendly name like 'Main Website', 'Mobile App'
    fqdn VARCHAR(255) NOT NULL, -- Full domain like 'www.acme.com'
    sitecore_url TEXT NOT NULL, -- Sitecore CM URL like 'https://cm.acme.com'
    -- Site characteristics
    site_type VARCHAR(50) DEFAULT 'Website', -- Website, Mobile, Intranet, etc.
    environment VARCHAR(50) DEFAULT 'Production', -- Dev, Staging, Production
    sitecore_version VARCHAR(50), -- 10.3, XM Cloud, etc.
    -- Technical details
    api_endpoint TEXT, -- GraphQL endpoint
    api_key_encrypted TEXT, -- Encrypted API key for this site
    authentication_method VARCHAR(50) DEFAULT 'API_KEY', -- API_KEY, OAUTH, etc.
    -- Site status
    is_active BOOLEAN DEFAULT TRUE,
    is_accessible BOOLEAN DEFAULT TRUE,
    last_successful_scan TIMESTAMP WITH TIME ZONE,
    last_scan_error TEXT,
    -- Analysis settings
    scan_frequency VARCHAR(50) DEFAULT 'Weekly',
    analysis_depth VARCHAR(50) DEFAULT 'Standard', -- Basic, Standard, Deep
    enabled_modules JSONB DEFAULT '["schema", "content", "templates"]'::jsonb,
    -- Performance and limits
    request_timeout INTEGER DEFAULT 30000, -- milliseconds
    max_content_items INTEGER DEFAULT 1000,
    rate_limit_delay INTEGER DEFAULT 100, -- milliseconds between requests
    -- Site metadata
    description TEXT,
    business_unit VARCHAR(255), -- For large organizations
    technology_stack JSONB DEFAULT '{}'::jsonb, -- Frontend tech, CMS version, etc.
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Constraints
    UNIQUE(customer_id, fqdn),
    UNIQUE(customer_id, sitecore_url)
);

-- Store site relationships and hierarchies
CREATE TABLE IF NOT EXISTS site_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_site_id UUID NOT NULL REFERENCES customer_sites(id) ON DELETE CASCADE,
    child_site_id UUID NOT NULL REFERENCES customer_sites(id) ON DELETE CASCADE,
    relationship_type VARCHAR(50) NOT NULL, -- PARENT_CHILD, CLUSTER, LOAD_BALANCED
    relationship_strength DECIMAL DEFAULT 1.0, -- For weighted analysis
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(parent_site_id, child_site_id)
);

-- =============================
-- ENHANCED SCANS TABLE
-- =============================

-- Update scans table to include customer and site context
-- Note: This assumes we'll migrate existing scans or start fresh
CREATE TABLE IF NOT EXISTS scans_v2 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    site_id UUID NOT NULL REFERENCES customer_sites(id) ON DELETE CASCADE,
    -- Scan identification
    scan_name VARCHAR(255), -- Optional friendly name
    scan_type VARCHAR(50) DEFAULT 'Full', -- Full, Incremental, Targeted
    -- Scan details (keep existing structure)
    target_url TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    -- Analysis scope
    modules_requested JSONB DEFAULT '["enhanced-schema", "enhanced-content", "enhanced-templates"]'::jsonb,
    analysis_depth VARCHAR(50) DEFAULT 'Standard',
    -- Results summary
    total_modules INTEGER DEFAULT 0,
    successful_modules INTEGER DEFAULT 0,
    average_confidence DECIMAL DEFAULT 0.0,
    -- Performance metrics
    total_duration_ms INTEGER DEFAULT 0,
    total_api_calls INTEGER DEFAULT 0,
    total_data_size_kb INTEGER DEFAULT 0,
    -- Error handling
    error_count INTEGER DEFAULT 0,
    warnings_count INTEGER DEFAULT 0,
    critical_issues JSONB DEFAULT '[]'::jsonb,
    -- Scan context
    triggered_by VARCHAR(100) DEFAULT 'Manual', -- Manual, Scheduled, API, Webhook
    trigger_details JSONB DEFAULT '{}'::jsonb,
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================
-- UPDATE EXISTING TABLES FOR MULTI-SITE
-- =============================

-- Add customer and site context to GraphQL types
ALTER TABLE graphql_types
ADD COLUMN IF NOT EXISTS customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
ADD COLUMN IF NOT EXISTS site_id UUID REFERENCES customer_sites(id) ON DELETE CASCADE;

-- Add customer and site context to content items
ALTER TABLE content_items
ADD COLUMN IF NOT EXISTS customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
ADD COLUMN IF NOT EXISTS site_id UUID REFERENCES customer_sites(id) ON DELETE CASCADE;

-- Add customer and site context to template definitions
ALTER TABLE template_definitions
ADD COLUMN IF NOT EXISTS customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
ADD COLUMN IF NOT EXISTS site_id UUID REFERENCES customer_sites(id) ON DELETE CASCADE;

-- Add customer and site context to field usage statistics
ALTER TABLE field_usage_statistics
ADD COLUMN IF NOT EXISTS customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
ADD COLUMN IF NOT EXISTS site_id UUID REFERENCES customer_sites(id) ON DELETE CASCADE;

-- =============================
-- CROSS-SITE ANALYSIS TABLES
-- =============================

-- Store comparative analysis results between sites
CREATE TABLE IF NOT EXISTS cross_site_comparisons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    comparison_name VARCHAR(255) NOT NULL,
    comparison_type VARCHAR(50) NOT NULL, -- SITE_VS_SITE, PORTFOLIO_ANALYSIS, BENCHMARK
    -- Sites being compared
    primary_site_id UUID NOT NULL REFERENCES customer_sites(id) ON DELETE CASCADE,
    comparison_sites JSONB NOT NULL, -- Array of site IDs
    -- Analysis parameters
    analysis_dimensions JSONB NOT NULL, -- ["schema_complexity", "content_volume", etc.]
    weight_configuration JSONB DEFAULT '{}'::jsonb,
    -- Results
    comparison_results JSONB NOT NULL,
    summary_insights JSONB DEFAULT '{}'::jsonb,
    recommendations JSONB DEFAULT '[]'::jsonb,
    -- Metadata
    confidence_score DECIMAL DEFAULT 0.0,
    analysis_version VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Store portfolio-wide insights for customers with multiple sites
CREATE TABLE IF NOT EXISTS portfolio_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    insight_type VARCHAR(100) NOT NULL, -- CONSOLIDATION_OPPORTUNITY, MIGRATION_READINESS, etc.
    scope VARCHAR(50) NOT NULL, -- ALL_SITES, SITE_CLUSTER, ENVIRONMENT
    -- Analysis scope
    included_sites JSONB NOT NULL, -- Array of site IDs
    analysis_period JSONB NOT NULL, -- {start_date, end_date}
    -- Insights data
    insight_data JSONB NOT NULL,
    key_metrics JSONB DEFAULT '{}'::jsonb,
    recommendations JSONB DEFAULT '[]'::jsonb,
    -- Business impact
    estimated_effort_hours INTEGER,
    estimated_cost_savings DECIMAL,
    priority_score INTEGER DEFAULT 5, -- 1-10 scale
    -- Metadata
    confidence_score DECIMAL DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE -- For time-sensitive insights
);

-- Store benchmarking data for industry/size comparisons
CREATE TABLE IF NOT EXISTS benchmark_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    benchmark_type VARCHAR(100) NOT NULL, -- INDUSTRY, COMPANY_SIZE, TECHNOLOGY_STACK
    benchmark_category VARCHAR(100) NOT NULL, -- E_COMMERCE, MANUFACTURING, etc.
    -- Anonymized aggregated data
    metric_name VARCHAR(255) NOT NULL,
    metric_value DECIMAL NOT NULL,
    sample_size INTEGER NOT NULL,
    percentile_25 DECIMAL,
    percentile_50 DECIMAL,
    percentile_75 DECIMAL,
    percentile_90 DECIMAL,
    -- Context
    data_source VARCHAR(100) DEFAULT 'PLATFORM_AGGREGATE',
    collection_period JSONB NOT NULL, -- {start_date, end_date}
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Constraints
    UNIQUE(benchmark_type, benchmark_category, metric_name, collection_period)
);

-- =============================
-- ENHANCED INDEXES FOR MULTI-SITE
-- =============================

-- Customer and site indexes
CREATE INDEX IF NOT EXISTS idx_customers_code ON customers(customer_code);
CREATE INDEX IF NOT EXISTS idx_customers_active ON customers(is_active, subscription_tier);
CREATE INDEX IF NOT EXISTS idx_customer_sites_customer ON customer_sites(customer_id, is_active);
CREATE INDEX IF NOT EXISTS idx_customer_sites_fqdn ON customer_sites(fqdn);
CREATE INDEX IF NOT EXISTS idx_customer_sites_last_scan ON customer_sites(last_successful_scan);

-- Enhanced scans indexes
CREATE INDEX IF NOT EXISTS idx_scans_v2_customer_site ON scans_v2(customer_id, site_id);
CREATE INDEX IF NOT EXISTS idx_scans_v2_status ON scans_v2(status, started_at);
CREATE INDEX IF NOT EXISTS idx_scans_v2_site_date ON scans_v2(site_id, started_at DESC);

-- Multi-site data indexes
CREATE INDEX IF NOT EXISTS idx_graphql_types_customer_site ON graphql_types(customer_id, site_id);
CREATE INDEX IF NOT EXISTS idx_content_items_customer_site ON content_items(customer_id, site_id);
CREATE INDEX IF NOT EXISTS idx_template_definitions_customer_site ON template_definitions(customer_id, site_id);

-- Cross-site analysis indexes
CREATE INDEX IF NOT EXISTS idx_cross_site_comparisons_customer ON cross_site_comparisons(customer_id, comparison_type);
CREATE INDEX IF NOT EXISTS idx_portfolio_insights_customer ON portfolio_insights(customer_id, insight_type);
CREATE INDEX IF NOT EXISTS idx_benchmark_data_category ON benchmark_data(benchmark_type, benchmark_category);

-- =============================
-- MULTI-SITE REPORTING VIEWS
-- =============================

-- Customer portfolio overview
CREATE OR REPLACE VIEW customer_portfolio AS
SELECT
    c.id as customer_id,
    c.name as customer_name,
    c.customer_code,
    COUNT(cs.id) as total_sites,
    COUNT(CASE WHEN cs.is_active THEN 1 END) as active_sites,
    COUNT(CASE WHEN cs.last_successful_scan IS NOT NULL THEN 1 END) as scanned_sites,
    MAX(cs.last_successful_scan) as latest_scan,
    STRING_AGG(DISTINCT cs.site_type, ', ') as site_types,
    STRING_AGG(DISTINCT cs.environment, ', ') as environments
FROM customers c
LEFT JOIN customer_sites cs ON c.id = cs.customer_id
GROUP BY c.id, c.name, c.customer_code;

-- Site analysis summary with multi-site context
CREATE OR REPLACE VIEW site_analysis_summary AS
SELECT
    cs.id as site_id,
    cs.customer_id,
    c.name as customer_name,
    cs.name as site_name,
    cs.fqdn,
    cs.site_type,
    cs.environment,
    COUNT(s.id) as total_scans,
    MAX(s.started_at) as latest_scan,
    AVG(s.average_confidence) as avg_confidence,
    SUM(s.total_duration_ms) as total_analysis_time,
    -- Cross-site ranking within customer
    ROW_NUMBER() OVER (PARTITION BY cs.customer_id ORDER BY MAX(s.started_at) DESC) as scan_recency_rank,
    ROW_NUMBER() OVER (PARTITION BY cs.customer_id ORDER BY AVG(s.average_confidence) DESC) as quality_rank
FROM customer_sites cs
LEFT JOIN customers c ON cs.customer_id = c.id
LEFT JOIN scans_v2 s ON cs.id = s.site_id
GROUP BY cs.id, cs.customer_id, c.name, cs.name, cs.fqdn, cs.site_type, cs.environment;

-- Cross-site GraphQL schema comparison
CREATE OR REPLACE VIEW cross_site_schema_comparison AS
SELECT
    gt.customer_id,
    c.name as customer_name,
    gt.name as type_name,
    COUNT(DISTINCT gt.site_id) as sites_with_type,
    AVG(gt.field_count) as avg_field_count,
    STRING_AGG(DISTINCT cs.name, ', ') as site_names,
    MAX(gt.created_at) as last_seen
FROM graphql_types gt
JOIN customers c ON gt.customer_id = c.id
JOIN customer_sites cs ON gt.site_id = cs.id
GROUP BY gt.customer_id, c.name, gt.name
HAVING COUNT(DISTINCT gt.site_id) > 1; -- Only show types that appear in multiple sites

-- Customer content portfolio analysis
CREATE OR REPLACE VIEW customer_content_portfolio AS
SELECT
    ci.customer_id,
    c.name as customer_name,
    COUNT(DISTINCT ci.site_id) as sites_with_content,
    COUNT(ci.id) as total_content_items,
    COUNT(DISTINCT ci.template_name) as unique_templates,
    AVG(ci.child_count) as avg_content_depth,
    STRING_AGG(DISTINCT ci.template_name, ', ') as common_templates
FROM content_items ci
JOIN customers c ON ci.customer_id = c.id
GROUP BY ci.customer_id, c.name;

-- =============================
-- MIGRATION FUNCTIONS
-- =============================

-- Function to migrate existing scans to multi-site structure
CREATE OR REPLACE FUNCTION migrate_existing_scans_to_multisite()
RETURNS INTEGER AS $$
DECLARE
    migrated_count INTEGER := 0;
    scan_record RECORD;
    default_customer_id UUID;
    default_site_id UUID;
BEGIN
    -- Create a default customer for existing data
    INSERT INTO customers (name, display_name, customer_code, notes)
    VALUES ('Legacy Data', 'Legacy Analysis Data', 'LEGACY', 'Migrated from single-site system')
    ON CONFLICT (customer_code) DO NOTHING
    RETURNING id INTO default_customer_id;

    -- Get the default customer ID if it already exists
    IF default_customer_id IS NULL THEN
        SELECT id INTO default_customer_id FROM customers WHERE customer_code = 'LEGACY';
    END IF;

    -- Create a default site for existing scans
    INSERT INTO customer_sites (customer_id, name, fqdn, sitecore_url, description)
    VALUES (default_customer_id, 'Legacy Site', 'legacy.example.com', 'https://legacy.example.com', 'Migrated from single-site analysis')
    ON CONFLICT (customer_id, fqdn) DO NOTHING
    RETURNING id INTO default_site_id;

    -- Get the default site ID if it already exists
    IF default_site_id IS NULL THEN
        SELECT id INTO default_site_id
        FROM customer_sites
        WHERE customer_id = default_customer_id AND fqdn = 'legacy.example.com';
    END IF;

    -- Update existing data tables with customer and site IDs
    UPDATE graphql_types SET customer_id = default_customer_id, site_id = default_site_id
    WHERE customer_id IS NULL;

    UPDATE content_items SET customer_id = default_customer_id, site_id = default_site_id
    WHERE customer_id IS NULL;

    UPDATE template_definitions SET customer_id = default_customer_id, site_id = default_site_id
    WHERE customer_id IS NULL;

    UPDATE field_usage_statistics SET customer_id = default_customer_id, site_id = default_site_id
    WHERE customer_id IS NULL;

    GET DIAGNOSTICS migrated_count = ROW_COUNT;

    RETURN migrated_count;
END;
$$ LANGUAGE plpgsql;

-- =============================
-- COMMENTS FOR PHASE 2 DEVELOPMENT
-- =============================

-- MULTI-SITE ARCHITECTURE BENEFITS:
-- 1. Customer Isolation: Complete data separation between customers
-- 2. Portfolio Analysis: Compare sites within a customer organization
-- 3. Benchmarking: Anonymous cross-customer insights
-- 4. Scalability: Support for enterprise customers with many sites
-- 5. Business Intelligence: Customer success and churn analysis

-- PHASE 2 DEVELOPMENT IMPLICATIONS:
-- 1. All queries must include customer_id/site_id for data isolation
-- 2. UI needs customer/site selection components
-- 3. Reporting can offer single-site, customer-wide, or benchmark views
-- 4. API design should be customer-scoped by default
-- 5. Multi-tenancy security must be enforced at application level

-- RECOMMENDED QUERY PATTERNS:
-- Single Site: WHERE site_id = ?
-- Customer Portfolio: WHERE customer_id = ?
-- Cross-Customer Benchmark: Aggregate with anonymization
-- Site Comparison: WHERE customer_id = ? AND site_id IN (...)

-- FUTURE ENHANCEMENTS:
-- 1. Customer billing based on site count and analysis frequency
-- 2. White-label deployment for large customers
-- 3. Real-time sync between related sites
-- 4. Automated migration recommendations across customer portfolio
-- 5. AI-powered insights based on portfolio patterns