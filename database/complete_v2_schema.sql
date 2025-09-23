-- =====================================================================
-- SMART SITECORE ANALYSIS PLATFORM - V2.0 COMPLETE SCHEMA
-- =====================================================================
-- This script completely recreates the v2.0 multi-site architecture
-- WARNING: This will DROP ALL existing data and recreate tables
-- =====================================================================

-- Drop existing tables in dependency order (safeguards against foreign key constraints)
DROP TABLE IF EXISTS cross_site_comparisons CASCADE;
DROP TABLE IF EXISTS portfolio_insights CASCADE;
DROP TABLE IF EXISTS benchmark_data CASCADE;
DROP TABLE IF EXISTS site_relationships CASCADE;
DROP TABLE IF EXISTS scans_v2 CASCADE;
DROP TABLE IF EXISTS customer_sites CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

-- Drop any remaining legacy tables
DROP TABLE IF EXISTS sites CASCADE;
DROP TABLE IF EXISTS scans CASCADE;
DROP TABLE IF EXISTS graphql_types CASCADE;
DROP TABLE IF EXISTS content_items CASCADE;
DROP TABLE IF EXISTS analysis_results CASCADE;
DROP TABLE IF EXISTS template_definitions CASCADE;
DROP TABLE IF EXISTS scan_results CASCADE;
DROP TABLE IF EXISTS scan_modules CASCADE;

-- =====================================================================
-- CORE V2.0 MULTI-SITE TABLES
-- =====================================================================

-- customers: Multi-tenant customer management
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    customer_code VARCHAR(50) UNIQUE,
    domain VARCHAR(255),
    industry VARCHAR(100),
    company_size VARCHAR(50),
    region VARCHAR(100),
    primary_contact_name VARCHAR(255),
    primary_contact_email VARCHAR(255),
    subscription_tier VARCHAR(50) DEFAULT 'standard',
    analysis_frequency VARCHAR(50) DEFAULT 'monthly',
    retention_period INTEGER DEFAULT 365,
    api_key_hash VARCHAR(255),
    access_restrictions JSONB DEFAULT '{}',
    notes TEXT,
    tags VARCHAR[] DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'active',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_analysis_at TIMESTAMPTZ,

    CONSTRAINT customers_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT customers_valid_status CHECK (status IN ('active', 'inactive', 'suspended', 'trial')),
    CONSTRAINT customers_valid_company_size CHECK (company_size IN ('startup', 'small', 'medium', 'large', 'enterprise') OR company_size IS NULL)
);

-- customer_sites: Multi-site management per customer
CREATE TABLE customer_sites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    display_name VARCHAR(255),
    url VARCHAR(500),
    sitecore_url VARCHAR(500) NOT NULL,
    environment VARCHAR(50) DEFAULT 'production',
    version VARCHAR(50),
    technology_stack JSONB DEFAULT '{}',
    configuration JSONB DEFAULT '{}',
    access_credentials JSONB DEFAULT '{}',
    last_scan_at TIMESTAMPTZ,
    next_scan_at TIMESTAMPTZ,
    scan_frequency VARCHAR(50) DEFAULT 'weekly',
    priority INTEGER DEFAULT 1,
    tags VARCHAR[] DEFAULT '{}',
    notes TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT customer_sites_name_not_empty CHECK (length(trim(name)) > 0),
    CONSTRAINT customer_sites_valid_status CHECK (status IN ('active', 'inactive', 'maintenance', 'archived')),
    CONSTRAINT customer_sites_valid_environment CHECK (environment IN ('development', 'staging', 'production', 'qa')),
    CONSTRAINT customer_sites_valid_priority CHECK (priority BETWEEN 1 AND 10),
    CONSTRAINT unique_customer_site_name UNIQUE(customer_id, name)
);

