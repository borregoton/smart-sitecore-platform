"""
Supabase Database Client V2 - Multiple Connection Strategies
Handles different connection methods based on what's available
"""

import json
import uuid
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import asyncpg


class SupabaseClientV2:
    """Enhanced database client with multiple connection strategies"""

    def __init__(self):
        # Connection parameters
        self.host = "10.0.0.196"
        self.pg_port = 5432
        self.api_port = 8000

        # Credentials to try (including tenant-based format)
        tenant_id = "zyafowjs5i4ltxxq"
        self.credentials = {
            'postgres_with_tenant': {
                'user': f'postgres.{tenant_id}',
                'password': 'boTW1PbupfnkXRdlXr1RFdL7qqyi43wm',
                'database': 'postgres'
            },
            'postgres': {
                'user': 'postgres',
                'password': 'boTW1PbupfnkXRdlXr1RFdL7qqyi43wm',
                'database': 'postgres'
            },
            'supabase_with_tenant': {
                'user': f'supabase.{tenant_id}',
                'password': 'yRPHDq9MaQt6JIDl3kSkoR2E',
                'database': 'postgres'
            },
            'supabase': {
                'user': 'supabase',
                'password': 'yRPHDq9MaQt6JIDl3kSkoR2E',
                'database': 'postgres'
            }
        }

        # Connection state
        self.connection_method = None
        self.pool: Optional[asyncpg.Pool] = None
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self) -> Dict[str, Any]:
        """Try different connection methods and return what works"""

        # Strategy 1: Direct PostgreSQL connection
        pg_result = await self._try_postgresql()
        if pg_result['success']:
            self.connection_method = 'postgresql'
            return {
                'method': 'postgresql',
                'status': 'connected',
                'details': pg_result
            }

        # Strategy 2: Supabase REST API (if we can figure out auth)
        api_result = await self._try_rest_api()
        if api_result['success']:
            self.connection_method = 'rest_api'
            return {
                'method': 'rest_api',
                'status': 'connected',
                'details': api_result
            }

        # Strategy 3: Local fallback (what we've been using)
        return {
            'method': 'local_fallback',
            'status': 'using_local_files',
            'message': 'No direct database connection available, using local JSON files',
            'pg_error': pg_result.get('error'),
            'api_error': api_result.get('error')
        }

    async def _try_postgresql(self) -> Dict[str, Any]:
        """Try PostgreSQL connection with different credentials"""

        for cred_name, creds in self.credentials.items():
            try:
                # Test connection
                conn = await asyncpg.connect(
                    host=self.host,
                    port=self.pg_port,
                    database=creds['database'],
                    user=creds['user'],
                    password=creds['password'],
                    timeout=10
                )

                # Test basic query
                version = await conn.fetchval("SELECT version()")

                # Test our schema
                tables = await conn.fetch(
                    """SELECT tablename FROM pg_tables
                       WHERE schemaname = 'public'
                       AND tablename IN ('sites', 'scans', 'scan_modules', 'analysis_results')"""
                )

                # Create pool if connection works
                self.pool = await asyncpg.create_pool(
                    host=self.host,
                    port=self.pg_port,
                    database=creds['database'],
                    user=creds['user'],
                    password=creds['password'],
                    min_size=1,
                    max_size=5
                )

                await conn.close()

                return {
                    'success': True,
                    'credentials': cred_name,
                    'database_version': version.split()[0:2],
                    'schema_tables': [t['tablename'] for t in tables],
                    'schema_ready': len(tables) == 4
                }

            except Exception as e:
                continue

        return {
            'success': False,
            'error': 'All PostgreSQL connection attempts failed'
        }

    async def _try_rest_api(self) -> Dict[str, Any]:
        """Try Supabase REST API connection"""

        try:
            # Create session for API calls
            timeout = aiohttp.ClientTimeout(total=10)
            self.session = aiohttp.ClientSession(timeout=timeout)

            # Try different auth methods
            auth_variants = [
                {'apikey': self.credentials['supabase']['password']},
                {'Authorization': f"Bearer {self.credentials['supabase']['password']}"},
                {
                    'apikey': self.credentials['supabase']['password'],
                    'Authorization': f"Bearer {self.credentials['supabase']['password']}"
                }
            ]

            for headers in auth_variants:
                try:
                    url = f"http://{self.host}:{self.api_port}/rest/v1/"
                    async with self.session.get(url, headers=headers) as response:
                        if response.status == 200:
                            return {
                                'success': True,
                                'auth_method': headers,
                                'api_url': url
                            }
                except:
                    continue

            return {
                'success': False,
                'error': 'REST API authentication failed'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'REST API connection failed: {e}'
            }

    async def ensure_site(self, url: str) -> str:
        """Ensure site exists and return site_id"""
        if self.connection_method == 'postgresql':
            return await self._pg_ensure_site(url)
        elif self.connection_method == 'rest_api':
            return await self._api_ensure_site(url)
        else:
            # Fallback to local implementation
            from .local_db_client import local_db_client
            return await local_db_client.ensure_site(url)

    async def _pg_ensure_site(self, url: str) -> str:
        """PostgreSQL implementation"""
        async with self.pool.acquire() as conn:
            # Check if exists
            row = await conn.fetchrow("SELECT id FROM sites WHERE url = $1", url)
            if row:
                return str(row['id'])

            # Create new
            site_id = str(uuid.uuid4())
            await conn.execute(
                "INSERT INTO sites (id, url, created_at) VALUES ($1, $2, $3)",
                site_id, url, datetime.utcnow()
            )
            return site_id

    async def _api_ensure_site(self, url: str) -> str:
        """REST API implementation"""
        # This would need the correct API authentication
        # For now, fallback to local
        from .local_db_client import local_db_client
        return await local_db_client.ensure_site(url)

    async def create_scan(self, site_id: str, subscription_tier: str = "free") -> str:
        """Create new scan"""
        if self.connection_method == 'postgresql':
            return await self._pg_create_scan(site_id, subscription_tier)
        else:
            from .local_db_client import local_db_client
            return await local_db_client.create_scan(site_id, subscription_tier)

    async def _pg_create_scan(self, site_id: str, subscription_tier: str) -> str:
        """PostgreSQL implementation"""
        scan_id = str(uuid.uuid4())
        now = datetime.utcnow()

        async with self.pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO scans (id, site_id, status, subscription_tier, created_at, started_at)
                   VALUES ($1, $2, $3, $4, $5, $6)""",
                scan_id, site_id, "running", subscription_tier, now, now
            )
        return scan_id

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
        """Save scan module and result"""
        if self.connection_method == 'postgresql':
            return await self._pg_save_module(
                scan_id, module, data_source, confidence, duration_ms,
                result, requires_credentials, error
            )
        else:
            from .local_db_client import local_db_client
            return await local_db_client.save_module(
                scan_id, module, data_source, confidence, duration_ms,
                result, requires_credentials, error
            )

    async def _pg_save_module(
        self, scan_id: str, module: str, data_source: str, confidence: float,
        duration_ms: int, result: Any, requires_credentials: bool, error: Optional[str]
    ) -> str:
        """PostgreSQL implementation"""
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

    async def finish_scan(self, scan_id: str, error: Optional[str] = None):
        """Mark scan as complete"""
        if self.connection_method == 'postgresql':
            await self._pg_finish_scan(scan_id, error)
        else:
            from .local_db_client import local_db_client
            await local_db_client.finish_scan(scan_id, error)

    async def _pg_finish_scan(self, scan_id: str, error: Optional[str]):
        """PostgreSQL implementation"""
        status = "error" if error else "complete"
        now = datetime.utcnow()

        async with self.pool.acquire() as conn:
            await conn.execute(
                """UPDATE scans
                   SET status = $1, finished_at = $2, error = $3
                   WHERE id = $4""",
                status, now, error, scan_id
            )

    async def get_scan_results(self, scan_id: str) -> List[Dict[str, Any]]:
        """Get all results for a scan"""
        if self.connection_method == 'postgresql':
            return await self._pg_get_scan_results(scan_id)
        else:
            from .local_db_client import local_db_client
            return await local_db_client.get_scan_results(scan_id)

    async def _pg_get_scan_results(self, scan_id: str) -> List[Dict[str, Any]]:
        """PostgreSQL implementation"""
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

    async def test_connection(self) -> Dict[str, Any]:
        """Test and return connection status"""
        connection_status = await self.initialize()

        if connection_status['method'] == 'postgresql':
            # Test schema if PostgreSQL works
            try:
                async with self.pool.acquire() as conn:
                    tables = await conn.fetch(
                        """SELECT tablename FROM pg_tables
                           WHERE schemaname = 'public'
                           AND tablename IN ('sites', 'scans', 'scan_modules', 'analysis_results')"""
                    )

                    connection_status['schema_status'] = {
                        'tables_found': [t['tablename'] for t in tables],
                        'schema_ready': len(tables) == 4
                    }
            except Exception as e:
                connection_status['schema_error'] = str(e)

        return connection_status

    async def close(self):
        """Close connections"""
        if self.pool:
            await self.pool.close()
        if self.session:
            await self.session.close()


# Global instance
supabase_client_v2 = SupabaseClientV2()