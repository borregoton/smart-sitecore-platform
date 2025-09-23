#!/usr/bin/env python3
"""
Fix V2.0 Schema Issues
Add missing columns to make existing schema compatible with v2.0 extraction code
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


class SchemaFixer:
    """Fix schema compatibility issues for v2.0 extraction"""

    def __init__(self):
        self.db_client = SupabaseClientV2()

    async def fix_schema(self):
        """Apply schema fixes to make existing database v2.0 compatible"""

        print("SMART SITECORE ANALYSIS PLATFORM - V2.0")
        print("Schema Compatibility Fix")
        print("=" * 55)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        try:
            # Connect to database
            print("[1/4] Connecting to database...")
            db_result = await self.db_client.initialize()

            if self.db_client.connection_method != 'postgresql':
                print("[ERROR] Need PostgreSQL connection for schema fixes")
                return False

            print("[OK] Connected successfully")

            # Check current schema state
            print("[2/4] Analyzing current schema...")
            issues = await self._analyze_schema_issues()

            if not issues:
                print("[OK] No schema issues found - database is v2.0 compatible!")
                return True

            # Apply fixes
            print("[3/4] Applying schema fixes...")
            await self._apply_fixes(issues)

            # Verify fixes
            print("[4/4] Verifying fixes...")
            remaining_issues = await self._analyze_schema_issues()

            if not remaining_issues:
                print("[SUCCESS] All schema issues resolved!")
                print("\nDatabase is now v2.0 compatible!")
                print("Ready to run: python launch.py GrabSiteCoreData")
                return True
            else:
                print(f"[WARNING] {len(remaining_issues)} issues remain")
                for issue in remaining_issues:
                    print(f"  - {issue}")
                return False

        except Exception as e:
            print(f"[ERROR] Schema fix failed: {e}")
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

    async def _analyze_schema_issues(self):
        """Analyze what schema issues exist for complete v2.0 multi-site architecture"""

        issues = []

        # Complete v2.0 multi-site schema requirements
        required_tables = {
            'customers': ['id', 'name', 'created_at', 'status'],
            'customer_sites': ['id', 'customer_id', 'name', 'url', 'sitecore_url', 'created_at', 'status'],
            'scans_v2': ['id', 'customer_id', 'site_id', 'scan_type', 'status', 'started_at', 'completed_at', 'metadata', 'results', 'error_message'],
            'site_relationships': ['id', 'primary_site_id', 'related_site_id', 'relationship_type', 'created_at'],
            'cross_site_comparisons': ['id', 'scan_id', 'comparison_type', 'site_a_id', 'site_b_id', 'metrics', 'created_at'],
            'portfolio_insights': ['id', 'customer_id', 'insight_type', 'data', 'generated_at'],
            'benchmark_data': ['id', 'industry', 'company_size', 'region', 'metric_name', 'value', 'percentile', 'updated_at']
        }

        async with self.db_client.pool.acquire() as conn:
            for table_name, required_cols in required_tables.items():
                table_cols = await conn.fetch("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = $1 AND table_schema = 'public'
                """, table_name)

                if table_cols:
                    actual_cols = [col['column_name'] for col in table_cols]
                    missing_cols = set(required_cols) - set(actual_cols)
                    if missing_cols:
                        issues.append(f"{table_name} table missing columns: {list(missing_cols)}")
                else:
                    issues.append(f"{table_name} table does not exist")

        return issues

    async def _apply_fixes(self, issues):
        """Apply fixes for complete v2.0 multi-site schema"""

        async with self.db_client.pool.acquire() as conn:
            for issue in issues:
                print(f"  Fixing: {issue}")

                try:
                    # Handle specific column additions to existing tables
                    if "customers table missing columns:" in issue and "status" in issue:
                        await conn.execute("""
                            ALTER TABLE customers
                            ADD COLUMN IF NOT EXISTS status VARCHAR(50) DEFAULT 'active'
                        """)
                        print(f"    [OK] Added 'status' column to customers table")

                    # Create complete v2.0 multi-site tables
                    elif "customer_sites table does not exist" in issue:
                        await conn.execute("""
                            CREATE TABLE customer_sites (
                                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
                                name VARCHAR(255) NOT NULL,
                                url VARCHAR(500),
                                sitecore_url VARCHAR(500) NOT NULL,
                                created_at TIMESTAMPTZ DEFAULT NOW(),
                                updated_at TIMESTAMPTZ DEFAULT NOW(),
                                status VARCHAR(50) DEFAULT 'active',
                                CONSTRAINT unique_customer_site_name UNIQUE(customer_id, name)
                            )
                        """)
                        print(f"    [OK] Created customer_sites table with proper foreign keys")

                    elif "scans_v2 table does not exist" in issue:
                        await conn.execute("""
                            CREATE TABLE scans_v2 (
                                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
                                site_id UUID REFERENCES customer_sites(id) ON DELETE CASCADE,
                                scan_type VARCHAR(100) NOT NULL DEFAULT 'full_extraction',
                                status VARCHAR(50) DEFAULT 'pending',
                                started_at TIMESTAMPTZ DEFAULT NOW(),
                                completed_at TIMESTAMPTZ,
                                metadata JSONB DEFAULT '{}',
                                results JSONB DEFAULT '{}',
                                error_message TEXT,
                                duration_seconds INTEGER,
                                items_extracted INTEGER DEFAULT 0,
                                api_calls_made INTEGER DEFAULT 0
                            )
                        """)
                        print(f"    [OK] Created scans_v2 table with extraction tracking")

                    elif "site_relationships table does not exist" in issue:
                        await conn.execute("""
                            CREATE TABLE site_relationships (
                                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                primary_site_id UUID REFERENCES customer_sites(id) ON DELETE CASCADE,
                                related_site_id UUID REFERENCES customer_sites(id) ON DELETE CASCADE,
                                relationship_type VARCHAR(100) NOT NULL,
                                created_at TIMESTAMPTZ DEFAULT NOW(),
                                metadata JSONB DEFAULT '{}',
                                CONSTRAINT no_self_relationship CHECK (primary_site_id != related_site_id),
                                CONSTRAINT unique_site_relationship UNIQUE(primary_site_id, related_site_id, relationship_type)
                            )
                        """)
                        print(f"    [OK] Created site_relationships table for cross-site analysis")

                    elif "cross_site_comparisons table does not exist" in issue:
                        await conn.execute("""
                            CREATE TABLE cross_site_comparisons (
                                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                scan_id UUID REFERENCES scans_v2(id) ON DELETE CASCADE,
                                comparison_type VARCHAR(100) NOT NULL,
                                site_a_id UUID REFERENCES customer_sites(id) ON DELETE CASCADE,
                                site_b_id UUID REFERENCES customer_sites(id) ON DELETE CASCADE,
                                metrics JSONB NOT NULL DEFAULT '{}',
                                created_at TIMESTAMPTZ DEFAULT NOW(),
                                CONSTRAINT no_self_comparison CHECK (site_a_id != site_b_id)
                            )
                        """)
                        print(f"    [OK] Created cross_site_comparisons table for benchmarking")

                    elif "portfolio_insights table does not exist" in issue:
                        await conn.execute("""
                            CREATE TABLE portfolio_insights (
                                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
                                insight_type VARCHAR(100) NOT NULL,
                                data JSONB NOT NULL DEFAULT '{}',
                                generated_at TIMESTAMPTZ DEFAULT NOW(),
                                expires_at TIMESTAMPTZ,
                                confidence_score DECIMAL(3,2),
                                tags VARCHAR[] DEFAULT '{}'
                            )
                        """)
                        print(f"    [OK] Created portfolio_insights table for dashboard analytics")

                    elif "benchmark_data table does not exist" in issue:
                        await conn.execute("""
                            CREATE TABLE benchmark_data (
                                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                                industry VARCHAR(100),
                                company_size VARCHAR(50),
                                region VARCHAR(100),
                                metric_name VARCHAR(150) NOT NULL,
                                value DECIMAL(15,4) NOT NULL,
                                percentile DECIMAL(5,2),
                                sample_size INTEGER,
                                updated_at TIMESTAMPTZ DEFAULT NOW(),
                                source VARCHAR(100) DEFAULT 'internal',
                                CONSTRAINT unique_benchmark UNIQUE(industry, company_size, region, metric_name)
                            )
                        """)
                        print(f"    [OK] Created benchmark_data table for industry comparisons")

                    # Handle missing columns in existing tables
                    elif "table missing columns:" in issue:
                        table_name = issue.split()[0]
                        print(f"    [INFO] Adding missing columns to {table_name} (specific implementation needed)")

                except Exception as e:
                    print(f"    [ERROR] Failed to fix '{issue}': {e}")
                    # Continue with other fixes even if one fails

            # Create useful indexes for performance
            try:
                print(f"  Creating performance indexes...")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_customer_sites_customer_id ON customer_sites(customer_id)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_scans_v2_customer_site ON scans_v2(customer_id, site_id)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_scans_v2_status ON scans_v2(status)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_portfolio_insights_customer ON portfolio_insights(customer_id)")
                await conn.execute("CREATE INDEX IF NOT EXISTS idx_benchmark_data_lookup ON benchmark_data(industry, company_size, region)")
                print(f"    [OK] Created performance indexes")
            except Exception as e:
                print(f"    [WARNING] Some indexes may already exist: {e}")

    async def _test_v2_compatibility(self):
        """Test if the schema is now v2.0 compatible"""

        try:
            async with self.db_client.pool.acquire() as conn:
                # Try the exact operations that failed before
                test_customer_id = "00000000-0000-0000-0000-000000000001"

                # Test customer creation (this was failing before)
                await conn.execute("""
                    INSERT INTO customers (id, name, created_at, status)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    status = EXCLUDED.status
                """, test_customer_id, "Test Customer V2", datetime.now(), 'active')

                # Clean up test data
                await conn.execute("DELETE FROM customers WHERE id = $1", test_customer_id)

                return True

        except Exception as e:
            print(f"[ERROR] V2 compatibility test failed: {e}")
            return False


async def main():
    """Main entry point for schema fixing"""

    fixer = SchemaFixer()
    success = await fixer.fix_schema()

    if success:
        print("\n[SUCCESS] Schema is now v2.0 compatible!")
        print("You can now run: python launch.py GrabSiteCoreData")
    else:
        print("\n[ERROR] Schema fixes incomplete")
        print("Manual intervention may be required")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)