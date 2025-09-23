-- =====================================================
-- SMART SITECORE ANALYSIS PLATFORM - ENHANCED SCHEMA
-- =====================================================
-- Normalized database structure for efficient querying
-- and Node.js/React reporting interfaces
--
-- Version: Phase 1.5 Enhancement
-- Created: 2025-01-22
-- Purpose: Transform JSON blobs into queryable structures
-- =====================================================

-- =============================
-- GRAPHQL SCHEMA TABLES
-- =============================

-- Store individual GraphQL types with full metadata
CREATE TABLE IF NOT EXISTS graphql_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    kind VARCHAR(50) NOT NULL, -- OBJECT, ENUM, INTERFACE, UNION, SCALAR
    description TEXT,
    is_deprecated BOOLEAN DEFAULT FALSE,
    deprecation_reason TEXT,
    -- Metadata for analysis
    field_count INTEGER DEFAULT 0,
    interface_count INTEGER DEFAULT 0,
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Composite unique constraint
    UNIQUE(scan_id, name)
);

-- Store individual GraphQL field definitions with rich metadata
CREATE TABLE IF NOT EXISTS graphql_fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type_id UUID NOT NULL REFERENCES graphql_types(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    field_type VARCHAR(255) NOT NULL, -- GraphQL type (String!, [Item], etc.)
    description TEXT,
    is_deprecated BOOLEAN DEFAULT FALSE,
    deprecation_reason TEXT,
    -- Field characteristics
    is_list BOOLEAN DEFAULT FALSE,
    is_non_null BOOLEAN DEFAULT FALSE,
    is_scalar BOOLEAN DEFAULT FALSE,
    -- Arguments and type details (keep as JSONB for flexibility)
    arguments JSONB DEFAULT '[]'::jsonb,
    type_detail JSONB DEFAULT '{}'::jsonb,
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Composite unique constraint
    UNIQUE(type_id, name)
);

-- Store GraphQL interfaces implemented by types
CREATE TABLE IF NOT EXISTS graphql_interfaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type_id UUID NOT NULL REFERENCES graphql_types(id) ON DELETE CASCADE,
    interface_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(type_id, interface_name)
);

-- Store type relationships for inheritance analysis
CREATE TABLE IF NOT EXISTS graphql_type_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    source_type VARCHAR(255) NOT NULL,
    target_type VARCHAR(255) NOT NULL,
    relationship_type VARCHAR(50) NOT NULL, -- IMPLEMENTS, REFERENCES, CONTAINS
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(scan_id, source_type, target_type, relationship_type)
);

-- =============================
-- CONTENT STRUCTURE TABLES
-- =============================

-- Store individual content items with metadata
CREATE TABLE IF NOT EXISTS content_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    sitecore_id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    path TEXT NOT NULL,
    display_name VARCHAR(255),
    template_name VARCHAR(255),
    template_id VARCHAR(255),
    -- Content characteristics
    has_children BOOLEAN DEFAULT FALSE,
    child_count INTEGER DEFAULT 0,
    depth_level INTEGER DEFAULT 0,
    -- Content status
    is_published BOOLEAN DEFAULT TRUE,
    language VARCHAR(10) DEFAULT 'en',
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Constraints
    UNIQUE(scan_id, sitecore_id)
);

-- Store field values for comprehensive content analysis
CREATE TABLE IF NOT EXISTS content_field_values (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID NOT NULL REFERENCES content_items(id) ON DELETE CASCADE,
    field_name VARCHAR(255) NOT NULL,
    field_value TEXT,
    -- Value analysis
    value_type VARCHAR(50) NOT NULL, -- Text, HTML/XML, Numeric, Boolean, etc.
    value_length INTEGER DEFAULT 0,
    has_value BOOLEAN DEFAULT FALSE,
    is_empty BOOLEAN DEFAULT TRUE,
    -- Content insights
    word_count INTEGER DEFAULT 0,
    contains_html BOOLEAN DEFAULT FALSE,
    contains_links BOOLEAN DEFAULT FALSE,
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Constraints
    UNIQUE(item_id, field_name)
);

-- =============================
-- TEMPLATE DEFINITION TABLES
-- =============================

