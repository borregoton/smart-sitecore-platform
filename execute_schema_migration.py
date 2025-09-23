#!/usr/bin/env python3
"""
Execute Enhanced Schema Migration
Execute the database schema enhancement migration safely
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the cli directory to the path so we can import modules
sys.path.insert(0, 'cli')

try:
    from supabase import create_client, Client
except ImportError as e:
    print(f"Missing dependency: {e}")
    sys.exit(1)

# Database configuration (using existing Supabase setup)
SUPABASE_URL = "http://10.0.0.196:8000"
SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UtZGVtbyIsImlhdCI6MTc1ODU1NzY1MywiZXhwIjoyMDczOTMyMDUzfQ.eCfBa97jXcYRm0cgwBhbR62qs8KQTxmkjP6ef3SPCVA"

async def execute_migration():
    """Execute the enhanced schema migration"""

    print("ENHANCED SCHEMA MIGRATION")
    print("=" * 40)

    try:
        # Connect to database (disable SSL for local Supabase)
        print(f"Connecting to database at {DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}...")
        connection = await asyncpg.connect(ssl=False, **DATABASE_CONFIG)

        print("[OK] Connected to database successfully")

        # Read the enhanced schema SQL
        schema_file = Path(__file__).parent / 'database' / 'enhanced_schema.sql'
        if not schema_file.exists():
            raise Exception(f"Schema file not found: {schema_file}")

        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        print(f"[OK] Read enhanced schema SQL ({len(schema_sql)} characters)")

        # Execute the schema creation
        print("Executing enhanced schema creation...")
        await connection.execute(schema_sql)
        print("[SUCCESS] Enhanced schema created successfully")

        # Read and execute migration SQL
        migration_file = Path(__file__).parent / 'database' / 'migrate_to_enhanced_schema.sql'
        if migration_file.exists():
            with open(migration_file, 'r', encoding='utf-8') as f:
                migration_sql = f.read()

            print("Executing data migration...")
            # Note: migration SQL uses \i command which doesn't work with asyncpg
            # So we'll execute the schema parts manually

            # Split SQL by major sections and execute
            sql_parts = migration_sql.split('-- =============================')
            for i, part in enumerate(sql_parts):
                if part.strip() and not part.strip().startswith('-- PRE-MIGRATION CHECKS'):
                    if '\\i enhanced_schema.sql' not in part:
                        try:
                            if part.strip():
                                await connection.execute(part)
                                print(f"[OK] Executed migration part {i+1}")
                        except Exception as e:
                            if "already exists" not in str(e):
                                print(f"[WARNING] Migration part {i+1}: {e}")

        # Verify the migration
        await verify_migration(connection)

        await connection.close()
        print("[SUCCESS] Enhanced schema migration completed!")

        return True

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def verify_migration(connection):
    """Verify the migration was successful"""

    print("\nVerifying migration results...")

    # Check new tables exist
    tables_to_check = [
        'graphql_types',
        'graphql_fields',
        'content_items',
        'content_field_values',
        'template_definitions',
        'template_fields'
    ]

    for table_name in tables_to_check:
        try:
            count = await connection.fetchval(f"SELECT COUNT(*) FROM {table_name}")
            print(f"  {table_name}: {count} rows")
        except Exception as e:
            print(f"  {table_name}: ERROR - {e}")

    # Check views exist
    views_to_check = [
        'template_analysis',
        'field_usage_analysis',
        'content_hierarchy'
    ]

    print("\nChecking views...")
    for view_name in views_to_check:
        try:
            await connection.fetchval(f"SELECT COUNT(*) FROM {view_name} LIMIT 1")
            print(f"  {view_name}: OK")
        except Exception as e:
            print(f"  {view_name}: ERROR - {e}")

if __name__ == "__main__":
    print("Starting enhanced schema migration...")
    success = asyncio.run(execute_migration())

    if success:
        print("\n[SUCCESS] Migration completed successfully!")
        print("Enhanced schema is ready for Phase 2 development.")
    else:
        print("\n[FAILED] Migration failed!")
        print("Please check errors above and resolve issues.")

    sys.exit(0 if success else 1)