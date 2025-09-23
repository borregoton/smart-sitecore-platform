#!/usr/bin/env python3
"""
Test Specific Database Credentials
Test each credential set individually with detailed error reporting
"""

import asyncio
import sys
import os
from datetime import datetime

try:
    import asyncpg
except ImportError:
    print("[ERROR] asyncpg not installed")
    print("Run: python launch.py --setup-only")
    sys.exit(1)


async def test_credential_set(name, user, password, database="postgres"):
    """Test a specific set of credentials"""

    print(f"\nTesting {name} credentials:")
    print(f"  User: {user}")
    print(f"  Password: {password[:8]}...")
    print(f"  Database: {database}")

    try:
        # Test connection with 15 second timeout
        print(f"  Attempting connection...")

        conn = await asyncio.wait_for(
            asyncpg.connect(
                host="10.0.0.196",
                port=5432,
                database=database,
                user=user,
                password=password
            ),
            timeout=15.0
        )

        print(f"  [SUCCESS] Connected successfully!")

        # Test basic query
        try:
            version = await conn.fetchval("SELECT version()")
            print(f"  [SUCCESS] Query test passed")
            print(f"  PostgreSQL: {version.split()[0]} {version.split()[1]}")

            # Test table listing
            tables = await conn.fetch("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)

            table_names = [row['tablename'] for row in tables]
            print(f"  [SUCCESS] Found {len(table_names)} tables")

            # Show some table names
            if table_names:
                print(f"  Sample tables: {', '.join(table_names[:5])}")
                if len(table_names) > 5:
                    print(f"                 ... and {len(table_names) - 5} more")

            await conn.close()
            return True

        except Exception as query_error:
            print(f"  [ERROR] Query failed: {query_error}")
            await conn.close()
            return False

    except asyncio.TimeoutError:
        print(f"  [TIMEOUT] Connection timed out after 15 seconds")
        return False

    except Exception as e:
        error_msg = str(e)
        print(f"  [FAILED] Connection failed: {error_msg}")

        # Provide specific guidance based on error type
        if "authentication failed" in error_msg.lower():
            print(f"  → Wrong username or password")
        elif "database" in error_msg.lower() and "does not exist" in error_msg.lower():
            print(f"  → Database '{database}' doesn't exist")
        elif "connection refused" in error_msg.lower():
            print(f"  → Database server not accepting connections")
        elif "timeout" in error_msg.lower():
            print(f"  → Network timeout or server overloaded")
        else:
            print(f"  → Unknown connection issue")

        return False


async def main():
    """Test all credential combinations"""

    print("SMART SITECORE ANALYSIS PLATFORM - V2.0")
    print("Detailed Credential Testing")
    print("=" * 55)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target: 10.0.0.196:5432")
    print()

    # Test credentials including tenant-based usernames
    tenant_id = "zyafowjs5i4ltxxq"

    credentials_to_test = [
        # Original format
        {
            'name': 'supabase_original',
            'user': 'supabase',
            'password': 'yRPHDq9MaQt6JIDl3kSkoR2E',
            'database': 'postgres'
        },
        {
            'name': 'postgres_original',
            'user': 'postgres',
            'password': 'boTW1PbupfnkXRdlXr1RFdL7qqyi43wm',
            'database': 'postgres'
        },
        # Tenant-based format (your suggestion)
        {
            'name': 'postgres_with_tenant',
            'user': f'postgres.{tenant_id}',
            'password': 'boTW1PbupfnkXRdlXr1RFdL7qqyi43wm',
            'database': 'postgres'
        },
        {
            'name': 'supabase_with_tenant',
            'user': f'supabase.{tenant_id}',
            'password': 'yRPHDq9MaQt6JIDl3kSkoR2E',
            'database': 'postgres'
        },
        # Try with different database names
        {
            'name': 'postgres_tenant_on_supabase_db',
            'user': f'postgres.{tenant_id}',
            'password': 'boTW1PbupfnkXRdlXr1RFdL7qqyi43wm',
            'database': 'supabase'
        },
        {
            'name': 'postgres_tenant_on_tenant_db',
            'user': f'postgres.{tenant_id}',
            'password': 'boTW1PbupfnkXRdlXr1RFdL7qqyi43wm',
            'database': tenant_id
        }
    ]

    successful_credentials = []

    for creds in credentials_to_test:
        success = await test_credential_set(
            creds['name'],
            creds['user'],
            creds['password'],
            creds['database']
        )

        if success:
            successful_credentials.append(creds)

    # Summary
    print("\n" + "=" * 55)
    print("CREDENTIAL TEST SUMMARY")
    print("=" * 55)

    if successful_credentials:
        print(f"[SUCCESS] Found {len(successful_credentials)} working credential(s)!")
        print()

        for creds in successful_credentials:
            print(f"✓ {creds['name']}: {creds['user']}@{creds['database']}")

        print()
        print("RECOMMENDED NEXT STEPS:")

        # Pick the best credential
        best_cred = successful_credentials[0]
        print(f"1. Use '{best_cred['name']}' credentials for v2.0 extraction")
        print(f"2. Update cli/smart_sitecore/supabase_client_v2.py if needed")
        print(f"3. Run: python launch.py GrabSiteCoreData")

    else:
        print("[FAILED] No working credentials found!")
        print()
        print("POSSIBLE ISSUES:")
        print("- Passwords have been changed since these were recorded")
        print("- Database users have been disabled")
        print("- Authentication method changed (e.g., key-based instead of password)")
        print("- Database access restricted to specific IP ranges")
        print()
        print("RECOMMENDED ACTIONS:")
        print("1. Contact database administrator for current credentials")
        print("2. Verify these users still exist in the database")
        print("3. Check if IP 10.0.0.196 is still the correct database server")
        print("4. Confirm Supabase instance is running and accessible")

    print("=" * 55)
    return len(successful_credentials) > 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)