-- Store Sitecore template definitions
CREATE TABLE IF NOT EXISTS template_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    template_id VARCHAR(255) NOT NULL,
    template_name VARCHAR(255) NOT NULL,
    template_path TEXT,
    -- Template metadata
    is_system_template BOOLEAN DEFAULT FALSE,
    usage_count INTEGER DEFAULT 0,
    -- Inheritance
    base_templates JSONB DEFAULT '[]'::jsonb,
    inheritance_chain JSONB DEFAULT '[]'::jsonb,
    -- Statistics
    field_count INTEGER DEFAULT 0,
    section_count INTEGER DEFAULT 0,
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Constraints
    UNIQUE(scan_id, template_id)
);

-- Store template field definitions with rich metadata
CREATE TABLE IF NOT EXISTS template_fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL REFERENCES template_definitions(id) ON DELETE CASCADE,
    field_name VARCHAR(255) NOT NULL,
    field_type VARCHAR(255),
    field_id VARCHAR(255),
    -- Field characteristics
    is_required BOOLEAN DEFAULT FALSE,
    is_shared BOOLEAN DEFAULT FALSE,
    is_unversioned BOOLEAN DEFAULT FALSE,
    max_length INTEGER,
    -- Organization
    section_name VARCHAR(255),
    sort_order INTEGER DEFAULT 0,
    -- Validation and defaults
    validation_regex TEXT,
    default_value TEXT,
    help_text TEXT,
    -- Usage statistics
    usage_count INTEGER DEFAULT 0,
    avg_content_length DECIMAL,
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Constraints
    UNIQUE(template_id, field_name)
);

-- Store template inheritance relationships
CREATE TABLE IF NOT EXISTS template_inheritance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    child_template_id UUID NOT NULL REFERENCES template_definitions(id) ON DELETE CASCADE,
    parent_template_id UUID NOT NULL REFERENCES template_definitions(id) ON DELETE CASCADE,
    inheritance_level INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(child_template_id, parent_template_id)
);

-- =============================
-- ANALYSIS METADATA TABLES
-- =============================

-- Store field usage statistics across the entire scan
CREATE TABLE IF NOT EXISTS field_usage_statistics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    field_name VARCHAR(255) NOT NULL,
    -- Usage metrics
    total_occurrences INTEGER DEFAULT 0,
    templates_using_field INTEGER DEFAULT 0,
    items_with_values INTEGER DEFAULT 0,
    items_empty INTEGER DEFAULT 0,
    -- Content analysis
    avg_content_length DECIMAL,
    max_content_length INTEGER,
    common_value_types JSONB DEFAULT '[]'::jsonb,
    -- Performance insights
    query_frequency INTEGER DEFAULT 0,
    last_analyzed TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Constraints
    UNIQUE(scan_id, field_name)
);

-- Store content model insights for reporting
CREATE TABLE IF NOT EXISTS content_model_insights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    insight_type VARCHAR(100) NOT NULL, -- template_usage, field_coverage, etc.
    insight_data JSONB NOT NULL,
    confidence_score DECIMAL DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =============================
-- PERFORMANCE INDEXES
-- =============================

-- GraphQL schema indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_graphql_types_scan_kind ON graphql_types(scan_id, kind);
CREATE INDEX IF NOT EXISTS idx_graphql_types_name ON graphql_types(name);
CREATE INDEX IF NOT EXISTS idx_graphql_fields_type_name ON graphql_fields(type_id, name);
CREATE INDEX IF NOT EXISTS idx_graphql_fields_field_type ON graphql_fields(field_type);

-- Content structure indexes for reporting queries
CREATE INDEX IF NOT EXISTS idx_content_items_scan_template ON content_items(scan_id, template_name);
CREATE INDEX IF NOT EXISTS idx_content_items_path ON content_items(path);
CREATE INDEX IF NOT EXISTS idx_content_items_template_id ON content_items(template_id);
CREATE INDEX IF NOT EXISTS idx_content_field_values_item_field ON content_field_values(item_id, field_name);
CREATE INDEX IF NOT EXISTS idx_content_field_values_field_type ON content_field_values(field_name, value_type);
CREATE INDEX IF NOT EXISTS idx_content_field_values_has_value ON content_field_values(has_value, field_name);

