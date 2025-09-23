#!/usr/bin/env python3
"""
Database Schema Inspector
Examine the actual database schema to understand what exists vs what's expected
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the cli directory to the path
sys.path.insert(0, 'cli')

try:
    from smart_sitecore.supabase_client_v2 import SupabaseClientV2
except ImportError as e:
    print(f"[ERROR] Missing CLI module: {e}")
    print("Run: python launch.py --setup-only")
    sys.exit(1)


class SchemaInspector:
    """Inspect database schema and compare with expectations"""

    def __init__(self):
        self.db_client = SupabaseClientV2()

    async def inspect_schema(self):
        """Comprehensive schema inspection"""

        print("SMART SITECORE ANALYSIS PLATFORM - V2.0")
        print("Database Schema Inspector")
        print("=" * 55)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        try:
            # Connect to database
            print("[1/5] Connecting to database...")
            db_result = await self.db_client.initialize()

            if self.db_client.connection_method != 'postgresql':
                print("[ERROR] Need PostgreSQL connection for schema inspection")
                return False

            print("[OK] Connected successfully")

            # Get all tables
            print("[2/5] Listing all tables...")
            async with self.db_client.pool.acquire() as conn:
                tables = await conn.fetch("""
                    SELECT tablename, schemaname
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    ORDER BY tablename
                """)

                print(f"[OK] Found {len(tables)} tables")
                for table in tables:
                    print(f"  - {table['tablename']}")

            # Check v2.0 specific tables
            print("\n[3/5] Checking v2.0 multi-site tables...")
            v2_tables = ['customers', 'customer_sites', 'scans_v2', 'site_relationships', 'cross_site_comparisons']

            for table_name in v2_tables:
                await self._inspect_table(table_name)

            # Check v1.0 legacy tables
            print("\n[4/5] Checking v1.0 legacy tables...")
            v1_tables = ['sites', 'scans', 'graphql_types', 'content_items', 'analysis_results']

            for table_name in v1_tables:
                await self._inspect_table(table_name)

            # Schema recommendations
            print("\n[5/5] Generating schema recommendations...")
            await self._generate_recommendations()

            return True

        except Exception as e:
            print(f"[ERROR] Schema inspection failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            # Clean up
            try:
                if hasattr(self.db_client, 'pool') and self.db_client.pool:
                    await self.db_client.pool.close()
            except:
                pass

    async def _inspect_table(self, table_name):
        """Inspect a specific table structure"""

        async with self.db_client.pool.acquire() as conn:
            try:
                # Get table columns
                columns = await conn.fetch("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = $1 AND table_schema = 'public'
                    ORDER BY ordinal_position
                """, table_name)

                if columns:
                    print(f"\n  {table_name}:")
                    for col in columns:
                        nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
                        default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
                        print(f"    {col['column_name']:<20} {col['data_type']:<15} {nullable}{default}")

                    # Get row count
                    count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
                    print(f"    [INFO] Contains {count} rows")

                else:
                    print(f"  {table_name}: TABLE NOT FOUND")

            except Exception as e:
                print(f"  {table_name}: ERROR - {e}")

    async def _generate_recommendations(self):
        """Generate recommendations based on schema inspection"""

        print("\n" + "=" * 55)
        print("SCHEMA ANALYSIS & RECOMMENDATIONS")
        print("=" * 55)

        async with self.db_client.pool.acquire() as conn:
            # Check if customers table exists and what columns it has
            customers_cols = await conn.fetch("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'customers' AND table_schema = 'public'
            """)

            customer_sites_cols = await conn.fetch("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'customer_sites' AND table_schema = 'public'
            """)

            scans_v2_cols = await conn.fetch("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'scans_v2' AND table_schema = 'public'
            """)

        # Expected v2.0 schema
        expected_customers = ['id', 'name', 'created_at', 'status']
        expected_customer_sites = ['id', 'customer_id', 'name', 'url', 'sitecore_url', 'created_at', 'status']
        expected_scans_v2 = ['id', 'customer_id', 'site_id', 'scan_type', 'status', 'started_at', 'completed_at', 'metadata', 'results', 'error_message']

        if customers_cols:
            actual_customers = [col['column_name'] for col in customers_cols]
            missing_customers = set(expected_customers) - set(actual_customers)
            extra_customers = set(actual_customers) - set(expected_customers)

            print("CUSTOMERS TABLE ANALYSIS:")
            print(f"  Expected columns: {expected_customers}")
            print(f"  Actual columns:   {actual_customers}")
            if missing_customers:
                print(f"  Missing columns:  {list(missing_customers)}")
            if extra_customers:
                print(f"  Extra columns:    {list(extra_customers)}")
        else:
            print("CUSTOMERS TABLE: NOT FOUND")

        print("\nRECOMMENDED ACTIONS:")

        if not customers_cols:
            print("1. [CRITICAL] Create v2.0 multi-site schema")
            print("   - Run database migration script")
            print("   - Create customers, customer_sites, scans_v2 tables")

        elif customers_cols and set(['id', 'name', 'created_at']) <= set([col['column_name'] for col in customers_cols]):
            if 'status' not in [col['column_name'] for col in customers_cols]:
                print("1. [SCHEMA UPDATE] Add missing 'status' column to customers table")
                print("   SQL: ALTER TABLE customers ADD COLUMN status VARCHAR(50) DEFAULT 'active'")

            print("2. [CODE UPDATE] Alternatively, modify extraction code to match existing schema")
            print("3. [TEST AGAIN] Re-run GrabSiteCoreData after schema fix")

        else:
            print("1. [MAJOR MISMATCH] Schema structure significantly different")
            print("   - Consider fresh schema creation")
            print("   - Or major code modifications to match existing structure")

        print("\nIMMEDIATE NEXT STEPS:")
        print("1. Review the schema analysis above")
        print("2. Choose: Fix schema OR modify code")
        print("3. For quick fix: Add missing columns to existing tables")
        print("4. For clean start: Create complete v2.0 schema")


async def main():
    """Main entry point for schema inspection"""

    inspector = SchemaInspector()
    success = await inspector.inspect_schema()

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)