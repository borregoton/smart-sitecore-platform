#!/usr/bin/env python3
"""
Create Missing Modules Table
The sites and scans tables exist, but we need to create the modules table
"""

import asyncio
import sys
import os

# Add the cli directory to the path so we can import modules
sys.path.insert(0, 'cli')

try:
    from supabase import create_client, Client
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Make sure you're running in the virtual environment")
    sys.exit(1)


async def create_modules_table():
    """Create the missing modules table"""

    print("CREATING MODULES TABLE")
    print("=" * 25)

    # Provided working credentials
    SUPABASE_URL = "http://10.0.0.196:8000"
    SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UtZGVtbyIsImlhdCI6MTc1ODU1NzY1MywiZXhwIjoyMDczOTMyMDUzfQ.eCfBa97jXcYRm0cgwBhbR62qs8KQTxmkjP6ef3SPCVA"

    print(f"URL: {SUPABASE_URL}")
    print(f"Using SERVICE_ROLE key for admin operations")

    try:
        # Create admin client
        supabase_admin: Client = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)
        print(f"[SUCCESS] Admin client created")

        # Method 1: Try to use the table and let Supabase auto-create it
        print(f"\n[1] Testing if modules table exists...")

        try:
            result = supabase_admin.table('modules').select('*').limit(1).execute()
            print(f"   [SUCCESS] Modules table already exists!")
            return True
        except Exception as e:
            if 'does not exist' in str(e):
                print(f"   [INFO] Modules table doesn't exist, need to create it")
            else:
                print(f"   [ERROR] Unexpected error: {e}")

        # Method 2: Try to create the table by attempting an insert with all required fields
        print(f"\n[2] Creating modules table by structure...")

        # Create a test module record that defines the table structure
        test_module = {
            'scan_id': '00000000-0000-0000-0000-000000000000',  # Test UUID
            'module': 'test-module',
            'data_source': 'test-source',
            'confidence': 1.0,
            'duration_ms': 100,
            'result': {'test': True},
            'requires_credentials': False,
            'error': None
        }

        try:
            result = supabase_admin.table('modules').insert(test_module).execute()
            print(f"   [SUCCESS] Modules table created successfully!")
            print(f"   Test record inserted: {result.data}")

            # Clean up test record
            if result.data and len(result.data) > 0:
                test_id = result.data[0].get('id')
                if test_id:
                    supabase_admin.table('modules').delete().eq('id', test_id).execute()
                    print(f"   [CLEANUP] Test record removed")

            return True

        except Exception as e:
            print(f"   [ERROR] Failed to create modules table: {e}")
            print(f"   This might need to be done via SQL in Supabase dashboard")

        # Method 3: Show SQL that needs to be run manually
        print(f"\n[3] Manual SQL for Supabase dashboard:")
        print(f"   If the above failed, run this SQL in Supabase Studio:")
        print(f"   http://10.0.0.196:8000/project/default/sql")

        sql_statement = """
-- Create modules table
CREATE TABLE IF NOT EXISTS public.modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID REFERENCES public.scans(id),
    module TEXT NOT NULL,
    data_source TEXT NOT NULL,
    confidence DECIMAL(3,2) DEFAULT 0.0,
    duration_ms INTEGER DEFAULT 0,
    result JSONB,
    requires_credentials BOOLEAN DEFAULT FALSE,
    error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_modules_scan_id ON public.modules(scan_id);

-- Grant permissions
GRANT ALL ON public.modules TO anon, authenticated, service_role;
"""

        print(sql_statement)

        return False

    except Exception as e:
        print(f"[ERROR] General failure: {e}")
        return False


async def verify_full_schema():
    """Verify all three tables exist and are accessible"""

    print(f"\n" + "="*40)
    print(f"FULL SCHEMA VERIFICATION")
    print(f"="*40)

    SUPABASE_URL = "http://10.0.0.196:8000"
    SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UtZGVtbyIsImlhdCI6MTc1ODU1NzY1MywiZXhwIjoyMDczOTMyMDUzfQ.eCfBa97jXcYRm0cgwBhbR62qs8KQTxmkjP6ef3SPCVA"

    try:
        supabase_admin: Client = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)

        required_tables = ['sites', 'scans', 'modules']
        working_tables = []

        for table_name in required_tables:
            try:
                result = supabase_admin.table(table_name).select('*').limit(1).execute()
                working_tables.append(table_name)
                print(f"   [OK] {table_name} table exists and accessible")
            except Exception as e:
                print(f"   [FAIL] {table_name} table: {e}")

        print(f"\nSchema Status: {len(working_tables)}/{len(required_tables)} tables ready")

        if len(working_tables) == len(required_tables):
            print(f"[SUCCESS] Full schema is ready for Phase 1 extraction!")
            return True
        else:
            print(f"[ACTION NEEDED] Create missing tables before running extraction")
            return False

    except Exception as e:
        print(f"[ERROR] Schema verification failed: {e}")
        return False


if __name__ == "__main__":
    print("Creating missing modules table...")

    # Create modules table
    modules_created = asyncio.run(create_modules_table())

    # Verify full schema
    schema_ready = asyncio.run(verify_full_schema())

    print(f"\n" + "="*50)
    print(f"MODULES TABLE CREATION SUMMARY")
    print(f"="*50)

    if modules_created:
        print(f"[SUCCESS] Modules table created successfully")
    else:
        print(f"[ACTION NEEDED] Modules table needs manual creation")

    if schema_ready:
        print(f"[SUCCESS] Full database schema is ready!")
        print(f"[NEXT] Update configuration to use real Supabase")
        print(f"[NEXT] Test Phase 1 extraction with real database")
    else:
        print(f"[ACTION NEEDED] Complete schema setup before proceeding")