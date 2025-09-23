-- =====================================================
-- SMART Sitecore Analysis Platform - Database Schema
-- Based on supabase_kit.md specification
-- Execute this in Supabase Studio SQL Editor
-- =====================================================

-- Clean up existing tables if they exist (optional)
-- Uncomment the following lines if you need to recreate the schema
-- DROP TABLE IF EXISTS analysis_results CASCADE;
-- DROP TABLE IF EXISTS scan_modules CASCADE;
-- DROP TABLE IF EXISTS scans CASCADE;
-- DROP TABLE IF EXISTS sites CASCADE;

-- =====================================================
-- 1. SITES TABLE
-- Stores website URLs that are being analyzed
-- =====================================================
CREATE TABLE IF NOT EXISTS sites (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  url text NOT NULL UNIQUE,
  slug text GENERATED ALWAYS AS (regexp_replace(lower(url), '[^a-z0-9]+', '-', 'g')) STORED,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS sites_slug_idx ON sites(slug);

-- =====================================================
-- 2. SCANS TABLE
-- Stores scan sessions for each site
-- =====================================================
CREATE TABLE IF NOT EXISTS scans (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  site_id uuid NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
  status text NOT NULL DEFAULT 'queued', -- queued|running|complete|error
  subscription_tier text DEFAULT 'free',
  created_at timestamptz NOT NULL DEFAULT now(),
  started_at timestamptz,
  finished_at timestamptz,
  error text
);

CREATE INDEX IF NOT EXISTS scans_site_idx ON scans(site_id);

-- =====================================================
-- 3. SCAN_MODULES TABLE
-- Stores individual analysis modules run during each scan
-- =====================================================
CREATE TABLE IF NOT EXISTS scan_modules (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  scan_id uuid NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
  module text NOT NULL,                  -- "sitecore","openapi","sitemap","json"
  data_source text NOT NULL,             -- "sitecore-graphql","openapi","sitemap","json-sample"
  confidence real NOT NULL DEFAULT 0,    -- 0.0 to 1.0 confidence score
  requires_credentials boolean NOT NULL DEFAULT false,
  duration_ms integer NOT NULL DEFAULT 0,
  error text,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS scan_modules_scan_idx ON scan_modules(scan_id);
CREATE INDEX IF NOT EXISTS scan_modules_module_idx ON scan_modules(module);

-- =====================================================
-- 4. ANALYSIS_RESULTS TABLE
-- Stores the actual analysis results as JSONB
-- =====================================================
CREATE TABLE IF NOT EXISTS analysis_results (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  scan_module_id uuid NOT NULL REFERENCES scan_modules(id) ON DELETE CASCADE,
  result jsonb NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS analysis_results_gin ON analysis_results USING gin(result jsonb_path_ops);

-- =====================================================
-- VERIFICATION QUERIES
-- Run these to verify the schema was created correctly
-- =====================================================

-- Check all tables exist
SELECT
  tablename,
  schemaname
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('sites', 'scans', 'scan_modules', 'analysis_results')
ORDER BY tablename;

-- Check indexes
SELECT
  indexname,
  tablename
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('sites', 'scans', 'scan_modules', 'analysis_results')
ORDER BY tablename, indexname;

-- Test insert permissions (optional)
-- Uncomment to test if inserts work
/*
INSERT INTO sites (url) VALUES ('https://test-connection.example.com')
ON CONFLICT (url) DO NOTHING;

SELECT 'Schema verification: SUCCESS - All tables created and accessible' as status;
*/

-- =====================================================
-- SAMPLE QUERIES FOR TESTING
-- =====================================================

-- After Phase 1 extraction runs, you can use these queries:

-- 1. View all sites
-- SELECT * FROM sites ORDER BY created_at DESC;

-- 2. View recent scans with their status
-- SELECT s.id, s.status, st.url, s.created_at, s.finished_at
-- FROM scans s
-- JOIN sites st ON s.site_id = st.id
-- ORDER BY s.created_at DESC;

-- 3. View scan modules and their results
-- SELECT
--   sm.module,
--   sm.data_source,
--   sm.confidence,
--   sm.duration_ms,
--   sm.error,
--   ar.result
-- FROM scan_modules sm
-- LEFT JOIN analysis_results ar ON sm.id = ar.scan_module_id
-- WHERE sm.scan_id = 'YOUR_SCAN_ID_HERE'
-- ORDER BY sm.created_at;

-- =====================================================
-- SCHEMA READY!
-- Your Phase 1 Sitecore extraction can now save data to these tables
-- =====================================================