-- scans_v2: Enhanced scan tracking with comprehensive metrics
CREATE TABLE scans_v2 (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    site_id UUID NOT NULL REFERENCES customer_sites(id) ON DELETE CASCADE,
    scan_type VARCHAR(100) NOT NULL DEFAULT 'full_extraction',
    scan_version VARCHAR(20) DEFAULT '2.0',
    trigger_type VARCHAR(50) DEFAULT 'manual',
    triggered_by VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending',
    progress_percentage INTEGER DEFAULT 0,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER,

    -- Extraction metrics
    modules_attempted INTEGER DEFAULT 0,
    modules_successful INTEGER DEFAULT 0,
    modules_failed INTEGER DEFAULT 0,
    items_extracted INTEGER DEFAULT 0,
    api_calls_made INTEGER DEFAULT 0,
    endpoints_accessed TEXT[] DEFAULT '{}',

    -- Data storage
    metadata JSONB DEFAULT '{}',
    results JSONB DEFAULT '{}',
    errors JSONB DEFAULT '{}',
    error_message TEXT,

    -- Quality metrics
    data_quality_score DECIMAL(5,2),
    completeness_percentage INTEGER,
    confidence_score DECIMAL(5,2),

    -- Environment info
    extraction_environment JSONB DEFAULT '{}',
    system_info JSONB DEFAULT '{}',

    CONSTRAINT scans_v2_valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled', 'partial')),
    CONSTRAINT scans_v2_valid_progress CHECK (progress_percentage BETWEEN 0 AND 100),
    CONSTRAINT scans_v2_valid_scores CHECK (
        (data_quality_score IS NULL OR data_quality_score BETWEEN 0 AND 100) AND
        (confidence_score IS NULL OR confidence_score BETWEEN 0 AND 100) AND
        (completeness_percentage IS NULL OR completeness_percentage BETWEEN 0 AND 100)
    )
);

-- =====================================================================
-- ADVANCED ANALYTICS TABLES
-- =====================================================================

-- site_relationships: Cross-site relationship mapping
CREATE TABLE site_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    primary_site_id UUID NOT NULL REFERENCES customer_sites(id) ON DELETE CASCADE,
    related_site_id UUID NOT NULL REFERENCES customer_sites(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL,
    strength DECIMAL(3,2) DEFAULT 1.0,
    confidence DECIMAL(3,2) DEFAULT 1.0,
    metadata JSONB DEFAULT '{}',
    detected_at TIMESTAMPTZ DEFAULT NOW(),
    last_verified_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT site_relationships_no_self_reference CHECK (primary_site_id != related_site_id),
    CONSTRAINT site_relationships_valid_strength CHECK (strength BETWEEN 0 AND 1),
    CONSTRAINT site_relationships_valid_confidence CHECK (confidence BETWEEN 0 AND 1),
    CONSTRAINT site_relationships_valid_type CHECK (relationship_type IN (
        'parent_child', 'sibling', 'clone', 'template_shared', 'content_shared',
        'technology_similar', 'performance_similar', 'architectural_similar'
    )),
    CONSTRAINT unique_site_relationship UNIQUE(primary_site_id, related_site_id, relationship_type)
);

-- cross_site_comparisons: Detailed cross-site analysis results
CREATE TABLE cross_site_comparisons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES scans_v2(id) ON DELETE CASCADE,
    comparison_type VARCHAR(100) NOT NULL,
    site_a_id UUID NOT NULL REFERENCES customer_sites(id) ON DELETE CASCADE,
    site_b_id UUID NOT NULL REFERENCES customer_sites(id) ON DELETE CASCADE,
    comparison_category VARCHAR(100),

    -- Comparison metrics
    similarity_score DECIMAL(5,2),
    difference_score DECIMAL(5,2),
    performance_delta DECIMAL(10,4),
    complexity_delta INTEGER,

    -- Detailed metrics
    metrics JSONB NOT NULL DEFAULT '{}',
    differences JSONB DEFAULT '{}',
    recommendations JSONB DEFAULT '{}',

    -- Metadata
    algorithm_version VARCHAR(20) DEFAULT '1.0',
    confidence_level DECIMAL(3,2) DEFAULT 1.0,
    processing_time_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT cross_site_comparisons_no_self_comparison CHECK (site_a_id != site_b_id),
    CONSTRAINT cross_site_comparisons_valid_scores CHECK (
        (similarity_score IS NULL OR similarity_score BETWEEN 0 AND 100) AND
        (difference_score IS NULL OR difference_score BETWEEN 0 AND 100) AND
        (confidence_level IS NULL OR confidence_level BETWEEN 0 AND 1)
    ),
    CONSTRAINT cross_site_comparisons_valid_type CHECK (comparison_type IN (
        'performance', 'seo', 'accessibility', 'security', 'content_quality',
        'technical_architecture', 'user_experience', 'modernization_readiness'
    ))
);

