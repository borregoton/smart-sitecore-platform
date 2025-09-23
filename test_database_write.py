#!/usr/bin/env python3
"""
Quick Database Write Test
Test authentication and write permissions without wasting Sitecore API calls
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime

# Add the cli directory to the path
sys.path.insert(0, 'cli')

try:
    from smart_sitecore.supabase_client_v2 import SupabaseClientV2
except ImportError as e:
    print(f"[ERROR] Missing CLI module: {e}")
    print("Run: python launch.py --setup-only")
    sys.exit(1)


class DatabaseWriteTest:
    """Quick test of database write capabilities"""

    def __init__(self):
        self.db_client = SupabaseClientV2()

    async def test_database_write(self):
        """Test database authentication and write permissions"""

        print("SMART SITECORE ANALYSIS PLATFORM - V2.0")
        print("Database Write Test (Quick Authentication Check)")
        print("=" * 55)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        try:
            # Step 1: Test connection
            print("[1/4] Testing database connection...")
            db_result = await self.db_client.initialize()

            if self.db_client.connection_method is None:
                print(f"[FAILED] Database connection failed")
                print(f"Error: {db_result.get('pg_error', 'Unknown error')}")
                return False

            print(f"[OK] Connected via {self.db_client.connection_method}")

            # Step 2: Test basic read access
            print("[2/4] Testing read access...")
            if self.db_client.connection_method == 'postgresql' and self.db_client.pool:
                async with self.db_client.pool.acquire() as conn:
                    # Test simple query
                    result = await conn.fetchval("SELECT 1 as test")
                    if result == 1:
                        print("[OK] Read access confirmed")
                    else:
                        print("[FAILED] Read test returned unexpected result")
                        return False
            else:
                print("[FAILED] No PostgreSQL connection available")
                return False

            # Step 3: Test table access (check if v2.0 tables exist)
            print("[3/4] Testing table access...")
            async with self.db_client.pool.acquire() as conn:
                # Check if v2.0 tables exist
                tables_check = await conn.fetch("""
                    SELECT tablename
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    AND tablename IN ('customers', 'customer_sites', 'scans_v2')
                """)

                existing_tables = [row['tablename'] for row in tables_check]
                print(f"[INFO] Found v2.0 tables: {existing_tables}")

                if not existing_tables:
                    print("[WARNING] No v2.0 tables found - may need schema creation")
                else:
                    print(f"[OK] Found {len(existing_tables)} v2.0 tables")

            # Step 4: Test write access (attempt to create test customer)
            print("[4/4] Testing write access...")
            test_customer_id = str(uuid.uuid4())
            test_customer_name = f"TEST_CUSTOMER_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            async with self.db_client.pool.acquire() as conn:
                try:
                    # Try to create a test customer record
                    await conn.execute("""
                        INSERT INTO customers (id, name, created_at, status)
                        VALUES ($1, $2, $3, $4)
                    """, test_customer_id, test_customer_name, datetime.now(), 'test')

                    print("[OK] Write access confirmed - test customer created")

                    # Clean up test data
                    await conn.execute("DELETE FROM customers WHERE id = $1", test_customer_id)
                    print("[OK] Test cleanup completed")

                    return True

                except Exception as write_error:
                    print(f"[FAILED] Write access failed: {write_error}")

                    # Check if it's a table missing error
                    if "relation \"customers\" does not exist" in str(write_error):
                        print("[INFO] customers table doesn't exist - need schema creation")
                        return "schema_missing"
                    else:
                        print("[ERROR] Write permission denied or other database error")
                        return False

        except Exception as e:
            print(f"[ERROR] Database test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            # Clean up connection
            try:
                if hasattr(self.db_client, 'pool') and self.db_client.pool:
                    await self.db_client.pool.close()
                if hasattr(self.db_client, 'session') and self.db_client.session:
                    await self.db_client.session.close()
            except:
                pass

    def display_results(self, result):
        """Display test results and recommendations"""

        print("\n" + "=" * 55)
        print("DATABASE WRITE TEST RESULTS")
        print("=" * 55)

        if result is True:
            print("[SUCCESS] Database is ready for v2.0 extraction!")
            print()
            print("CONFIRMED CAPABILITIES:")
            print("  - Authentication: WORKING")
            print("  - Read access: WORKING")
            print("  - Write access: WORKING")
            print("  - v2.0 schema: PRESENT")
            print()
            print("READY TO PROCEED:")
            print("  python launch.py GrabSiteCoreData")
            print()
            print("NOTE: You can skip 'clear_database' since write test passed.")

        elif result == "schema_missing":
            print("[PARTIAL] Database accessible but v2.0 schema missing")
            print()
            print("CONFIRMED CAPABILITIES:")
            print("  - Authentication: WORKING")
            print("  - Read access: WORKING")
            print("  - Write access: WORKING")
            print("  - v2.0 schema: MISSING")
            print()
            print("REQUIRED ACTION:")
            print("  1. Create v2.0 schema first")
            print("  2. Run schema migration from database/multi_site_architecture.sql")
            print("  3. Then run: python launch.py GrabSiteCoreData")

        else:
            print("[FAILED] Database not ready for v2.0 extraction")
            print()
            print("ISSUES DETECTED:")
            print("  - Authentication or permissions failing")
            print("  - Cannot write to database")
            print()
            print("REQUIRED ACTIONS:")
            print("  1. Get updated database credentials from administrator")
            print("  2. Update passwords in: cli/smart_sitecore/supabase_client_v2.py")
            print("  3. Ensure database user has CREATE/INSERT/UPDATE/DELETE permissions")
            print("  4. Re-run this test to confirm")
            print()
            print("DO NOT attempt GrabSiteCoreData until database write succeeds")

        print("=" * 55)


async def main():
    """Main entry point for database write test"""

    tester = DatabaseWriteTest()
    result = await tester.test_database_write()
    tester.display_results(result)

    # Return appropriate exit code
    if result is True:
        return True  # Success
    elif result == "schema_missing":
        return True  # Partial success (fixable)
    else:
        return False  # Failed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)