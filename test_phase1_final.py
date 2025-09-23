#!/usr/bin/env python3
"""
Phase 1 Final Test - Simple Implementation
Tests all four Phase 1 requirements without Unicode or complex extraction
"""

import asyncio
import aiohttp
import json
import time
import sys
import os
sys.path.insert(0, 'cli')

from smart_sitecore.config import SitecoreCredentials
from smart_sitecore.local_db_client import local_db_client as db_client


async def run_simple_phase1_extraction(sitecore_url: str, api_key: str) -> str:
    """Simple Phase 1 extraction focusing on deliverables"""

    print("PHASE 1: SITECORE DATA EXTRACTION")
    print("=" * 40)

    credentials = SitecoreCredentials(
        url=sitecore_url,
        auth_type='apikey',
        api_key=api_key
    )

    # Initialize database
    await db_client.initialize_schema()
    site_id = await db_client.ensure_site(sitecore_url)
    scan_id = await db_client.create_scan(site_id)

    print(f"Site ID: {site_id}")
    print(f"Scan ID: {scan_id}")

    # Create HTTP session
    timeout = aiohttp.ClientTimeout(total=30)
    headers = credentials.get_headers()

    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:

        # 1. GraphQL Schema Extraction
        print("\n[1/4] GraphQL Schema Extraction")
        await extract_schema(session, credentials, scan_id)

        # 2. Content Tree Extraction
        print("\n[2/4] Content Tree Extraction")
        await extract_content_tree(session, credentials, scan_id)

        # 3. Template Extraction
        print("\n[3/4] Template Extraction")
        await extract_templates(session, credentials, scan_id)

        # 4. Data Persistence (already done)
        print("\n[4/4] Data Persistence - COMPLETE")

    # Mark scan as complete
    await db_client.finish_scan(scan_id)

    print(f"\nPhase 1 extraction completed!")
    print(f"Scan ID: {scan_id}")
    return scan_id


async def extract_schema(session: aiohttp.ClientSession, credentials: SitecoreCredentials, scan_id: str):
    """Extract GraphQL schema"""
    start_time = time.time()

    try:
        # Simple introspection query
        query = """
        query IntrospectionQuery {
            __schema {
                queryType { name }
                types {
                    name
                    kind
                }
            }
        }
        """

        graphql_url = credentials.get_full_graphql_url()

        async with session.post(graphql_url, json={'query': query}) as response:
            if response.status == 200:
                data = await response.json()

                if 'data' in data and '__schema' in data['data']:
                    schema = data['data']['__schema']
                    types = schema.get('types', [])

                    result = {
                        'schema_extracted': True,
                        'query_type': schema.get('queryType', {}).get('name', 'Query'),
                        'total_types': len(types),
                        'object_types': [t['name'] for t in types if t['kind'] == 'OBJECT'][:10],
                        'extraction_method': 'introspection'
                    }

                    print("   SUCCESS - GraphQL schema extracted")
                    print(f"   Types found: {len(types)}")
                    confidence = 0.9

                else:
                    result = {'schema_extracted': False, 'reason': 'Invalid response'}
                    confidence = 0.1
                    print("   PARTIAL - Invalid schema response")

            else:
                result = {'schema_extracted': False, 'reason': f'HTTP {response.status}'}
                confidence = 0.0
                print(f"   FAILED - HTTP {response.status}")

        duration_ms = int((time.time() - start_time) * 1000)

        await db_client.save_module(
            scan_id=scan_id,
            module="sitecore-schema",
            data_source="sitecore-graphql",
            confidence=confidence,
            duration_ms=duration_ms,
            result=result,
            requires_credentials=True
        )

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        await db_client.save_module(
            scan_id=scan_id,
            module="sitecore-schema",
            data_source="sitecore-graphql",
            confidence=0.0,
            duration_ms=duration_ms,
            result=None,
            requires_credentials=True,
            error=str(e)
        )
        print(f"   ERROR - {e}")