-- portfolio_insights: Customer portfolio analytics and insights
CREATE TABLE portfolio_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    insight_type VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    priority VARCHAR(20) DEFAULT 'medium',

    -- Insight data
    title VARCHAR(255) NOT NULL,
    description TEXT,
    data JSONB NOT NULL DEFAULT '{}',
    metrics JSONB DEFAULT '{}',
    recommendations JSONB DEFAULT '{}',

    -- Scoring and validation
    impact_score DECIMAL(5,2),
    confidence_score DECIMAL(3,2) DEFAULT 1.0,
    effort_estimate VARCHAR(50),
    business_value VARCHAR(50),

    -- Lifecycle
    generated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    last_updated_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active',

    -- Categorization
    tags VARCHAR[] DEFAULT '{}',
    affected_sites UUID[] DEFAULT '{}',

    -- Tracking
    view_count INTEGER DEFAULT 0,
    action_taken BOOLEAN DEFAULT false,
    action_taken_at TIMESTAMPTZ,

    CONSTRAINT portfolio_insights_valid_priority CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT portfolio_insights_valid_status CHECK (status IN ('active', 'acknowledged', 'resolved', 'dismissed')),
    CONSTRAINT portfolio_insights_valid_scores CHECK (
        (impact_score IS NULL OR impact_score BETWEEN 0 AND 100) AND
        (confidence_score IS NULL OR confidence_score BETWEEN 0 AND 1)
    ),
    CONSTRAINT portfolio_insights_title_not_empty CHECK (length(trim(title)) > 0)
);

-- benchmark_data: Industry and comparative benchmarking data
CREATE TABLE benchmark_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Segmentation
    industry VARCHAR(100),
    company_size VARCHAR(50),
    region VARCHAR(100),
    technology_stack VARCHAR(100),

    -- Metric definition
    metric_category VARCHAR(100) NOT NULL,
    metric_name VARCHAR(150) NOT NULL,
    metric_description TEXT,
    metric_unit VARCHAR(50),

    -- Statistical data
    value DECIMAL(15,4) NOT NULL,
    percentile DECIMAL(5,2),
    quartile INTEGER,
    sample_size INTEGER,
    standard_deviation DECIMAL(15,4),
    min_value DECIMAL(15,4),
    max_value DECIMAL(15,4),
    median_value DECIMAL(15,4),

    -- Data quality
    data_quality_score DECIMAL(3,2) DEFAULT 1.0,
    confidence_interval DECIMAL(5,2),
    margin_of_error DECIMAL(5,2),

    -- Source and versioning
    source VARCHAR(100) DEFAULT 'internal',
    source_detail TEXT,
    collection_method VARCHAR(100),
    data_version VARCHAR(20) DEFAULT '1.0',

    -- Timestamps
    measurement_date DATE,
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,

    CONSTRAINT benchmark_data_valid_percentile CHECK (percentile IS NULL OR percentile BETWEEN 0 AND 100),
    CONSTRAINT benchmark_data_valid_quartile CHECK (quartile IS NULL OR quartile BETWEEN 1 AND 4),
    CONSTRAINT benchmark_data_valid_quality CHECK (data_quality_score BETWEEN 0 AND 1),
    CONSTRAINT benchmark_data_valid_company_size CHECK (company_size IN ('startup', 'small', 'medium', 'large', 'enterprise') OR company_size IS NULL),
    CONSTRAINT unique_benchmark_metric UNIQUE(industry, company_size, region, metric_category, metric_name, measurement_date)
);

