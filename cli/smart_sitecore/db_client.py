"""
Supabase Database Client for Sitecore Data Extraction
Phase 1: Implements the schema from supabase_kit.md

Connects to database at 10.0.0.196 with provided credentials
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import asyncpg
import asyncio


class SupabaseClient:
    """Database client for Phase 1 data extraction"""

    def __init__(self):
        # Database connection parameters from provided credentials
        self.host = "10.0.0.196"
        self.port = 5432
        self.database = "postgres"
        self.username = "postgres"
        self.password = "boTW1PbupfnkXRdlXr1RFdL7qqyi43wm"
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Initialize database connection pool"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.username,
                password=self.password,
                min_size=1,
                max_size=10
            )

    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def ensure_site(self, url: str) -> str:
        """Ensure site exists and return site_id"""
        await self.connect()

        async with self.pool.acquire() as conn:
            # Check if site exists
            row = await conn.fetchrow(
                "SELECT id FROM sites WHERE url = $1",
                url
            )

            if row:
                return str(row['id'])

            # Create new site
            site_id = str(uuid.uuid4())
            await conn.execute(
                "INSERT INTO sites (id, url, created_at) VALUES ($1, $2, $3)",
                site_id, url, datetime.utcnow()
            )
            return site_id

    async def create_scan(self, site_id: str, subscription_tier: str = "free") -> str:
        """Create new scan and return scan_id"""
        await self.connect()

        scan_id = str(uuid.uuid4())
        now = datetime.utcnow()

        async with self.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO scans (id, site_id, status, subscription_tier, created_at, started_at)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                scan_id, site_id, "running", subscription_tier, now, now
            )

        return scan_id

    async def finish_scan(self, scan_id: str, error: Optional[str] = None):
        """Mark scan as complete or error"""
        await self.connect()

        status = "error" if error else "complete"
        now = datetime.utcnow()

        async with self.pool.acquire() as conn:
            await conn.execute(
                """UPDATE scans
                   SET status = $1, finished_at = $2, error = $3
                   WHERE id = $4""",
                status, now, error, scan_id
            )

    async def save_module(
        self,
        scan_id: str,
        module: str,
        data_source: str,
        confidence: float,
        duration_ms: int,
        result: Any,
        requires_credentials: bool = True,
        error: Optional[str] = None
    ) -> str:
        """Save scan module and analysis result"""
        await self.connect()

        module_id = str(uuid.uuid4())
        result_id = str(uuid.uuid4())
        now = datetime.utcnow()

        async with self.pool.acquire() as conn:
            # Insert scan_module
            await conn.execute(
                """INSERT INTO scan_modules
                   (id, scan_id, module, data_source, confidence, requires_credentials,
                    duration_ms, error, created_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)""",
                module_id, scan_id, module, data_source, confidence,
                requires_credentials, duration_ms, error, now
            )

            # Insert analysis_result if we have data
            if result is not None:
                result_json = json.dumps(result, default=str)
                await conn.execute(
                    """INSERT INTO analysis_results (id, scan_module_id, result, created_at)
                       VALUES ($1, $2, $3, $4)""",
                    result_id, module_id, result_json, now
                )

        return module_id

    async def get_scan_results(self, scan_id: str) -> List[Dict[str, Any]]:
        """Get all results for a scan"""
        await self.connect()

        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """SELECT sm.module, sm.data_source, sm.confidence, sm.duration_ms,
                          sm.error, ar.result
                   FROM scan_modules sm
                   LEFT JOIN analysis_results ar ON sm.id = ar.scan_module_id
                   WHERE sm.scan_id = $1
                   ORDER BY sm.created_at""",
                scan_id
            )

            results = []
            for row in rows:
                result = {
                    'module': row['module'],
                    'data_source': row['data_source'],
                    'confidence': float(row['confidence']),
                    'duration_ms': row['duration_ms'],
                    'error': row['error'],
                    'result': json.loads(row['result']) if row['result'] else None
                }
                results.append(result)

            return results

    async def initialize_schema(self):
        """Initialize database schema if not exists"""
        await self.connect()

        schema_sql = """
        -- sites
        CREATE TABLE IF NOT EXISTS sites (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
          url text NOT NULL UNIQUE,
          slug text GENERATED ALWAYS AS (regexp_replace(lower(url), '[^a-z0-9]+', '-', 'g')) STORED,
          created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS sites_slug_idx ON sites(slug);

        -- scans
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

        -- scan_modules
        CREATE TABLE IF NOT EXISTS scan_modules (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
          scan_id uuid NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
          module text NOT NULL,                  -- "sitecore","openapi","sitemap","json"
          data_source text NOT NULL,             -- "sitecore-graphql","openapi","sitemap","json-sample"
          confidence real NOT NULL DEFAULT 0,
          requires_credentials boolean NOT NULL DEFAULT false,
          duration_ms integer NOT NULL DEFAULT 0,
          error text,
          created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS scan_modules_scan_idx ON scan_modules(scan_id);
        CREATE INDEX IF NOT EXISTS scan_modules_module_idx ON scan_modules(module);

        -- analysis_results
        CREATE TABLE IF NOT EXISTS analysis_results (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
          scan_module_id uuid NOT NULL REFERENCES scan_modules(id) ON DELETE CASCADE,
          result jsonb NOT NULL,
          created_at timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS analysis_results_gin ON analysis_results USING gin(result jsonb_path_ops);
        """

        async with self.pool.acquire() as conn:
            # Split and execute each statement
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            for statement in statements:
                try:
                    await conn.execute(statement)
                except Exception as e:
                    print(f"Schema initialization warning: {e}")

    async def test_connection(self) -> Dict[str, Any]:
        """Test database connection and return status"""
        try:
            await self.connect()

            async with self.pool.acquire() as conn:
                # Test basic query
                row = await conn.fetchrow("SELECT version() as version, now() as current_time")

                # Test schema existence
                tables = await conn.fetch(
                    """SELECT tablename FROM pg_tables
                       WHERE schemaname = 'public'
                       AND tablename IN ('sites', 'scans', 'scan_modules', 'analysis_results')
                       ORDER BY tablename"""
                )

                return {
                    'status': 'connected',
                    'database_version': row['version'],
                    'current_time': row['current_time'],
                    'tables_found': [t['tablename'] for t in tables],
                    'schema_ready': len(tables) == 4
                }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }


# Global client instance
db_client = SupabaseClient()