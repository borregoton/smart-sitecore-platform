#!/usr/bin/env python3
"""
Test Enhanced Phase 1 Extraction
Test the new comprehensive data extraction capabilities
"""

import asyncio
import sys
import os

# Add the cli directory to the path so we can import modules
sys.path.insert(0, 'cli')

from smart_sitecore.enhanced_phase1_extractor import run_enhanced_phase1_extraction


async def test_enhanced_extraction():
    """Test the enhanced Phase 1 extraction"""

    print("TESTING ENHANCED PHASE 1 EXTRACTION")
    print("=" * 40)

    # Known working Sitecore endpoint
    sitecore_url = "https://cm-qa-sc103.kajoo.ca"
    api_key = "{34B8FFF8-8F50-4C41-95A8-D2A9304EBD52}"

    try:
        print(f"Running enhanced extraction on: {sitecore_url}")

        # Run enhanced Phase 1 extraction
        scan_id = await run_enhanced_phase1_extraction(sitecore_url, api_key)

        print(f"\\n[SUCCESS] Enhanced extraction completed!")
        print(f"Scan ID: {scan_id}")

        # Compare with previous extraction
        await compare_extraction_results(scan_id)

        return True

    except Exception as e:
        print(f"\\n[ERROR] Enhanced extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def compare_extraction_results(scan_id: str):
    """Compare enhanced extraction results with previous ones"""

    print(f"\\n" + "="*50)
    print(f"ENHANCED EXTRACTION ANALYSIS")
    print(f"="*50)

    try:
        from supabase import create_client, Client

        # Working credentials
        SUPABASE_URL = "http://10.0.0.196:8000"
        SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UtZGVtbyIsImlhdCI6MTc1ODU1NzY1MywiZXhwIjoyMDczOTMyMDUzfQ.eCfBa97jXcYRm0cgwBhbR62qs8KQTxmkjP6ef3SPCVA"

        supabase_admin: Client = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)

        # Get enhanced scan modules
        enhanced_modules = supabase_admin.table('scan_modules').select('*').eq('scan_id', scan_id).execute()

        print(f"Enhanced scan modules: {len(enhanced_modules.data)}")

        for module in enhanced_modules.data:
            module_name = module['module']
            confidence = module['confidence']
            duration = module['duration_ms']

            print(f"\\n[{module_name.upper()}]")
            print(f"  Confidence: {confidence}")
            print(f"  Duration: {duration}ms")

            # Get detailed results
            results = supabase_admin.table('analysis_results').select('result').eq('scan_module_id', module['id']).execute()

            if results.data and len(results.data) > 0:
                result_data = results.data[0]['result']

                if 'enhanced-sitecore-schema' in module_name:
                    await analyze_enhanced_schema_results(result_data)

    except Exception as e:
        print(f"[ERROR] Comparison failed: {e}")


async def analyze_enhanced_schema_results(schema_data):
    """Analyze the enhanced schema extraction results"""

    if not schema_data:
        print(f"  [ERROR] No schema data found")
        return

    print(f"  Enhanced Schema Analysis:")

    # Basic stats
    total_types = schema_data.get('total_types', 0)
    object_types = schema_data.get('object_types', [])
    enum_types = schema_data.get('enum_types', [])
    query_fields = schema_data.get('query_fields', [])

    print(f"    Total GraphQL types: {total_types}")
    print(f"    Object types captured: {len(object_types)}")
    print(f"    Enum types captured: {len(enum_types)}")
    print(f"    Query fields captured: {len(query_fields)}")

    # Enhanced stats
    if 'schema_statistics' in schema_data:
        stats = schema_data['schema_statistics']
        print(f"    Interface types: {stats.get('interface_count', 0)}")
        print(f"    Union types: {stats.get('union_count', 0)}")
        print(f"    Total field definitions: {stats.get('total_fields', 0)}")
        print(f"    Avg fields per type: {stats.get('avg_fields_per_type', 0):.1f}")

    # Coverage comparison
    if object_types and total_types > 0:
        coverage = (len(object_types) / total_types) * 100
        print(f"    Schema coverage: {coverage:.1f}%")

        if coverage > 80:
            print(f"    [SUCCESS] Excellent schema coverage!")
        elif coverage > 50:
            print(f"    [GOOD] Good schema coverage")
        else:
            print(f"    [WARNING] Limited schema coverage")

    # Field definition analysis
    if object_types and len(object_types) > 0:
        sample_type = object_types[0]
        fields = sample_type.get('fields', [])

        print(f"    Sample type: {sample_type.get('name')}")
        print(f"    Sample field count: {len(fields)}")

        if fields and len(fields) > 0:
            sample_field = fields[0]
            print(f"    Sample field structure: {list(sample_field.keys())}")

            has_type_details = 'type_detail' in sample_field
            has_args = 'args' in sample_field

            print(f"    Field type details captured: {has_type_details}")
            print(f"    Field arguments captured: {has_args}")

            if has_type_details and has_args:
                print(f"    [SUCCESS] Comprehensive field extraction working!")
            else:
                print(f"    [WARNING] Field extraction may be incomplete")

    # Relationship analysis
    relationships = schema_data.get('type_relationships', {})
    print(f"    Type relationships: {len(relationships)}")

    if relationships:
        print(f"    [SUCCESS] Type relationship mapping captured")
    else:
        print(f"    [INFO] No type relationships found")


if __name__ == "__main__":
    print("Starting enhanced Phase 1 extraction test...")
    success = asyncio.run(test_enhanced_extraction())

    if success:
        print(f"\\n[SUCCESS] Enhanced extraction test completed successfully!")
    else:
        print(f"\\n[FAILED] Enhanced extraction test failed!")

    sys.exit(0 if success else 1)