-- =====================================================================
-- PERFORMANCE INDEXES
-- =====================================================================

-- Customer indexes
CREATE INDEX idx_customers_status ON customers(status);
CREATE INDEX idx_customers_industry ON customers(industry);
CREATE INDEX idx_customers_company_size ON customers(company_size);
CREATE INDEX idx_customers_region ON customers(region);
CREATE INDEX idx_customers_subscription_tier ON customers(subscription_tier);
CREATE INDEX idx_customers_created_at ON customers(created_at);

-- Customer sites indexes
CREATE INDEX idx_customer_sites_customer_id ON customer_sites(customer_id);
CREATE INDEX idx_customer_sites_status ON customer_sites(status);
CREATE INDEX idx_customer_sites_environment ON customer_sites(environment);
CREATE INDEX idx_customer_sites_last_scan ON customer_sites(last_scan_at);
CREATE INDEX idx_customer_sites_priority ON customer_sites(priority);

-- Scans indexes
CREATE INDEX idx_scans_v2_customer_id ON scans_v2(customer_id);
CREATE INDEX idx_scans_v2_site_id ON scans_v2(site_id);
CREATE INDEX idx_scans_v2_customer_site ON scans_v2(customer_id, site_id);
CREATE INDEX idx_scans_v2_status ON scans_v2(status);
CREATE INDEX idx_scans_v2_scan_type ON scans_v2(scan_type);
CREATE INDEX idx_scans_v2_started_at ON scans_v2(started_at);
CREATE INDEX idx_scans_v2_completed_at ON scans_v2(completed_at);

-- Analytics indexes
CREATE INDEX idx_site_relationships_primary ON site_relationships(primary_site_id);
CREATE INDEX idx_site_relationships_related ON site_relationships(related_site_id);
CREATE INDEX idx_site_relationships_type ON site_relationships(relationship_type);

CREATE INDEX idx_cross_site_comparisons_scan ON cross_site_comparisons(scan_id);
CREATE INDEX idx_cross_site_comparisons_sites ON cross_site_comparisons(site_a_id, site_b_id);
CREATE INDEX idx_cross_site_comparisons_type ON cross_site_comparisons(comparison_type);

CREATE INDEX idx_portfolio_insights_customer ON portfolio_insights(customer_id);
CREATE INDEX idx_portfolio_insights_type ON portfolio_insights(insight_type);
CREATE INDEX idx_portfolio_insights_priority ON portfolio_insights(priority);
CREATE INDEX idx_portfolio_insights_status ON portfolio_insights(status);
CREATE INDEX idx_portfolio_insights_generated ON portfolio_insights(generated_at);

CREATE INDEX idx_benchmark_data_lookup ON benchmark_data(industry, company_size, region);
CREATE INDEX idx_benchmark_data_metric ON benchmark_data(metric_category, metric_name);
CREATE INDEX idx_benchmark_data_percentile ON benchmark_data(percentile);
CREATE INDEX idx_benchmark_data_measurement_date ON benchmark_data(measurement_date);

-- =====================================================================
-- USEFUL VIEWS FOR ANALYTICS
-- =====================================================================

-- Active customer portfolio overview
CREATE VIEW customer_portfolio_overview AS
SELECT
    c.id,
    c.name,
    c.industry,
    c.company_size,
    c.subscription_tier,
    COUNT(cs.id) as total_sites,
    COUNT(CASE WHEN cs.status = 'active' THEN 1 END) as active_sites,
    MAX(s.completed_at) as last_scan_completed,
    COUNT(s.id) as total_scans,
    AVG(s.data_quality_score) as avg_data_quality
FROM customers c
LEFT JOIN customer_sites cs ON c.id = cs.customer_id
LEFT JOIN scans_v2 s ON cs.id = s.site_id AND s.status = 'completed'
WHERE c.status = 'active'
GROUP BY c.id, c.name, c.industry, c.company_size, c.subscription_tier;

