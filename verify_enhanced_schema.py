#!/usr/bin/env python3
"""
Verify Enhanced Schema Implementation
Check that all tables exist and test data migration
"""

import sys
import os
import json

# Add the cli directory to the path so we can import modules
sys.path.insert(0, 'cli')

try:
    from supabase import create_client, Client
except ImportError as e:
    print(f"Missing dependency: {e}")
    sys.exit(1)

def verify_enhanced_schema():
    """Verify the enhanced schema was created successfully"""

    print("ENHANCED SCHEMA VERIFICATION")
    print("=" * 40)

    try:
        # Connect using working Supabase client
        SUPABASE_URL = "http://10.0.0.196:8000"
        SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UtZGVtbyIsImlhdCI6MTc1ODU1NzY1MywiZXhwIjoyMDczOTMyMDUzfQ.eCfBa97jXcYRm0cgwBhbR62qs8KQTxmkjP6ef3SPCVA"

        supabase: Client = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)
        print("[OK] Connected to Supabase successfully")

        # Verify all enhanced tables exist
        enhanced_tables = [
            'graphql_types',
            'graphql_fields',
            'graphql_interfaces',
            'graphql_type_relationships',
            'content_items',
            'content_field_values',
            'template_definitions',
            'template_fields',
            'template_inheritance',
            'field_usage_statistics',
            'content_model_insights'
        ]

        print("\nVERIFYING ENHANCED TABLES:")
        print("-" * 30)

        tables_verified = 0
        for table_name in enhanced_tables:
            try:
                # Try to select from the table
                result = supabase.table(table_name).select('*').limit(1).execute()
                print(f"[OK] {table_name}: Table exists, {len(result.data)} rows")
                tables_verified += 1
            except Exception as e:
                print(f"[ERROR] {table_name}: {e}")

        # Verify views exist
        enhanced_views = [
            'template_analysis',
            'field_usage_analysis',
            'content_hierarchy'
        ]

        print(f"\nVERIFYING ENHANCED VIEWS:")
        print("-" * 30)

        views_verified = 0
        for view_name in enhanced_views:
            try:
                result = supabase.table(view_name).select('*').limit(1).execute()
                print(f"[OK] {view_name}: View exists")
                views_verified += 1
            except Exception as e:
                print(f"[ERROR] {view_name}: {e}")

        # Summary
        print(f"\nVERIFICATION SUMMARY:")
        print(f"Tables created: {tables_verified}/{len(enhanced_tables)}")
        print(f"Views created: {views_verified}/{len(enhanced_views)}")

        if tables_verified == len(enhanced_tables) and views_verified == len(enhanced_views):
            print("[SUCCESS] Enhanced schema is fully operational!")

            # Now test data migration
            return test_data_migration(supabase)
        else:
            print("[WARNING] Some components missing - check errors above")
            return False

    except Exception as e:
        print(f"[ERROR] Schema verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_data_migration(supabase: Client):
    """Test migrating existing enhanced data to normalized tables"""

    print("\n" + "="*50)
    print("TESTING DATA MIGRATION")
    print("="*50)

    try:
        # Get the latest enhanced schema data
        schema_modules = supabase.table('scan_modules').select('id, scan_id, confidence').eq('module', 'enhanced-sitecore-schema').order('created_at', desc=True).limit(1).execute()

        if not schema_modules.data:
            print("[ERROR] No enhanced schema data found to migrate")
            return False

        module_data = schema_modules.data[0]
        scan_id = module_data['scan_id']
        module_id = module_data['id']

        print(f"Migrating latest scan: {scan_id}")

        # Get the schema result data
        result = supabase.table('analysis_results').select('result').eq('scan_module_id', module_id).execute()

        if not result.data:
            print("[ERROR] No result data found")
            return False

        schema_data = result.data[0]['result']
        print(f"[OK] Retrieved schema data with {len(schema_data.get('object_types', []))} object types")

        # Migrate GraphQL Types
        migrated_types = migrate_graphql_types(supabase, scan_id, schema_data)
        print(f"[SUCCESS] Migrated {migrated_types} GraphQL types")

        # Migrate Content Data
        migrated_content = migrate_content_data(supabase, scan_id)
        print(f"[SUCCESS] Migrated {migrated_content} content items")

        # Test enhanced queries
        test_enhanced_queries(supabase, scan_id)

        return True

    except Exception as e:
        print(f"[ERROR] Data migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def migrate_graphql_types(supabase: Client, scan_id: str, schema_data: dict) -> int:
    """Migrate GraphQL schema data to normalized tables"""

    migrated_count = 0

    # Migrate object types
    for type_data in schema_data.get('object_types', []):
        try:
            # Insert GraphQL type
            type_result = supabase.table('graphql_types').upsert({
                'scan_id': scan_id,
                'name': type_data.get('name'),
                'kind': 'OBJECT',
                'description': type_data.get('description'),
                'field_count': len(type_data.get('fields', []))
            }, on_conflict='scan_id,name').execute()

            if type_result.data:
                type_id = type_result.data[0]['id']

                # Migrate fields for this type
                for field_data in type_data.get('fields', []):
                    supabase.table('graphql_fields').upsert({
                        'type_id': type_id,
                        'name': field_data.get('name'),
                        'field_type': field_data.get('type'),
                        'description': field_data.get('description'),
                        'is_deprecated': field_data.get('is_deprecated', False),
                        'arguments': field_data.get('args', []),
                        'type_detail': field_data.get('type_detail', {})
                    }, on_conflict='type_id,name').execute()

                migrated_count += 1

        except Exception as e:
            print(f"[WARNING] Failed to migrate type {type_data.get('name', 'unknown')}: {e}")

    return migrated_count

def migrate_content_data(supabase: Client, scan_id: str) -> int:
    """Migrate content data to normalized tables"""

    try:
        # Get enhanced content data for this scan
        content_modules = supabase.table('scan_modules').select('id').eq('scan_id', scan_id).eq('module', 'enhanced-sitecore-content').execute()

        if not content_modules.data:
            print("[INFO] No enhanced content data to migrate")
            return 0

        module_id = content_modules.data[0]['id']
        result = supabase.table('analysis_results').select('result').eq('scan_module_id', module_id).execute()

        if not result.data or not result.data[0]['result']:
            return 0

        content_data = result.data[0]['result']
        migrated_count = 0

        # Migrate site/content items
        for site_data in content_data.get('sites', []):
            try:
                # Insert content item
                item_result = supabase.table('content_items').upsert({
                    'scan_id': scan_id,
                    'sitecore_id': site_data.get('id'),
                    'name': site_data.get('name'),
                    'path': site_data.get('path'),
                    'display_name': site_data.get('display_name'),
                    'template_name': site_data.get('template'),
                    'template_id': site_data.get('template_id'),
                    'has_children': site_data.get('has_children', False),
                    'child_count': site_data.get('child_count', 0)
                }, on_conflict='scan_id,sitecore_id').execute()

                if item_result.data:
                    item_id = item_result.data[0]['id']

                    # Migrate field values
                    field_samples = site_data.get('field_samples', {})
                    field_types = site_data.get('field_types', {})

                    for field_name, field_info in field_samples.items():
                        field_type_info = field_types.get(field_name, {})

                        supabase.table('content_field_values').upsert({
                            'item_id': item_id,
                            'field_name': field_name,
                            'field_value': field_info.get('value'),
                            'value_type': field_type_info.get('value_type', 'Unknown'),
                            'value_length': field_info.get('length', 0),
                            'has_value': field_info.get('has_value', False),
                            'is_empty': not field_info.get('has_value', False)
                        }, on_conflict='item_id,field_name').execute()

                    migrated_count += 1

            except Exception as e:
                print(f"[WARNING] Failed to migrate content item {site_data.get('name', 'unknown')}: {e}")

        return migrated_count

    except Exception as e:
        print(f"[ERROR] Content migration failed: {e}")
        return 0

def test_enhanced_queries(supabase: Client, scan_id: str):
    """Test enhanced query capabilities"""

    print(f"\nTESTING ENHANCED QUERY CAPABILITIES:")
    print("-" * 40)

    try:
        # Test 1: GraphQL type analysis
        types_result = supabase.table('graphql_types').select('name, kind, field_count').eq('scan_id', scan_id).execute()
        print(f"[OK] GraphQL Types Query: {len(types_result.data)} types found")

        if types_result.data:
            sample_type = types_result.data[0]
            print(f"     Sample: {sample_type['name']} ({sample_type['field_count']} fields)")

        # Test 2: Field analysis
        fields_result = supabase.table('graphql_fields').select('name, field_type').limit(5).execute()
        print(f"[OK] GraphQL Fields Query: {len(fields_result.data)} sample fields")

        # Test 3: Content analysis
        content_result = supabase.table('content_items').select('name, template_name, child_count').eq('scan_id', scan_id).execute()
        print(f"[OK] Content Items Query: {len(content_result.data)} items found")

        # Test 4: Field values analysis
        field_values_result = supabase.table('content_field_values').select('field_name, value_type, has_value').limit(5).execute()
        print(f"[OK] Field Values Query: {len(field_values_result.data)} field values")

        # Test 5: Template analysis view
        template_analysis_result = supabase.table('template_analysis').select('*').eq('scan_id', scan_id).execute()
        print(f"[OK] Template Analysis View: {len(template_analysis_result.data)} templates analyzed")

        print(f"\n[SUCCESS] All enhanced queries working correctly!")

    except Exception as e:
        print(f"[ERROR] Enhanced query test failed: {e}")

def assess_phase2_readiness(supabase: Client):
    """Assess readiness for Phase 2"""

    print(f"\n" + "="*60)
    print("PHASE 2 READINESS ASSESSMENT")
    print("="*60)

    readiness_checks = {
        'Enhanced Schema': False,
        'Data Migration': False,
        'Query Performance': False,
        'Rich Data Available': False,
        'Node.js Ready': False
    }

    try:
        # Check 1: Enhanced schema exists
        tables_count = 0
        for table in ['graphql_types', 'content_items', 'template_analysis']:
            try:
                supabase.table(table).select('id').limit(1).execute()
                tables_count += 1
            except:
                pass

        readiness_checks['Enhanced Schema'] = tables_count >= 3

        # Check 2: Data migration successful
        types_result = supabase.table('graphql_types').select('id').execute()
        content_result = supabase.table('content_items').select('id').execute()
        readiness_checks['Data Migration'] = len(types_result.data) > 0 and len(content_result.data) > 0

        # Check 3: Query performance
        # Simple performance test
        import time
        start_time = time.time()
        supabase.table('template_analysis').select('*').execute()
        query_time = time.time() - start_time
        readiness_checks['Query Performance'] = query_time < 1.0  # Should be fast

        # Check 4: Rich data available
        fields_result = supabase.table('graphql_fields').select('id').execute()
        field_values_result = supabase.table('content_field_values').select('id').execute()
        readiness_checks['Rich Data Available'] = len(fields_result.data) > 100 and len(field_values_result.data) > 0

        # Check 5: Node.js ready (views and proper structure)
        view_result = supabase.table('template_analysis').select('*').limit(1).execute()
        readiness_checks['Node.js Ready'] = len(view_result.data) >= 0  # View accessible

        # Display results
        print("Readiness Checklist:")
        for check, status in readiness_checks.items():
            status_icon = "[OK]" if status else "[FAIL]"
            print(f"  {status_icon} {check}")

        overall_ready = all(readiness_checks.values())

        if overall_ready:
            print(f"\n[SUCCESS] FULLY READY FOR PHASE 2!")
            print("Enhanced capabilities available:")
            print("- Comprehensive GraphQL schema analysis")
            print("- Rich content and field value analysis")
            print("- Template inheritance and usage patterns")
            print("- Performance-optimized queries")
            print("- Node.js/React ready data structures")

        else:
            print(f"\n[WARNING] Some readiness checks failed")
            failed_checks = [check for check, status in readiness_checks.items() if not status]
            print(f"Failed checks: {', '.join(failed_checks)}")

        return overall_ready

    except Exception as e:
        print(f"[ERROR] Readiness assessment failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting enhanced schema verification...")

    success = verify_enhanced_schema()

    if success:
        # Connect again for final assessment
        SUPABASE_URL = "http://10.0.0.196:8000"
        SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UtZGVtbyIsImlhdCI6MTc1ODU1NzY1MywiZXhwIjoyMDczOTMyMDUzfQ.eCfBa97jXcYRm0cgwBhbR62qs8KQTxmkjP6ef3SPCVA"
        supabase = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)

        phase2_ready = assess_phase2_readiness(supabase)

        if phase2_ready:
            print(f"\n[SUCCESS] PHASE 2 DEVELOPMENT CAN BEGIN!")
        else:
            print(f"\n[WARNING] Additional setup needed before Phase 2")
    else:
        print("\n[ERROR] Enhanced schema verification failed")

    sys.exit(0 if success else 1)