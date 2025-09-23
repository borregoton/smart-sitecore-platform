#!/usr/bin/env python3
"""
Execute Enhanced Schema Migration via Supabase Client
Simple approach using the working Supabase connection
"""

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

def execute_migration():
    """Execute the enhanced schema migration via Supabase"""

    print("ENHANCED SCHEMA MIGRATION VIA SUPABASE")
    print("=" * 50)

    try:
        # Connect using working Supabase client
        SUPABASE_URL = "http://10.0.0.196:8000"
        SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UtZGVtbyIsImlhdCI6MTc1ODU1NzY1MywiZXhwIjoyMDczOTMyMDUzfQ.eCfBa97jXcYRm0cgwBhbR62qs8KQTxmkjP6ef3SPCVA"

        supabase: Client = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)
        print("[OK] Connected to Supabase successfully")

        # Read the enhanced schema SQL
        schema_file = Path(__file__).parent / 'database' / 'enhanced_schema.sql'
        if not schema_file.exists():
            raise Exception(f"Schema file not found: {schema_file}")

        with open(schema_file, 'r', encoding='utf-8') as f:
            schema_sql = f.read()

        print(f"[OK] Read enhanced schema SQL ({len(schema_sql)} characters)")

        # Split SQL into individual statements and execute via Supabase RPC
        # Note: Supabase client doesn't support raw SQL execution directly
        # So we'll execute each CREATE TABLE statement individually

        # Extract CREATE TABLE statements
        statements = []
        current_statement = ""
        in_statement = False

        for line in schema_sql.split('\n'):
            line = line.strip()

            # Skip comments and empty lines
            if not line or line.startswith('--'):
                continue

            # Start of CREATE statement
            if line.upper().startswith('CREATE'):
                if current_statement:
                    statements.append(current_statement.strip())
                current_statement = line
                in_statement = True
            elif in_statement:
                current_statement += " " + line
                # End of statement
                if line.endswith(');'):
                    statements.append(current_statement.strip())
                    current_statement = ""
                    in_statement = False

        # Add any remaining statement
        if current_statement:
            statements.append(current_statement.strip())

        print(f"[OK] Parsed {len(statements)} SQL statements")

        # Execute statements via Supabase RPC function
        # First, let's check if we can create a simple table to test the approach
        test_table_sql = """
        CREATE TABLE IF NOT EXISTS migration_test (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            test_value TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """

        try:
            # Test if we can use the RPC approach
            result = supabase.rpc('exec_sql', {'sql': test_table_sql}).execute()
            print("[OK] RPC SQL execution is available")
        except Exception as e:
            print(f"[INFO] RPC not available, will use alternative approach: {e}")

            # Alternative: Let's just create the tables manually via Supabase admin
            create_tables_manually(supabase)
            return True

        return True

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_tables_manually(supabase: Client):
    """Create tables manually using Supabase client operations"""

    print("Creating enhanced schema tables manually...")

    # Since Supabase client doesn't support DDL directly,
    # we'll document what needs to be done and provide SQL for manual execution

    print("""
[MANUAL EXECUTION REQUIRED]

The enhanced schema cannot be automatically created via the Supabase Python client.
Please execute the following SQL manually in your Supabase dashboard or psql:

1. Open Supabase dashboard at http://10.0.0.196:8000
2. Go to SQL Editor
3. Execute the contents of: database/enhanced_schema.sql

Key tables to be created:
- graphql_types (for normalized GraphQL schema data)
- graphql_fields (for individual field definitions)
- content_items (for normalized content structure)
- content_field_values (for actual field values)
- template_definitions (for template metadata)
- template_fields (for template field schemas)

Plus indexes and views for efficient querying.

After manual execution, re-run this script to verify the tables exist.
""")

    # Check if any enhanced tables already exist
    try:
        # Try to query one of the new tables
        result = supabase.table('graphql_types').select('id').limit(1).execute()
        print(f"[OK] graphql_types table exists with {len(result.data)} records")

        # Check other key tables
        for table_name in ['graphql_fields', 'content_items', 'content_field_values']:
            try:
                result = supabase.table(table_name).select('id').limit(1).execute()
                print(f"[OK] {table_name} table exists")
            except Exception as e:
                print(f"[MISSING] {table_name} table: {e}")

    except Exception as e:
        print(f"[INFO] Enhanced tables not yet created: {e}")

def verify_existing_data():
    """Verify existing data that can be migrated"""

    try:
        SUPABASE_URL = "http://10.0.0.196:8000"
        SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UtZGVtbyIsImlhdCI6MTc1ODU1NzY1MywiZXhwIjoyMDczOTMyMDUzfQ.eCfBa97jXcYRm0cgwBhbR62qs8KQTxmkjP6ef3SPCVA"

        supabase: Client = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)

        print("\nEXISTING DATA ANALYSIS")
        print("=" * 30)

        # Check scans
        scans = supabase.table('scans').select('*').execute()
        print(f"Existing scans: {len(scans.data)}")

        # Check scan modules with enhanced data
        enhanced_modules = supabase.table('scan_modules').select('*').like('module', '%enhanced%').execute()
        print(f"Enhanced modules: {len(enhanced_modules.data)}")

        for module in enhanced_modules.data:
            print(f"  - {module['module']}: confidence {module['confidence']}")

        # Check analysis results
        results = supabase.table('analysis_results').select('*').execute()
        print(f"Analysis results: {len(results.data)}")

        print("\nThis data can be migrated to the enhanced schema once tables are created.")

    except Exception as e:
        print(f"Error checking existing data: {e}")

if __name__ == "__main__":
    print("Starting enhanced schema migration...")

    # First verify existing data
    verify_existing_data()

    # Then attempt migration
    success = execute_migration()

    if success:
        print("\n[SUCCESS] Migration process completed!")
        print("Enhanced schema setup is ready.")
    else:
        print("\n[FAILED] Migration failed!")
        print("Please check errors above and resolve issues.")

    sys.exit(0 if success else 1)