-- Recent scan performance metrics
CREATE VIEW recent_scan_performance AS
SELECT
    s.id,
    c.name as customer_name,
    cs.name as site_name,
    s.scan_type,
    s.status,
    s.started_at,
    s.completed_at,
    s.duration_seconds,
    s.modules_successful,
    s.modules_failed,
    s.items_extracted,
    s.api_calls_made,
    s.data_quality_score
FROM scans_v2 s
JOIN customer_sites cs ON s.site_id = cs.id
JOIN customers c ON s.customer_id = c.id
WHERE s.started_at >= NOW() - INTERVAL '30 days'
ORDER BY s.started_at DESC;

-- =====================================================================
-- SECURITY & PERMISSIONS
-- =====================================================================

-- Enable Row Level Security on sensitive tables
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer_sites ENABLE ROW LEVEL SECURITY;
ALTER TABLE scans_v2 ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolio_insights ENABLE ROW LEVEL SECURITY;

-- =====================================================================
-- DATA VALIDATION FUNCTIONS
-- =====================================================================

-- Function to validate scan completeness
CREATE OR REPLACE FUNCTION validate_scan_completeness(scan_uuid UUID)
RETURNS JSONB AS $$
DECLARE
    scan_record scans_v2%ROWTYPE;
    validation_result JSONB;
BEGIN
    SELECT * INTO scan_record FROM scans_v2 WHERE id = scan_uuid;

    IF NOT FOUND THEN
        RETURN jsonb_build_object('valid', false, 'error', 'Scan not found');
    END IF;

    validation_result := jsonb_build_object(
        'valid', true,
        'has_results', scan_record.results IS NOT NULL AND scan_record.results != '{}'::jsonb,
        'has_metadata', scan_record.metadata IS NOT NULL AND scan_record.metadata != '{}'::jsonb,
        'duration_reasonable', scan_record.duration_seconds IS NOT NULL AND scan_record.duration_seconds > 0,
        'items_extracted', scan_record.items_extracted,
        'quality_score', scan_record.data_quality_score
    );

    RETURN validation_result;
END;
$$ LANGUAGE plpgsql;

-- =====================================================================
-- INITIAL DATA SETUP
-- =====================================================================

-- Create default benchmark categories
INSERT INTO benchmark_data (metric_category, metric_name, metric_description, value, industry, company_size, region, source) VALUES
('performance', 'page_load_time', 'Average page load time in seconds', 3.2, 'general', 'medium', 'north_america', 'industry_standard'),
('performance', 'first_contentful_paint', 'First Contentful Paint in seconds', 1.8, 'general', 'medium', 'north_america', 'industry_standard'),
('seo', 'lighthouse_seo_score', 'Lighthouse SEO score out of 100', 85.0, 'general', 'medium', 'north_america', 'industry_standard'),
('accessibility', 'lighthouse_accessibility_score', 'Lighthouse Accessibility score out of 100', 78.0, 'general', 'medium', 'north_america', 'industry_standard'),
('modernization', 'technology_freshness_score', 'Technology stack modernization score', 72.0, 'general', 'medium', 'north_america', 'industry_standard')
ON CONFLICT (industry, company_size, region, metric_category, metric_name, measurement_date) DO NOTHING;

-- =====================================================================
-- SCHEMA VALIDATION
-- =====================================================================

-- Verify all tables exist
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name IN ('customers', 'customer_sites', 'scans_v2', 'site_relationships', 'cross_site_comparisons', 'portfolio_insights', 'benchmark_data');

    IF table_count = 7 THEN
        RAISE NOTICE 'SUCCESS: All 7 V2.0 tables created successfully';
    ELSE
        RAISE EXCEPTION 'ERROR: Only % out of 7 tables were created', table_count;
    END IF;
END $$;

-- =====================================================================
-- COMPLETION MESSAGE
-- =====================================================================

SELECT
    'V2.0 MULTI-SITE SCHEMA CREATED SUCCESSFULLY' as status,
    NOW() as completed_at,
    (SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public') as total_tables,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_schema = 'public') as total_columns,
    (SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public') as total_indexes;