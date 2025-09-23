#!/usr/bin/env python3
"""
Test Supabase Connection with Correct Credentials
Testing both postgres and supabase user credentials
"""

import asyncio
import asyncpg
from datetime import datetime


async def test_connection_variants():
    """Test different connection approaches to 10.0.0.196"""

    host = "10.0.0.196"
    port = 5432

    # Connection variants to test
    variants = [
        {
            "name": "Supabase User",
            "user": "supabase",
            "password": "yRPHDq9MaQt6JIDl3kSkoR2E",
            "database": "postgres"
        },
        {
            "name": "Postgres User",
            "user": "postgres",
            "password": "boTW1PbupfnkXRdlXr1RFdL7qqyi43wm",
            "database": "postgres"
        },
        {
            "name": "Supabase User - Default DB",
            "user": "supabase",
            "password": "yRPHDq9MaQt6JIDl3kSkoR2E",
            "database": "supabase"
        }
    ]

    print("TESTING SUPABASE CONNECTION VARIANTS")
    print("=" * 45)

    for variant in variants:
        print(f"\n[TEST] {variant['name']}")
        print(f"   User: {variant['user']}")
        print(f"   Database: {variant['database']}")

        try:
            # Try to establish connection
            conn = await asyncpg.connect(
                host=host,
                port=port,
                database=variant['database'],
                user=variant['user'],
                password=variant['password'],
                timeout=10
            )

            # Test basic query
            version = await conn.fetchval("SELECT version()")
            current_time = await conn.fetchval("SELECT now()")

            # Test schema access
            tables = await conn.fetch(
                """SELECT schemaname, tablename
                   FROM pg_tables
                   WHERE schemaname IN ('public', 'auth', 'storage', 'supabase')
                   ORDER BY schemaname, tablename"""
            )

            print(f"   SUCCESS - Connected successfully!")
            print(f"   Database Version: {version.split()[0:2]}")
            print(f"   Current Time: {current_time}")
            print(f"   Schemas/Tables Found: {len(tables)}")

            if tables:
                print(f"   Sample Tables:")
                for table in tables[:5]:
                    print(f"     - {table['schemaname']}.{table['tablename']}")
                if len(tables) > 5:
                    print(f"     ... and {len(tables) - 5} more")

            await conn.close()

            # If successful, try creating our schema
            print(f"\n   [SCHEMA TEST] Testing schema creation...")
            return await test_schema_creation(host, port, variant)

        except Exception as e:
            print(f"   FAILED - {e}")
            continue

    print(f"\nALL CONNECTION VARIANTS FAILED")
    return False


async def test_schema_creation(host, port, credentials):
    """Test creating our application schema"""

    try:
        conn = await asyncpg.connect(
            host=host,
            port=port,
            database=credentials['database'],
            user=credentials['user'],
            password=credentials['password'],
            timeout=10
        )

        # Check if our tables already exist
        our_tables = await conn.fetch(
            """SELECT tablename FROM pg_tables
               WHERE schemaname = 'public'
               AND tablename IN ('sites', 'scans', 'scan_modules', 'analysis_results')
               ORDER BY tablename"""
        )

        print(f"   Our tables found: {[t['tablename'] for t in our_tables]}")

        if len(our_tables) == 4:
            print(f"   SCHEMA EXISTS - All 4 tables already created")
            return True

        # Test creating a simple table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS connection_test (
                id SERIAL PRIMARY KEY,
                test_time TIMESTAMPTZ DEFAULT NOW(),
                message TEXT
            )
        """)

        # Test inserting data
        await conn.execute(
            "INSERT INTO connection_test (message) VALUES ($1)",
            f"Test from {credentials['name']} at {datetime.utcnow()}"
        )

        # Test reading data
        result = await conn.fetchval(
            "SELECT COUNT(*) FROM connection_test"
        )

        print(f"   SCHEMA TEST PASSED - Can create tables and insert data")
        print(f"   Test records in connection_test: {result}")

        await conn.close()
        return True

    except Exception as e:
        print(f"   SCHEMA TEST FAILED - {e}")
        return False


if __name__ == "__main__":
    print("Starting Supabase connection test...")
    result = asyncio.run(test_connection_variants())

    if result:
        print(f"\nREADY TO CREATE PRODUCTION SCHEMA")
    else:
        print(f"\nNEED TO RESOLVE CONNECTION ISSUES FIRST")