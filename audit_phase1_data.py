#!/usr/bin/env python3
"""
Audit Phase 1 Data Extraction Completeness
Examine what data we're actually storing and whether it's comprehensive enough
for local analysis without constantly hitting Sitecore APIs
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


async def audit_phase1_data():
    """Audit the completeness of Phase 1 data extraction"""

    print("PHASE 1 DATA EXTRACTION AUDIT")
    print("=" * 40)

    # Working credentials
    SUPABASE_URL = "http://10.0.0.196:8000"
    SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UtZGVtbyIsImlhdCI6MTc1ODU1NzY1MywiZXhwIjoyMDczOTMyMDUzfQ.eCfBa97jXcYRm0cgwBhbR62qs8KQTxmkjP6ef3SPCVA"

    try:
        supabase_admin: Client = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)
        print(f"[SUCCESS] Connected to Supabase")

        # Get the most recent scan
        scans_result = supabase_admin.table('scans').select('*').order('created_at', desc=True).limit(1).execute()

        if not scans_result.data:
            print(f"[ERROR] No scans found")
            return

        latest_scan = scans_result.data[0]
        scan_id = latest_scan['id']
        print(f"\\nAnalyzing latest scan: {scan_id}")
        print(f"Status: {latest_scan['status']}")
        print(f"Created: {latest_scan['created_at']}")

        # Get scan modules
        modules_result = supabase_admin.table('scan_modules').select('*').eq('scan_id', scan_id).execute()
        print(f"\\nFound {len(modules_result.data)} modules:")

        for module in modules_result.data:
            print(f"  - {module['module']}: {module['confidence']} confidence")

        # Examine each module's data in detail
        print(f"\\n" + "="*60)
        print(f"DETAILED DATA ANALYSIS")
        print(f"="*60)

        for module in modules_result.data:
            module_id = module['id']
            module_name = module['module']

            print(f"\\n[{module_name.upper()}] ANALYSIS")
            print(f"-" * 40)

            # Get analysis results for this module
            results = supabase_admin.table('analysis_results').select('result').eq('scan_module_id', module_id).execute()

            if results.data and len(results.data) > 0:
                result_data = results.data[0]['result']

                if module_name == 'sitecore-schema':
                    await analyze_schema_data(result_data)
                elif module_name == 'sitecore-content':
                    await analyze_content_data(result_data)
                elif module_name == 'sitecore-templates':
                    await analyze_template_data(result_data)
            else:
                print(f"[WARNING] No analysis results found for {module_name}")

        # Overall assessment
        print(f"\\n" + "="*60)
        print(f"PHASE 1 COMPLETENESS ASSESSMENT")
        print(f"="*60)
        await assess_data_completeness(modules_result.data, supabase_admin, scan_id)

    except Exception as e:
        print(f"[ERROR] Audit failed: {e}")
        import traceback
        traceback.print_exc()


async def analyze_schema_data(schema_data):
    """Analyze GraphQL schema extraction depth"""
    print(f"Schema Data Analysis:")

    if not schema_data:
        print(f"  [CRITICAL] No schema data stored!")
        return

    # Check what we captured
    schema_extracted = schema_data.get('schema_extracted', False)
    total_types = schema_data.get('total_types', 0)
    object_types = schema_data.get('object_types', [])
    query_fields = schema_data.get('query_fields', [])

    print(f"  [OK] Schema extracted: {schema_extracted}")
    print(f"  📊 Total types: {total_types}")
    print(f"  📦 Object types stored: {len(object_types)}")
    print(f"  🔍 Query fields stored: {len(query_fields)}")

    # Assess completeness
    if total_types > 0:
        stored_percentage = (len(object_types) / total_types) * 100
        print(f"  📈 Object type coverage: {stored_percentage:.1f}%")

        if stored_percentage < 50:
            print(f"  [WARNING]  [CONCERN] Only storing {len(object_types)} of {total_types} types")
            print(f"      This might limit local analysis capabilities")

    # Check query field details
    if query_fields:
        print(f"  🔍 Available query operations:")
        for field in query_fields[:5]:  # Show first 5
            print(f"     - {field.get('name')}: {field.get('type')} ({field.get('args', 0)} args)")

    # Assess schema depth
    if object_types:
        sample_type = object_types[0]
        print(f"  📋 Sample type structure: {list(sample_type.keys())}")

        has_field_details = 'field_count' in sample_type
        print(f"  🔬 Field details captured: {has_field_details}")

        if not has_field_details:
            print(f"  [WARNING]  [GAP] No field-level details - might need deeper extraction")


async def analyze_content_data(content_data):
    """Analyze content tree extraction depth"""
    print(f"Content Data Analysis:")

    if not content_data:
        print(f"  [CRITICAL] No content data stored!")
        return

    # Check what we captured
    content_extracted = content_data.get('content_extracted', False)
    total_items = content_data.get('estimated_total_items', 0)
    sites = content_data.get('sites', [])
    root_path = content_data.get('root_path')

    print(f"  [OK] Content extracted: {content_extracted}")
    print(f"  📊 Estimated total items: {total_items}")
    print(f"  🌐 Sites discovered: {len(sites)}")
    print(f"  📂 Root path: {root_path}")

    # Examine site data depth
    if sites:
        sample_site = sites[0]
        print(f"  📋 Sample site structure: {list(sample_site.keys())}")

        has_content_details = 'template' in sample_site
        print(f"  🔬 Template info captured: {has_content_details}")

        # Check if we have actual content or just metadata
        has_field_data = any(key in sample_site for key in ['fields', 'content', 'field_values'])
        print(f"  💾 Field/content data captured: {has_field_data}")

        if not has_field_data:
            print(f"  [WARNING]  [CRITICAL GAP] No actual content field data stored!")
            print(f"      We have metadata but not the actual content values")
            print(f"      This severely limits local analysis capabilities")

    # Assess content extraction depth
    print(f"  📈 Content extraction assessment:")
    if total_items > 0 and len(sites) > 0:
        items_per_site = total_items / len(sites)
        print(f"     - Average items per site: {items_per_site:.1f}")

        if items_per_site > 50:
            print(f"     - [OK] Good content volume for analysis")
        else:
            print(f"     - [WARNING]  Limited content volume")


async def analyze_template_data(template_data):
    """Analyze template extraction depth"""
    print(f"Template Data Analysis:")

    if not template_data:
        print(f"  [CRITICAL] No template data stored!")
        return

    # Check what we captured
    templates_extracted = template_data.get('templates_extracted', False)
    system_templates = template_data.get('system_templates', [])
    content_templates = template_data.get('content_templates', [])

    print(f"  [OK] Templates extracted: {templates_extracted}")
    print(f"  🏗️  System templates: {len(system_templates)}")
    print(f"  📄 Content templates: {len(content_templates)}")

    # Examine template depth
    all_templates = system_templates + content_templates
    if all_templates:
        sample_template = all_templates[0]
        print(f"  📋 Sample template structure: {list(sample_template.keys())}")

        has_field_definitions = 'fields' in sample_template or 'field_definitions' in sample_template
        has_inheritance_info = 'base_template' in sample_template or 'inheritance' in sample_template

        print(f"  🔬 Field definitions captured: {has_field_definitions}")
        print(f"  🔗 Inheritance info captured: {has_inheritance_info}")

        if not has_field_definitions:
            print(f"  [WARNING]  [CRITICAL GAP] No template field definitions!")
            print(f"      We have template names but not their structure")
            print(f"      This limits understanding of content model")

        # Check usage information
        has_usage_data = 'usage_count' in sample_template
        print(f"  📊 Usage statistics captured: {has_usage_data}")


async def assess_data_completeness(modules_data, supabase_admin, scan_id):
    """Provide overall assessment of Phase 1 data completeness"""

    print(f"Overall Phase 1 Assessment:")
    print(f"")

    # Check module success rate
    successful_modules = len([m for m in modules_data if m['error'] is None])
    total_modules = len(modules_data)

    print(f"[OK] Module Success Rate: {successful_modules}/{total_modules}")

    # Critical gaps analysis
    critical_gaps = []
    recommendations = []

    # Check if we need enhanced extraction
    print(f"\\n🔍 CRITICAL GAPS ANALYSIS:")

    # Schema completeness
    schema_module = next((m for m in modules_data if m['module'] == 'sitecore-schema'), None)
    if schema_module and schema_module['confidence'] < 0.9:
        critical_gaps.append("Schema extraction may be incomplete")
        recommendations.append("Enhance schema extraction to capture full field definitions")

    # Content depth
    content_module = next((m for m in modules_data if m['module'] == 'sitecore-content'), None)
    if content_module:
        recommendations.append("Add content field value extraction for comprehensive local analysis")

    # Template depth
    template_module = next((m for m in modules_data if m['module'] == 'sitecore-templates'), None)
    if template_module:
        recommendations.append("Enhance template extraction to capture field schemas and inheritance")

    # Data persistence completeness
    print(f"\\n💾 DATA PERSISTENCE ANALYSIS:")

    # Check database storage efficiency
    analysis_results = supabase_admin.table('analysis_results').select('*').eq('scan_module_id.in', f"({','.join([m['id'] for m in modules_data])})").execute()

    print(f"   📊 Analysis results stored: {len(analysis_results.data)}")

    if len(analysis_results.data) < successful_modules:
        critical_gaps.append("Some module results not persisted to analysis_results table")

    # Final recommendations
    print(f"\\n🎯 PHASE 1 COMPLETENESS VERDICT:")

    if not critical_gaps:
        print(f"   [OK] Phase 1 appears complete for basic analysis")
    else:
        print(f"   [WARNING]  Phase 1 has gaps that may limit local analysis:")
        for gap in critical_gaps:
            print(f"      - {gap}")

    print(f"\\n🚀 RECOMMENDATIONS FOR ENHANCEMENT:")
    for rec in recommendations:
        print(f"   📈 {rec}")

    # Phase 2 readiness assessment
    print(f"\\n🔮 PHASE 2 READINESS:")
    if successful_modules == total_modules and not critical_gaps:
        print(f"   [OK] Ready for Phase 2 development")
        print(f"   💡 Consider enhancing data depth for richer analysis")
    else:
        print(f"   [WARNING]  Should address Phase 1 gaps before Phase 2")
        print(f"   🔧 Focus on comprehensive data extraction first")


if __name__ == "__main__":
    print("Starting Phase 1 data completeness audit...")
    asyncio.run(audit_phase1_data())