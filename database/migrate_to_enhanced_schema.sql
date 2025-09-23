-- =====================================================
-- MIGRATION TO ENHANCED SCHEMA
-- =====================================================
-- Execute this script to upgrade from basic JSON storage
-- to the enhanced normalized structure
--
-- IMPORTANT: This preserves existing data while adding
-- new normalized tables alongside current structure
-- =====================================================

-- Check if we're connected to the right database
DO $$
BEGIN
    RAISE NOTICE 'Starting migration to enhanced schema at %', NOW();
    RAISE NOTICE 'Current database: %', current_database();
END $$;

-- =============================
-- PRE-MIGRATION CHECKS
-- =============================

-- Verify existing tables exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'scans') THEN
        RAISE EXCEPTION 'Base table "scans" does not exist. Please run base schema first.';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'scan_modules') THEN
        RAISE EXCEPTION 'Base table "scan_modules" does not exist. Please run base schema first.';
    END IF;

    RAISE NOTICE 'Base tables verified successfully';
END $$;

-- =============================
-- EXECUTE ENHANCED SCHEMA
-- =============================

-- Import the enhanced schema
\i enhanced_schema.sql

-- =============================
-- DATA MIGRATION FUNCTIONS
-- =============================

-- Function to migrate GraphQL schema data from JSON to normalized tables
CREATE OR REPLACE FUNCTION migrate_graphql_schema_data()
RETURNS INTEGER AS $$
DECLARE
    scan_record RECORD;
    module_record RECORD;
    schema_data JSONB;
    type_data JSONB;
    field_data JSONB;
    type_id UUID;
    migrated_count INTEGER := 0;
BEGIN
    -- Loop through all scans with enhanced GraphQL schema data
    FOR scan_record IN
        SELECT DISTINCT s.id as scan_id
        FROM scans s
        JOIN scan_modules sm ON s.id = sm.scan_id
        WHERE sm.module = 'enhanced-sitecore-schema'
        AND sm.error IS NULL
    LOOP
        RAISE NOTICE 'Migrating GraphQL schema data for scan: %', scan_record.scan_id;

        -- Get the enhanced schema data
        SELECT ar.result INTO schema_data
        FROM scan_modules sm
        JOIN analysis_results ar ON sm.id = ar.scan_module_id
        WHERE sm.scan_id = scan_record.scan_id
        AND sm.module = 'enhanced-sitecore-schema'
        LIMIT 1;

        -- Skip if no data found
        IF schema_data IS NULL THEN
            CONTINUE;
        END IF;

        -- Migrate object types
        FOR type_data IN SELECT * FROM jsonb_array_elements(schema_data->'object_types')
        LOOP
            -- Insert GraphQL type
            INSERT INTO graphql_types (scan_id, name, kind, description, field_count)
            VALUES (
                scan_record.scan_id,
                type_data->>'name',
                'OBJECT',
                type_data->>'description',
                COALESCE((type_data->>'field_count')::INTEGER, 0)
            )
            ON CONFLICT (scan_id, name) DO UPDATE SET
                description = EXCLUDED.description,
                field_count = EXCLUDED.field_count
            RETURNING id INTO type_id;

            -- Migrate fields for this type
            FOR field_data IN SELECT * FROM jsonb_array_elements(type_data->'fields')
            LOOP
                INSERT INTO graphql_fields (type_id, name, field_type, description, is_deprecated, arguments, type_detail)
                VALUES (
                    type_id,
                    field_data->>'name',
                    field_data->>'type',
                    field_data->>'description',
                    COALESCE((field_data->>'is_deprecated')::BOOLEAN, FALSE),
                    COALESCE(field_data->'args', '[]'::jsonb),
                    COALESCE(field_data->'type_detail', '{}'::jsonb)
                )
                ON CONFLICT (type_id, name) DO UPDATE SET
                    field_type = EXCLUDED.field_type,
                    description = EXCLUDED.description,
                    is_deprecated = EXCLUDED.is_deprecated,
                    arguments = EXCLUDED.arguments,
                    type_detail = EXCLUDED.type_detail;
            END LOOP;

            migrated_count := migrated_count + 1;
        END LOOP;

        -- Migrate enum types
        FOR type_data IN SELECT * FROM jsonb_array_elements(schema_data->'enum_types')
        LOOP
            INSERT INTO graphql_types (scan_id, name, kind, description)
            VALUES (
                scan_record.scan_id,
                type_data->>'name',
                'ENUM',
                type_data->>'description'
            )
            ON CONFLICT (scan_id, name) DO UPDATE SET
                description = EXCLUDED.description;

            migrated_count := migrated_count + 1;
        END LOOP;

    END LOOP;

    RETURN migrated_count;
END;
$$ LANGUAGE plpgsql;

-- Function to migrate content data from JSON to normalized tables
CREATE OR REPLACE FUNCTION migrate_content_data()
RETURNS INTEGER AS $$
DECLARE
    scan_record RECORD;
    content_data JSONB;
    site_data JSONB;
    field_name TEXT;
    field_info JSONB;
    item_id UUID;
    migrated_count INTEGER := 0;
