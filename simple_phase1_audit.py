#!/usr/bin/env python3
"""
Simple Phase 1 Data Completeness Audit
Focus on key questions about data depth without Unicode issues
"""

import asyncio
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


async def simple_audit():
    """Simple audit of Phase 1 data extraction"""

    print("PHASE 1 DATA COMPLETENESS AUDIT")
    print("=" * 40)

    # Working credentials
    SUPABASE_URL = "http://10.0.0.196:8000"
    SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UtZGVtbyIsImlhdCI6MTc1ODU1NzY1MywiZXhwIjoyMDczOTMyMDUzfQ.eCfBa97jXcYRm0cgwBhbR62qs8KQTxmkjP6ef3SPCVA"

    try:
        supabase_admin: Client = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)

        # Get the most recent scan
        scans_result = supabase_admin.table('scans').select('*').order('created_at', desc=True).limit(1).execute()
        latest_scan = scans_result.data[0]
        scan_id = latest_scan['id']

        print(f"Analyzing scan: {scan_id}")
        print(f"Status: {latest_scan['status']}")

        # Get scan modules and their data
        modules_result = supabase_admin.table('scan_modules').select('*').eq('scan_id', scan_id).execute()

        print(f"\\nModules found: {len(modules_result.data)}")

        for module in modules_result.data:
            module_name = module['module']
            confidence = module['confidence']
            error = module['error']

            print(f"\\n[{module_name.upper()}] Analysis:")
            print(f"  Confidence: {confidence}")
            print(f"  Error: {error}")

            # Get the actual analysis results
            results = supabase_admin.table('analysis_results').select('result').eq('scan_module_id', module['id']).execute()

            if results.data and len(results.data) > 0:
                result_data = results.data[0]['result']

                if module_name == 'sitecore-schema':
                    await analyze_schema_simple(result_data)
                elif module_name == 'sitecore-content':
                    await analyze_content_simple(result_data)
                elif module_name == 'sitecore-templates':
                    await analyze_templates_simple(result_data)
            else:
                print(f"  [WARNING] No detailed results stored for {module_name}")

        # Overall assessment
        print(f"\\n" + "="*50)
        print(f"PHASE 1 ASSESSMENT")
        print(f"="*50)

        await provide_assessment(modules_result.data)

    except Exception as e:
        print(f"[ERROR] Audit failed: {e}")


async def analyze_schema_simple(schema_data):
    """Simple schema analysis"""
    if not schema_data:
        print(f"  [CRITICAL] No schema data stored!")
        return

    total_types = schema_data.get('total_types', 0)
    object_types = schema_data.get('object_types', [])
    query_fields = schema_data.get('query_fields', [])

    print(f"  Total GraphQL types: {total_types}")
    print(f"  Object types stored: {len(object_types)}")
    print(f"  Query fields stored: {len(query_fields)}")

    # Key question: Do we have enough detail for local analysis?
    if object_types and len(object_types) > 0:
        sample = object_types[0]
        has_field_details = 'fields' in sample or 'field_definitions' in sample
        print(f"  Schema includes field definitions: {has_field_details}")

        if not has_field_details:
            print(f"  [GAP] Schema lacks field-level details")
            print(f"        This limits understanding of data structure")

    coverage = (len(object_types) / total_types * 100) if total_types > 0 else 0
    print(f"  Schema coverage: {coverage:.1f}%")