-- Template definition indexes for inheritance queries
CREATE INDEX IF NOT EXISTS idx_template_definitions_scan_name ON template_definitions(scan_id, template_name);
CREATE INDEX IF NOT EXISTS idx_template_definitions_usage ON template_definitions(usage_count DESC);
CREATE INDEX IF NOT EXISTS idx_template_fields_template_name ON template_fields(template_id, field_name);
CREATE INDEX IF NOT EXISTS idx_template_fields_field_type ON template_fields(field_type);
CREATE INDEX IF NOT EXISTS idx_template_inheritance_child ON template_inheritance(child_template_id);
CREATE INDEX IF NOT EXISTS idx_template_inheritance_parent ON template_inheritance(parent_template_id);

-- Analysis indexes for fast reporting
CREATE INDEX IF NOT EXISTS idx_field_usage_scan_occurrences ON field_usage_statistics(scan_id, total_occurrences DESC);
CREATE INDEX IF NOT EXISTS idx_field_usage_field_name ON field_usage_statistics(field_name);

-- =============================
-- REPORTING VIEWS FOR NODE.JS
-- =============================

-- Comprehensive template analysis view
CREATE OR REPLACE VIEW template_analysis AS
SELECT
    td.id,
    td.scan_id,
    td.template_name,
    td.template_id,
    td.usage_count,
    td.field_count,
    td.is_system_template,
    COUNT(ci.id) as active_content_items,
    COUNT(DISTINCT tf.field_name) as defined_fields,
    AVG(cfv.value_length) as avg_field_content_length
FROM template_definitions td
LEFT JOIN content_items ci ON td.template_id = ci.template_id
LEFT JOIN template_fields tf ON td.id = tf.template_id
LEFT JOIN content_field_values cfv ON ci.id = cfv.item_id
GROUP BY td.id, td.scan_id, td.template_name, td.template_id,
         td.usage_count, td.field_count, td.is_system_template;

-- Field usage across templates view
CREATE OR REPLACE VIEW field_usage_analysis AS
SELECT
    fus.scan_id,
    fus.field_name,
    fus.total_occurrences,
    fus.templates_using_field,
    fus.items_with_values,
    fus.avg_content_length,
    COUNT(DISTINCT tf.template_id) as template_definitions_count,
    COUNT(DISTINCT cfv.value_type) as value_types_count,
    STRING_AGG(DISTINCT td.template_name, ', ' ORDER BY td.template_name) as templates_list
FROM field_usage_statistics fus
LEFT JOIN template_fields tf ON fus.field_name = tf.field_name
LEFT JOIN template_definitions td ON tf.template_id = td.id AND td.scan_id = fus.scan_id
LEFT JOIN content_field_values cfv ON cfv.field_name = fus.field_name
GROUP BY fus.scan_id, fus.field_name, fus.total_occurrences,
         fus.templates_using_field, fus.items_with_values, fus.avg_content_length;

-- Content hierarchy view for tree visualization
CREATE OR REPLACE VIEW content_hierarchy AS
SELECT
    ci.id,
    ci.scan_id,
    ci.name,
    ci.path,
    ci.template_name,
    ci.has_children,
    ci.child_count,
    ci.depth_level,
    COUNT(cfv.id) as field_count,
    COUNT(CASE WHEN cfv.has_value THEN 1 END) as populated_fields,
    td.is_system_template
FROM content_items ci
LEFT JOIN content_field_values cfv ON ci.id = cfv.item_id
LEFT JOIN template_definitions td ON ci.template_id = td.template_id AND ci.scan_id = td.scan_id
GROUP BY ci.id, ci.scan_id, ci.name, ci.path, ci.template_name,
         ci.has_children, ci.child_count, ci.depth_level, td.is_system_template;

-- =============================
-- COMMENTS FOR FUTURE DEVELOPMENT
-- =============================

-- NOTES FOR NODE.JS/REACT INTEGRATION:
-- 1. All tables use UUID primary keys for REST API efficiency
-- 2. Foreign key relationships maintain data integrity
-- 3. JSONB columns for complex data that doesn't need normalization
-- 4. Indexes optimized for common reporting queries
-- 5. Views provide pre-aggregated data for dashboards
-- 6. Timestamp columns for caching and incremental updates
-- 7. Unique constraints prevent duplicate data

-- RECOMMENDED ORM USAGE:
-- - Prisma: Excellent TypeScript integration, auto-generates types
-- - Sequelize: Mature ORM with good PostgreSQL support
-- - TypeORM: Decorator-based, works well with NestJS

-- FUTURE ENHANCEMENTS:
-- - Add audit trails for content changes
-- - Implement soft deletes for historical analysis
-- - Add materialized views for complex aggregations
-- - Consider partitioning for large datasets