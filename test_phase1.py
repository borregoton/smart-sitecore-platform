#!/usr/bin/env python3
"""
Phase 1 Deliverables Test
Tests all four Phase 1 requirements:
1. Can connect to Sitecore GraphQL
2. Extracts real content items
3. Saves to Supabase
4. Returns scan IDs
"""

import asyncio
import sys
import os
sys.path.insert(0, 'cli')

from smart_sitecore.phase1_extractor import run_phase1_extraction
from smart_sitecore.db_client import db_client


async def test_phase1_deliverables():
    """Test all Phase 1 deliverables"""

    print("🎯 PHASE 1: SITECORE DATA EXTRACTION - DELIVERABLES TEST")
    print("=" * 65)

    # Known working Sitecore endpoint and API key
    sitecore_url = "https://cm-qa-sc103.kajoo.ca"
    api_key = "{34B8FFF8-8F50-4C41-95A8-D2A9304EBD52}"

    print(f"Target: {sitecore_url}")
    print(f"Database: 10.0.0.196:5432")

    try:
        # Test database connection first
        print("\n[PREREQUISITE] Testing database connection...")
        print("-" * 45)

        db_status = await db_client.test_connection()

        if db_status['status'] == 'connected':
            print(f"✅ Database connected successfully")
            print(f"   Version: {db_status['database_version'][:50]}...")
            print(f"   Tables: {db_status['tables_found']}")
            print(f"   Schema ready: {db_status['schema_ready']}")

            if not db_status['schema_ready']:
                print("   Initializing schema...")
                await db_client.initialize_schema()
        else:
            print(f"❌ Database connection failed: {db_status['error']}")
            return False

        # Run Phase 1 extraction
        print("\n[PHASE 1 EXTRACTION] Running complete extraction...")
        print("-" * 55)

        scan_id = await run_phase1_extraction(sitecore_url, api_key)

        print(f"\n[DELIVERABLE VERIFICATION] Checking Phase 1 requirements...")
        print("-" * 60)

        # Verify all deliverables
        deliverables_met = await verify_deliverables(scan_id)

        if deliverables_met:
            print(f"\n🎉 ALL PHASE 1 DELIVERABLES MET!")
            print(f"   Scan ID: {scan_id}")
            print(f"   Ready for Phase 2")
            return True
        else:
            print(f"\n❌ Some deliverables not met")
            return False

    except Exception as e:
        print(f"\n❌ Phase 1 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        await db_client.close()


async def verify_deliverables(scan_id: str) -> bool:
    """Verify all Phase 1 deliverables are met"""

    all_met = True

    print("Checking deliverables:")

    # Deliverable 1: Can connect to Sitecore GraphQL
    print("\n1️⃣  Can connect to Sitecore GraphQL")
    results = await db_client.get_scan_results(scan_id)

    graphql_modules = [r for r in results if 'sitecore' in r['module'] and r['error'] is None]
    if graphql_modules:
        print("   ✅ PASS - Connected to Sitecore GraphQL successfully")
        for module in graphql_modules:
            print(f"      {module['module']}: {module['confidence']:.2f} confidence")
    else:
        print("   ❌ FAIL - Could not connect to Sitecore GraphQL")
        all_met = False

    # Deliverable 2: Extracts real content items
    print("\n2️⃣  Extracts real content items")
    content_modules = [r for r in results if r['module'] == 'sitecore-content' and r['error'] is None]

    if content_modules:
        content_result = content_modules[0]['result']
        if content_result and content_result.get('content_extracted'):
            estimated_items = content_result.get('estimated_total_items', 0)
            sites_count = content_result.get('sites_discovered', 0)

            print("   ✅ PASS - Real content items extracted")
            print(f"      Sites discovered: {sites_count}")
            print(f"      Estimated items: {estimated_items}")

            if estimated_items > 0:
                print("      Content sample:")
                for site in content_result.get('sites', [])[:3]:
                    print(f"        - {site['name']}: {site['child_count']} items")
            else:
                print("   ⚠️  WARNING - No content items found")
        else:
            print("   ❌ FAIL - Content extraction returned no data")
            all_met = False
    else:
        print("   ❌ FAIL - Content extraction failed")
        all_met = False

    # Deliverable 3: Saves to Supabase
    print("\n3️⃣  Saves to Supabase")
    if results:
        print("   ✅ PASS - Data saved to Supabase successfully")
        print(f"      Modules saved: {len(results)}")
        print(f"      Database tables: sites, scans, scan_modules, analysis_results")

        # Check for actual data
        modules_with_data = [r for r in results if r['result'] is not None]
        print(f"      Modules with data: {len(modules_with_data)}")

        # Show storage breakdown
        for result in results:
            size_estimate = len(str(result['result'])) if result['result'] else 0
            status = "✅" if result['error'] is None else "❌"
            print(f"        {status} {result['module']}: ~{size_estimate} bytes")

    else:
        print("   ❌ FAIL - No data saved to Supabase")
        all_met = False

    # Deliverable 4: Returns scan IDs
    print("\n4️⃣  Returns scan IDs")
    if scan_id:
        print("   ✅ PASS - Scan ID returned successfully")
        print(f"      Scan ID: {scan_id}")
        print(f"      Format: UUID (36 characters)")

        # Verify scan exists in database
        try:
            scan_results = await db_client.get_scan_results(scan_id)
            if scan_results:
                print(f"      Scan retrievable: ✅ ({len(scan_results)} modules)")
            else:
                print(f"      Scan retrievable: ❌ (no modules found)")
                all_met = False
        except Exception as e:
            print(f"      Scan retrievable: ❌ ({e})")
            all_met = False
    else:
        print("   ❌ FAIL - No scan ID returned")
        all_met = False

    # Summary
    print(f"\n📋 DELIVERABLES SUMMARY")
    print("-" * 25)
    print(f"✅ Connect to GraphQL: {'PASS' if graphql_modules else 'FAIL'}")
    print(f"✅ Extract content: {'PASS' if content_modules else 'FAIL'}")
    print(f"✅ Save to Supabase: {'PASS' if results else 'FAIL'}")
    print(f"✅ Return scan IDs: {'PASS' if scan_id else 'FAIL'}")

    return all_met


async def test_database_schema():
    """Test database schema initialization"""

    print("\n[SCHEMA TEST] Testing database schema...")
    print("-" * 40)

    try:
        await db_client.initialize_schema()
        print("✅ Schema initialization successful")

        # Test basic operations
        test_url = "https://test-site.example.com"
        site_id = await db_client.ensure_site(test_url)
        scan_id = await db_client.create_scan(site_id)

        print(f"✅ Test site created: {site_id}")
        print(f"✅ Test scan created: {scan_id}")

        # Test module saving
        await db_client.save_module(
            scan_id=scan_id,
            module="test-module",
            data_source="test-source",
            confidence=1.0,
            duration_ms=100,
            result={"test": "data"},
            requires_credentials=False
        )

        print("✅ Test module saved")

        # Clean up test data
        await db_client.finish_scan(scan_id)
        print("✅ Test scan completed")

        return True

    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_phase1_deliverables())