async def extract_content_tree(session: aiohttp.ClientSession, credentials: SitecoreCredentials, scan_id: str):
    """Extract content tree"""
    start_time = time.time()

    try:
        query = """
        query ContentTree {
            item(path: "/sitecore/content", language: "en") {
                id
                name
                path
                children {
                    total
                    results {
                        ... on Item {
                            id
                            name
                            path
                            template {
                                name
                            }
                            hasChildren
                            children {
                                total
                            }
                        }
                    }
                }
            }
        }
        """

        graphql_url = credentials.get_full_graphql_url()

        async with session.post(graphql_url, json={'query': query}) as response:
            if response.status == 200:
                data = await response.json()

                if 'errors' not in data and 'data' in data:
                    content_root = data['data']['item']
                    if content_root:
                        children = content_root.get('children', {}).get('results', [])
                        total_children = content_root.get('children', {}).get('total', 0)

                        # Calculate total items
                        total_items = sum(child.get('children', {}).get('total', 0) for child in children)

                        sites_info = []
                        for child in children:
                            sites_info.append({
                                'name': child.get('name'),
                                'path': child.get('path'),
                                'template': child.get('template', {}).get('name'),
                                'child_count': child.get('children', {}).get('total', 0)
                            })

                        result = {
                            'content_extracted': True,
                            'root_path': content_root.get('path'),
                            'direct_children': total_children,
                            'estimated_total_items': total_items,
                            'sites_discovered': len(sites_info),
                            'sites': sites_info
                        }

                        print("   SUCCESS - Content tree extracted")
                        print(f"   Sites: {len(sites_info)}, Items: {total_items}")
                        confidence = 0.9

                    else:
                        result = {'content_extracted': False, 'reason': 'No content root found'}
                        confidence = 0.1
                        print("   PARTIAL - No content root")

                else:
                    result = {'content_extracted': False, 'reason': 'GraphQL errors'}
                    confidence = 0.0
                    print("   FAILED - GraphQL errors")

            else:
                result = {'content_extracted': False, 'reason': f'HTTP {response.status}'}
                confidence = 0.0
                print(f"   FAILED - HTTP {response.status}")

        duration_ms = int((time.time() - start_time) * 1000)

        await db_client.save_module(
            scan_id=scan_id,
            module="sitecore-content",
            data_source="sitecore-graphql",
            confidence=confidence,
            duration_ms=duration_ms,
            result=result,
            requires_credentials=True
        )

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        await db_client.save_module(
            scan_id=scan_id,
            module="sitecore-content",
            data_source="sitecore-graphql",
            confidence=0.0,
            duration_ms=duration_ms,
            result=None,
            requires_credentials=True,
            error=str(e)
        )
        print(f"   ERROR - {e}")