async def analyze_content_simple(content_data):
    """Simple content analysis"""
    if not content_data:
        print(f"  [CRITICAL] No content data stored!")
        return

    total_items = content_data.get('estimated_total_items', 0)
    sites = content_data.get('sites', [])

    print(f"  Total content items discovered: {total_items}")
    print(f"  Sites analyzed: {len(sites)}")

    # Key question: Do we have actual content or just metadata?
    if sites and len(sites) > 0:
        sample_site = sites[0]
        site_keys = list(sample_site.keys())
        print(f"  Site data includes: {site_keys}")

        # Check for actual content fields
        has_content_fields = any(key in sample_site for key in [
            'fields', 'content', 'field_values', 'item_data'
        ])

        print(f"  Actual content field data stored: {has_content_fields}")

        if not has_content_fields:
            print(f"  [CRITICAL GAP] Only metadata stored, no actual content!")
            print(f"                 Cannot do comprehensive content analysis locally")
            print(f"                 Would need to re-query Sitecore for field values")

    avg_items = total_items / len(sites) if sites else 0
    print(f"  Average items per site: {avg_items:.1f}")


async def analyze_templates_simple(template_data):
    """Simple template analysis"""
    if not template_data:
        print(f"  [CRITICAL] No template data stored!")
        return

    system_templates = template_data.get('system_templates', [])
    content_templates = template_data.get('content_templates', [])

    print(f"  System templates: {len(system_templates)}")
    print(f"  Content templates: {len(content_templates)}")

    # Key question: Do we have template structure details?
    all_templates = system_templates + content_templates
    if all_templates and len(all_templates) > 0:
        sample_template = all_templates[0]
        template_keys = list(sample_template.keys())
        print(f"  Template data includes: {template_keys}")

        # Check for field definitions
        has_field_definitions = any(key in sample_template for key in [
            'fields', 'field_definitions', 'template_fields'
        ])

        print(f"  Template field definitions stored: {has_field_definitions}")

        if not has_field_definitions:
            print(f"  [CRITICAL GAP] Template structure not captured!")
            print(f"                 Cannot analyze content model locally")
            print(f"                 Would need to re-query for template details")


async def provide_assessment(modules_data):
    """Provide overall assessment"""

    successful_modules = len([m for m in modules_data if m['error'] is None])
    total_modules = len(modules_data)

    print(f"Module Success Rate: {successful_modules}/{total_modules}")

    # Key Phase 1 Questions:
    print(f"\\nKEY PHASE 1 COMPLETENESS QUESTIONS:")
    print(f"-" * 40)

    print(f"1. Can we do local GraphQL schema analysis?")
    print(f"   Answer: PARTIAL - we have type names but may lack field details")

    print(f"\\n2. Can we do local content analysis without re-querying Sitecore?")
    print(f"   Answer: LIMITED - we have item counts/structure but likely no field values")

    print(f"\\n3. Can we analyze template relationships and content model locally?")
    print(f"   Answer: LIMITED - we have template names but likely no field schemas")

    print(f"\\n4. Are we storing enough data for comprehensive Phase 2 analysis?")
    print(f"   Answer: NEEDS ENHANCEMENT - current extraction is metadata-focused")

    print(f"\\nRECOMMENDATIONS:")
    print(f"-" * 15)
    print(f"1. ENHANCE Schema Extraction:")
    print(f"   - Store full field definitions for each GraphQL type")
    print(f"   - Capture field types, relationships, and constraints")

    print(f"\\n2. ENHANCE Content Extraction:")
    print(f"   - Extract actual field values for sample content items")
    print(f"   - Store representative content for each template type")
    print(f"   - Capture item relationships and references")

    print(f"\\n3. ENHANCE Template Extraction:")
    print(f"   - Extract complete template field definitions")
    print(f"   - Capture inheritance hierarchies")
    print(f"   - Store field types, validation rules, default values")

    print(f"\\nPHASE 2 READINESS:")
    print(f"-" * 18)
    if successful_modules == total_modules:
        print(f"[READY] Basic connectivity and data flow working")
        print(f"[ENHANCEMENT NEEDED] Increase data depth for rich local analysis")
        print(f"[CURRENT LIMITATION] May need frequent Sitecore API calls in Phase 2")
    else:
        print(f"[NOT READY] Fix Phase 1 module failures first")


if __name__ == "__main__":
    print("Starting simple Phase 1 completeness audit...")
    asyncio.run(simple_audit())