BEGIN
    -- Loop through all scans with enhanced content data
    FOR scan_record IN
        SELECT DISTINCT s.id as scan_id
        FROM scans s
        JOIN scan_modules sm ON s.id = sm.scan_id
        WHERE sm.module = 'enhanced-sitecore-content'
        AND sm.error IS NULL
    LOOP
        RAISE NOTICE 'Migrating content data for scan: %', scan_record.scan_id;

        -- Get the enhanced content data
        SELECT ar.result INTO content_data
        FROM scan_modules sm
        JOIN analysis_results ar ON sm.id = ar.scan_module_id
        WHERE sm.scan_id = scan_record.scan_id
        AND sm.module = 'enhanced-sitecore-content'
        LIMIT 1;

        -- Skip if no data found
        IF content_data IS NULL THEN
            CONTINUE;
        END IF;

        -- Migrate site/content items
        FOR site_data IN SELECT * FROM jsonb_array_elements(content_data->'sites')
        LOOP
            -- Insert content item
            INSERT INTO content_items (
                scan_id, sitecore_id, name, path, display_name,
                template_name, template_id, has_children, child_count
            )
            VALUES (
                scan_record.scan_id,
                site_data->>'id',
                site_data->>'name',
                site_data->>'path',
                site_data->>'display_name',
                site_data->>'template',
                site_data->>'template_id',
                COALESCE((site_data->>'has_children')::BOOLEAN, FALSE),
                COALESCE((site_data->>'child_count')::INTEGER, 0)
            )
            ON CONFLICT (scan_id, sitecore_id) DO UPDATE SET
                name = EXCLUDED.name,
                path = EXCLUDED.path,
                display_name = EXCLUDED.display_name,
                template_name = EXCLUDED.template_name,
                template_id = EXCLUDED.template_id,
                has_children = EXCLUDED.has_children,
                child_count = EXCLUDED.child_count
            RETURNING id INTO item_id;

            -- Migrate field values
            FOR field_name IN SELECT jsonb_object_keys(site_data->'field_samples')
            LOOP
                field_info := site_data->'field_samples'->field_name;

                INSERT INTO content_field_values (
                    item_id, field_name, field_value, value_type,
                    value_length, has_value, is_empty
                )
                VALUES (
                    item_id,
                    field_name,
                    field_info->>'value',
                    COALESCE((site_data->'field_types'->field_name)->>'value_type', 'Unknown'),
                    COALESCE((field_info->>'length')::INTEGER, 0),
                    COALESCE((field_info->>'has_value')::BOOLEAN, FALSE),
                    NOT COALESCE((field_info->>'has_value')::BOOLEAN, FALSE)
                )
                ON CONFLICT (item_id, field_name) DO UPDATE SET
                    field_value = EXCLUDED.field_value,
                    value_type = EXCLUDED.value_type,
                    value_length = EXCLUDED.value_length,
                    has_value = EXCLUDED.has_value,
                    is_empty = EXCLUDED.is_empty;
            END LOOP;

            migrated_count := migrated_count + 1;
        END LOOP;

    END LOOP;

    RETURN migrated_count;
END;
$$ LANGUAGE plpgsql;

-- =============================
-- EXECUTE MIGRATION
-- =============================

DO $$
DECLARE
    graphql_migrated INTEGER;
    content_migrated INTEGER;
BEGIN
    RAISE NOTICE 'Starting data migration...';

    -- Migrate GraphQL schema data
    SELECT migrate_graphql_schema_data() INTO graphql_migrated;
    RAISE NOTICE 'Migrated % GraphQL types', graphql_migrated;

    -- Migrate content data
    SELECT migrate_content_data() INTO content_migrated;
    RAISE NOTICE 'Migrated % content items', content_migrated;

    RAISE NOTICE 'Migration completed successfully!';
    RAISE NOTICE 'Total GraphQL types: %', graphql_migrated;
    RAISE NOTICE 'Total content items: %', content_migrated;
END $$;

-- =============================
-- POST-MIGRATION VERIFICATION
-- =============================

-- Verify migration results
DO $$
DECLARE
    table_stats RECORD;
BEGIN
    RAISE NOTICE 'Post-migration verification:';

    -- Check new table counts
    FOR table_stats IN
        SELECT
            'graphql_types' as table_name,
            COUNT(*) as row_count
        FROM graphql_types
        UNION ALL
        SELECT
            'graphql_fields' as table_name,
            COUNT(*) as row_count
        FROM graphql_fields
        UNION ALL
        SELECT
            'content_items' as table_name,
            COUNT(*) as row_count
        FROM content_items
        UNION ALL
        SELECT
            'content_field_values' as table_name,
            COUNT(*) as row_count
        FROM content_field_values
    LOOP
        RAISE NOTICE '  %: % rows', table_stats.table_name, table_stats.row_count;
    END LOOP;

    RAISE NOTICE 'Verification completed!';
END $$;

-- Clean up migration functions
DROP FUNCTION IF EXISTS migrate_graphql_schema_data();
DROP FUNCTION IF EXISTS migrate_content_data();

RAISE NOTICE 'Enhanced schema migration completed at %', NOW();