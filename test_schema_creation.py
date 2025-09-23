#!/usr/bin/env python3
"""
Test Schema Creation and Connection
Demonstrates the next steps for database connectivity
"""

import asyncio
import sys
import os
sys.path.insert(0, 'cli')

from smart_sitecore.supabase_client_v2 import supabase_client_v2


async def test_connection_strategies():
    """Test all available connection strategies"""

    print("SUPABASE CONNECTION ANALYSIS")
    print("=" * 35)

    print(f"Target Database: {supabase_client_v2.host}")
    print(f"PostgreSQL Port: {supabase_client_v2.pg_port}")
    print(f"API Port: {supabase_client_v2.api_port}")

    print(f"\nTesting connection strategies...")
    print("-" * 35)

    try:
        # Test all connection methods
        status = await supabase_client_v2.test_connection()

        print(f"Connection Method: {status['method']}")
        print(f"Status: {status['status']}")

        if status['method'] == 'postgresql':
            print(f"SUCCESS - Direct PostgreSQL connection working!")
            details = status['details']
            print(f"  Credentials: {details['credentials']}")
            print(f"  Database Version: {details['database_version']}")
            print(f"  Schema Tables: {details['schema_tables']}")
            print(f"  Schema Ready: {details['schema_ready']}")

            if not details['schema_ready']:
                print(f"\n  SCHEMA NEEDED - Only {len(details['schema_tables'])}/4 tables found")
                print(f"  Next step: Run create_supabase_schema.sql in Supabase Studio")

        elif status['method'] == 'rest_api':
            print(f"SUCCESS - REST API connection working!")
            details = status['details']
            print(f"  API URL: {details['api_url']}")
            print(f"  Auth Method: {details['auth_method']}")

        else:
            print(f"FALLBACK - Using local JSON files")
            print(f"  Reason: No direct database connection available")
            if 'pg_error' in status:
                print(f"  PostgreSQL Error: {status['pg_error']}")
            if 'api_error' in status:
                print(f"  API Error: {status['api_error']}")

        print(f"\nNEXT STEPS:")
        print(f"-" * 12)

        if status['method'] == 'local_fallback':
            print(f"1. Open Supabase Studio: http://10.0.0.196:8000/project/default/database/schemas")
            print(f"2. Login with supabase account + password: yRPHDq9MaQt6JIDl3kSkoR2E")
            print(f"3. Go to SQL Editor")
            print(f"4. Run the script: create_supabase_schema.sql")
            print(f"5. Verify all 4 tables are created")
            print(f"6. Re-run this test to check connection")
            print(f"7. If still failing, we'll investigate connection method")

        elif status['method'] == 'postgresql' and not status.get('schema_status', {}).get('schema_ready'):
            print(f"1. PostgreSQL connected but schema incomplete")
            print(f"2. Run create_supabase_schema.sql to create missing tables")
            print(f"3. Re-test connection")

        else:
            print(f"1. Database connection working!")
            print(f"2. Ready to run Phase 1 extraction with real database")
            print(f"3. Test with: python test_phase1_final.py")

        return status

    except Exception as e:
        print(f"CONNECTION TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        await supabase_client_v2.close()


async def demonstrate_phase1_readiness():
    """Show what Phase 1 extraction will look like with real database"""

    print(f"\nPHASE 1 EXTRACTION READINESS")
    print(f"=" * 30)

    # Test basic operations that Phase 1 will use
    try:
        status = await supabase_client_v2.initialize()

        if status['method'] != 'local_fallback':
            print(f"TESTING Phase 1 operations...")

            # Test site creation
            site_id = await supabase_client_v2.ensure_site("https://cm-qa-sc103.kajoo.ca")
            print(f"  Site ID: {site_id}")

            # Test scan creation
            scan_id = await supabase_client_v2.create_scan(site_id)
            print(f"  Scan ID: {scan_id}")

            # Test module saving
            module_id = await supabase_client_v2.save_module(
                scan_id=scan_id,
                module="connection-test",
                data_source="test",
                confidence=1.0,
                duration_ms=100,
                result={"test": "success", "timestamp": "2025-09-22"},
                requires_credentials=False
            )
            print(f"  Module ID: {module_id}")

            # Test scan completion
            await supabase_client_v2.finish_scan(scan_id)
            print(f"  Scan completed")

            # Test result retrieval
            results = await supabase_client_v2.get_scan_results(scan_id)
            print(f"  Results retrieved: {len(results)} modules")

            print(f"\nSUCCESS - Real database operations working!")
            print(f"Phase 1 extraction ready to use real database storage")

        else:
            print(f"Database not available - Phase 1 will use local JSON files")
            print(f"This is acceptable for now, but schema creation will enable real database")

    except Exception as e:
        print(f"PHASE 1 READINESS TEST FAILED: {e}")

    finally:
        await supabase_client_v2.close()


if __name__ == "__main__":
    print("Testing Supabase connection and schema readiness...")

    # Run connection test
    asyncio.run(test_connection_strategies())

    print("\n" + "=" * 50)

    # Run Phase 1 readiness test
    asyncio.run(demonstrate_phase1_readiness())