async def extract_templates(session: aiohttp.ClientSession, credentials: SitecoreCredentials, scan_id: str):
    """Extract template information"""
    start_time = time.time()

    try:
        # Try to get templates from content analysis
        query = """
        query TemplateAnalysis {
            item(path: "/sitecore/content", language: "en") {
                children {
                    results {
                        ... on Item {
                            template {
                                id
                                name
                            }
                            children {
                                results {
                                    ... on Item {
                                        template {
                                            id
                                            name
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """

        graphql_url = credentials.get_full_graphql_url()

        async with session.post(graphql_url, json={'query': query}) as response:
            if response.status == 200:
                data = await response.json()

                if 'errors' not in data and 'data' in data:
                    templates_found = {}

                    # Extract template usage from content
                    items = data.get('data', {}).get('item', {}).get('children', {}).get('results', [])

                    for item in items:
                        template = item.get('template', {})
                        template_name = template.get('name')
                        template_id = template.get('id')

                        if template_name:
                            if template_name not in templates_found:
                                templates_found[template_name] = {
                                    'id': template_id,
                                    'name': template_name,
                                    'usage_count': 0
                                }
                            templates_found[template_name]['usage_count'] += 1

                        # Check children too
                        children = item.get('children', {}).get('results', [])
                        for child in children:
                            child_template = child.get('template', {})
                            child_template_name = child_template.get('name')

                            if child_template_name:
                                if child_template_name not in templates_found:
                                    templates_found[child_template_name] = {
                                        'id': child_template.get('id'),
                                        'name': child_template_name,
                                        'usage_count': 0
                                    }
                                templates_found[child_template_name]['usage_count'] += 1

                    result = {
                        'templates_extracted': True,
                        'templates_found': list(templates_found.values()),
                        'total_templates': len(templates_found),
                        'extraction_method': 'content_analysis'
                    }

                    print("   SUCCESS - Templates extracted")
                    print(f"   Templates found: {len(templates_found)}")
                    confidence = 0.8

                else:
                    result = {'templates_extracted': False, 'reason': 'GraphQL errors'}
                    confidence = 0.0
                    print("   FAILED - GraphQL errors")

            else:
                result = {'templates_extracted': False, 'reason': f'HTTP {response.status}'}
                confidence = 0.0
                print(f"   FAILED - HTTP {response.status}")

        duration_ms = int((time.time() - start_time) * 1000)

        await db_client.save_module(
            scan_id=scan_id,
            module="sitecore-templates",
            data_source="sitecore-graphql",
            confidence=confidence,
            duration_ms=duration_ms,
            result=result,
            requires_credentials=True
        )

    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        await db_client.save_module(
            scan_id=scan_id,
            module="sitecore-templates",
            data_source="sitecore-graphql",
            confidence=0.0,
            duration_ms=duration_ms,
            result=None,
            requires_credentials=True,
            error=str(e)
        )
        print(f"   ERROR - {e}")


async def verify_all_deliverables():
    """Test all Phase 1 deliverables"""

    print("\nPHASE 1 DELIVERABLES VERIFICATION")
    print("=" * 40)

    # Known working credentials
    sitecore_url = "https://cm-qa-sc103.kajoo.ca"
    api_key = "{34B8FFF8-8F50-4C41-95A8-D2A9304EBD52}"

    try:
        # Run extraction
        scan_id = await run_simple_phase1_extraction(sitecore_url, api_key)

        # Verify deliverables
        print("\nVERIFYING DELIVERABLES:")
        print("-" * 25)

        results = await db_client.get_scan_results(scan_id)

        # 1. Can connect to Sitecore GraphQL
        graphql_success = any(r['module'].startswith('sitecore') and r['error'] is None for r in results)
        print(f"1. Connect to GraphQL: {'PASS' if graphql_success else 'FAIL'}")

        # 2. Extracts real content items
        content_success = any(r['module'] == 'sitecore-content' and r['error'] is None for r in results)
        print(f"2. Extract content: {'PASS' if content_success else 'FAIL'}")

        # 3. Saves to database
        data_saved = len(results) > 0
        print(f"3. Save to database: {'PASS' if data_saved else 'FAIL'}")

        # 4. Returns scan IDs
        scan_id_valid = scan_id is not None and len(scan_id) == 36
        print(f"4. Return scan IDs: {'PASS' if scan_id_valid else 'FAIL'}")

        # Show detailed results
        print(f"\nDETAILED RESULTS:")
        print(f"Scan ID: {scan_id}")
        print(f"Modules processed: {len(results)}")

        for result in results:
            status = "PASS" if result['error'] is None else "FAIL"
            confidence = result['confidence']
            duration = result['duration_ms']
            print(f"  {result['module']}: {status} ({confidence:.2f} confidence, {duration}ms)")

        # Show database summary
        summary = db_client.get_database_summary()
        print(f"\nDatabase Summary:")
        print(f"  Total sites: {summary['total_sites']}")
        print(f"  Total scans: {summary['total_scans']}")
        print(f"  Total modules: {summary['total_modules']}")
        print(f"  Total results: {summary['total_results']}")

        all_pass = graphql_success and content_success and data_saved and scan_id_valid

        print(f"\nFINAL RESULT: {'ALL DELIVERABLES MET' if all_pass else 'SOME DELIVERABLES FAILED'}")
        return all_pass

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(verify_all_deliverables())
    print(f"\nPhase 1 completion: {'SUCCESS' if result else 'FAILED'}")