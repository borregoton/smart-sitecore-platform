#!/usr/bin/env python3
"""
Database Extraction Report Generator
Generate comprehensive HTML report of what data is actually in the database
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add the cli directory to the path
sys.path.insert(0, 'cli')

try:
    from smart_sitecore.supabase_client_v2 import SupabaseClientV2
except ImportError as e:
    print(f"[ERROR] Missing CLI module: {e}")
    print("Run: python launch.py --setup-only")
    sys.exit(1)


class DatabaseReportGenerator:
    """Generate comprehensive HTML report of extracted data"""

    def __init__(self):
        self.db_client = SupabaseClientV2()

    async def generate_report(self):
        """Generate comprehensive HTML report"""

        print("SMART SITECORE ANALYSIS PLATFORM - V2.0")
        print("Database Extraction Report Generator")
        print("=" * 55)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        try:
            # Connect to database
            print("[1/5] Connecting to database...")
            db_result = await self.db_client.initialize()

            if self.db_client.connection_method != 'postgresql':
                print("[ERROR] Need PostgreSQL connection for report generation")
                return False

            print("[OK] Connected successfully")

            # Gather all data
            print("[2/5] Gathering scan data...")
            scan_data = await self._get_scan_data()

            print("[3/5] Gathering extraction modules...")
            module_data = await self._get_module_data()

            print("[4/5] Gathering analysis results...")
            results_data = await self._get_results_data()

            print("[4.5/5] Analyzing Sitecore content data...")
            content_analysis = await self._analyze_sitecore_content(results_data)

            print("[5/5] Generating HTML report...")
            html_content = await self._generate_html_report(scan_data, module_data, results_data, content_analysis)

            # Save report
            report_filename = f"sitecore_extraction_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(report_filename, 'w', encoding='utf-8') as f:
                f.write(html_content)

            print(f"[SUCCESS] Report generated: {report_filename}")
            print(f"Open in browser to view detailed extraction results")
            return True

        except Exception as e:
            print(f"[ERROR] Report generation failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            # Clean up
            try:
                if hasattr(self.db_client, 'pool') and self.db_client.pool:
                    await self.db_client.pool.close()
            except:
                pass

    async def _get_scan_data(self):
        """Get all scan data from both v1.0 and v2.0 tables"""
        data = {
            'v1_scans': [],
            'v2_scans': [],
            'v1_sites': [],
            'v2_sites': [],
            'customers': []
        }

        async with self.db_client.pool.acquire() as conn:
            # V1.0 scans
            try:
                v1_scans = await conn.fetch("SELECT * FROM scans ORDER BY created_at DESC LIMIT 20")
                data['v1_scans'] = [dict(row) for row in v1_scans]
            except:
                pass

            # V2.0 scans
            try:
                v2_scans = await conn.fetch("SELECT * FROM scans_v2 ORDER BY started_at DESC LIMIT 20")
                data['v2_scans'] = [dict(row) for row in v2_scans]
            except:
                pass

            # V1.0 sites
            try:
                v1_sites = await conn.fetch("SELECT * FROM sites ORDER BY created_at DESC")
                data['v1_sites'] = [dict(row) for row in v1_sites]
            except:
                pass

            # V2.0 sites
            try:
                v2_sites = await conn.fetch("SELECT * FROM customer_sites ORDER BY created_at DESC")
                data['v2_sites'] = [dict(row) for row in v2_sites]
            except:
                pass

            # Customers
            try:
                customers = await conn.fetch("SELECT * FROM customers ORDER BY created_at DESC")
                data['customers'] = [dict(row) for row in customers]
            except:
                pass

        return data

    async def _get_module_data(self):
        """Get all scan modules"""
        data = []

        async with self.db_client.pool.acquire() as conn:
            try:
                modules = await conn.fetch("""
                    SELECT sm.*, s.site_id, s.created_at as scan_created_at
                    FROM scan_modules sm
                    LEFT JOIN scans s ON sm.scan_id = s.id
                    ORDER BY sm.created_at DESC
                    LIMIT 50
                """)
                data = [dict(row) for row in modules]
            except Exception as e:
                print(f"[WARNING] Could not fetch scan modules: {e}")

        return data

    async def _get_results_data(self):
        """Get all analysis results with their full content"""
        data = []

        async with self.db_client.pool.acquire() as conn:
            try:
                results = await conn.fetch("""
                    SELECT ar.*, sm.module, sm.data_source, sm.confidence,
                           sm.duration_ms, sm.error, sm.created_at as module_created_at
                    FROM analysis_results ar
                    LEFT JOIN scan_modules sm ON ar.scan_module_id = sm.id
                    ORDER BY ar.created_at DESC
                    LIMIT 20
                """)
                data = [dict(row) for row in results]
            except Exception as e:
                print(f"[WARNING] Could not fetch analysis results: {e}")

        return data

    async def _analyze_sitecore_content(self, results_data):
        """Analyze extracted Sitecore content to find sites, pages, templates"""

        content_analysis = {
            'sites_discovered': [],
            'total_content_items': 0,
            'templates_found': [],
            'schema_types': 0,
            'field_definitions': 0,
            'content_by_site': {},
            'extraction_modules': [],
            'debug_info': []
        }

        print(f"[DEBUG] Analyzing {len(results_data)} results from database...")

        for result in results_data:
            try:
                result_json = result.get('result', '{}')
                if isinstance(result_json, str):
                    result_obj = json.loads(result_json)
                else:
                    result_obj = result_json

                module_name = result.get('module', '')

                print(f"[DEBUG] Processing module: {module_name}")
                print(f"[DEBUG] Data size: {len(str(result_json))} characters")
                if isinstance(result_obj, dict):
                    print(f"[DEBUG] Top-level keys: {list(result_obj.keys())}")
                    # Show a preview of the data
                    for key, value in list(result_obj.items())[:3]:  # Show first 3 keys
                        if isinstance(value, (list, dict)):
                            print(f"[DEBUG]   {key}: {type(value).__name__} with {len(value) if hasattr(value, '__len__') else 'unknown'} items")
                        else:
                            print(f"[DEBUG]   {key}: {str(value)[:100]}...")

                # Store debug info for the report
                debug_entry = {
                    'module': module_name,
                    'data_size': len(str(result_json)),
                    'top_keys': list(result_obj.keys()) if isinstance(result_obj, dict) else [],
                    'confidence': result.get('confidence', 0)
                }
                content_analysis['debug_info'].append(debug_entry)

                # Analyze schema extraction results
                if 'enhanced-sitecore-schema' in module_name:
                    if 'total_types' in result_obj:
                        content_analysis['schema_types'] = result_obj.get('total_types', 0)
                    if 'total_field_definitions' in result_obj:
                        content_analysis['field_definitions'] = result_obj.get('total_field_definitions', 0)
                    if 'object_types' in result_obj:
                        content_analysis['templates_found'] = result_obj.get('object_types', [])

                # Analyze content extraction results
                elif 'enhanced-sitecore-content' in module_name:
                    print(f"[DEBUG] Found content extraction module, analyzing structure...")
                    print(f"[DEBUG] Full JSON keys for this module: {list(result_obj.keys())}")

                    # Check all possible keys for site data
                    for key, value in result_obj.items():
                        print(f"[DEBUG] Content key '{key}': {type(value).__name__}")
                        if isinstance(value, (int, float)) and 'site' in key.lower():
                            print(f"[DEBUG]   Site-related number: {key} = {value}")
                        elif key == 'site_data' and isinstance(value, list):
                            print(f"[DEBUG]   FOUND SITE_DATA: {len(value)} items")
                            for i, site in enumerate(value[:2]):  # Show first 2 sites
                                print(f"[DEBUG]     Site {i+1}: {site}")
                        elif 'site' in key.lower() and isinstance(value, (list, dict)):
                            print(f"[DEBUG]   Site-related structure '{key}': {len(value) if hasattr(value, '__len__') else 'unknown'} items")

                    # Look for the actual sites structure we found! (PRIORITY CHECK)
                    if 'sites' in result_obj:
                        sites_list = result_obj.get('sites', [])
                        print(f"[DEBUG] *** PROCESSING SITES with {len(sites_list)} sites! ***")

                        for i, site_info in enumerate(sites_list):
                            if isinstance(site_info, dict):
                                site_name = site_info.get('name', f'Site {i+1}')
                                site_path = site_info.get('path', '')
                                template = site_info.get('template', 'Unknown')
                                child_count = site_info.get('child_count', 0)
                                has_children = site_info.get('has_children', False)
                                site_id = site_info.get('id', '')

                                print(f"[DEBUG] *** Processing Site: {site_name} (Path: {site_path}, Template: {template}, Children: {child_count}) ***")

                                # Add this site to our analysis
                                if site_name not in content_analysis['content_by_site']:
                                    content_analysis['content_by_site'][site_name] = []

                                # Create a content item representing this site's info
                                site_summary = {
                                    'name': site_name,
                                    'path': site_path,
                                    'template': template,
                                    'child_count': child_count,
                                    'has_children': has_children,
                                    'id': site_id,
                                    'type': 'sitecore_site'
                                }
                                content_analysis['content_by_site'][site_name].append(site_summary)
                                content_analysis['total_content_items'] += 1

                                # Add to discovered sites list
                                if site_name not in content_analysis['sites_discovered']:
                                    content_analysis['sites_discovered'].append(site_name)
                                    print(f"[DEBUG] *** Added site to discovered list: {site_name} ***")

                    # Look for sites and their content
                    if 'sites_processed' in result_obj:
                        sites_list = result_obj.get('sites_processed', [])
                        content_analysis['sites_discovered'].extend(sites_list)
                        print(f"[DEBUG] Found sites_processed: {sites_list}")

                    if 'content_items' in result_obj:
                        items = result_obj.get('content_items', [])
                        content_analysis['total_content_items'] += len(items)
                        print(f"[DEBUG] Found {len(items)} content items")

                        # Group content by site
                        for item in items:
                            site_name = item.get('site', item.get('siteName', 'Unknown Site'))
                            if site_name not in content_analysis['content_by_site']:
                                content_analysis['content_by_site'][site_name] = []
                            content_analysis['content_by_site'][site_name].append(item)

                    # Look for alternative structure - content tree by site
                    if 'content_tree' in result_obj:
                        tree = result_obj['content_tree']
                        print(f"[DEBUG] Found content_tree with {len(tree) if hasattr(tree, '__len__') else 'unknown'} entries")
                        if isinstance(tree, dict):
                            for site_key, site_data in tree.items():
                                print(f"[DEBUG] Content tree site: {site_key}")
                                if isinstance(site_data, dict) and 'items' in site_data:
                                    if site_key not in content_analysis['content_by_site']:  # Avoid duplication
                                        content_analysis['content_by_site'][site_key] = site_data['items']
                                        content_analysis['total_content_items'] += len(site_data['items'])
                                        print(f"[DEBUG] Added {len(site_data['items'])} items for site {site_key}")

                    # Look for sites with field data structure (the "4 sites" we saw)
                    if 'sites_with_field_data' in result_obj:
                        sites_count = result_obj.get('sites_with_field_data', 0)
                        print(f"[DEBUG] Found sites_with_field_data: {sites_count}")
                        if sites_count > 0:
                            # If we know there are sites but don't have the list, create placeholders
                            for i in range(sites_count):
                                site_name = f"Sitecore Site {i+1}"
                                if site_name not in content_analysis['content_by_site']:
                                    content_analysis['content_by_site'][site_name] = []

                    # (site_data parsing moved above for priority)

                    # Look for any other site-related data structures
                    for key in result_obj.keys():
                        if 'site' in key.lower() and key not in ['sites_processed', 'sites_with_field_data', 'site_data']:
                            value = result_obj[key]
                            print(f"[DEBUG] Found additional site key '{key}': {type(value).__name__} = {value}")
                            if isinstance(value, (list, dict)) and len(value) > 0:
                                print(f"[DEBUG]   Has {len(value)} items/keys")

                # Store module info for debugging
                content_analysis['extraction_modules'].append({
                    'module': module_name,
                    'confidence': result.get('confidence', 0),
                    'data_size': len(str(result_json)),
                    'keys': list(result_obj.keys()) if isinstance(result_obj, dict) else []
                })

            except Exception as e:
                print(f"[DEBUG] Error analyzing result for {result.get('module', 'unknown')}: {e}")
                continue

        # Calculate summary stats and remove duplicates
        content_analysis['sites_count'] = len(content_analysis['content_by_site'])
        content_analysis['sites_discovered'] = list(set(content_analysis['sites_discovered']))  # Remove duplicates
        if not content_analysis['sites_discovered']:  # If no explicit site list, use the keys
            content_analysis['sites_discovered'] = list(content_analysis['content_by_site'].keys())

        print(f"[DEBUG] Final analysis:")
        print(f"[DEBUG]   Sites discovered: {content_analysis['sites_discovered']}")
        print(f"[DEBUG]   Sites count: {content_analysis['sites_count']}")
        print(f"[DEBUG]   Total content items: {content_analysis['total_content_items']}")
        print(f"[DEBUG]   Content by site: {[(k, len(v)) for k, v in content_analysis['content_by_site'].items()]}")

        return content_analysis

    async def _generate_html_report(self, scan_data, module_data, results_data, content_analysis):
        """Generate comprehensive HTML report"""

        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        html = f"""<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Sitecore Extraction Report - {current_time}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1, h2, h3 {{ color: #e30613; }}
                .header {{ text-align: center; border-bottom: 3px solid #e30613; padding-bottom: 20px; margin-bottom: 30px; }}
                .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }}
                .summary-card {{ background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #e30613; }}
                .summary-card h4 {{ margin: 0 0 10px 0; color: #e30613; }}
                .summary-card .number {{ font-size: 24px; font-weight: bold; color: #333; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; }}
                th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #e30613; color: white; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .json-content {{ background: #f8f9fa; padding: 15px; border-radius: 5px; font-family: monospace; white-space: pre-wrap; max-height: 300px; overflow-y: auto; }}
                .success {{ color: #28a745; font-weight: bold; }}
                .warning {{ color: #ffc107; font-weight: bold; }}
                .error {{ color: #dc3545; font-weight: bold; }}
                .section {{ margin-bottom: 40px; }}
                .expandable {{ cursor: pointer; color: #e30613; }}
                .expandable:hover {{ text-decoration: underline; }}
                .collapsed {{ display: none; }}
            </style>
            <script>
                function toggleContent(id) {{
                    var content = document.getElementById(id);
                    var button = document.getElementById(id + '_btn');
                    if (content.style.display === 'none') {{
                        content.style.display = 'block';
                        button.textContent = 'Hide';
                    }} else {{
                        content.style.display = 'none';
                        button.textContent = 'Show';
                    }}
                }}
            </script>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔍 Sitecore Extraction Report</h1>
                    <p>Comprehensive Analysis of Database Contents</p>
                    <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>

                <div class="summary">
                    <div class="summary-card">
                        <h4>V1.0 Scans</h4>
                        <div class="number">{len(scan_data['v1_scans'])}</div>
                    </div>
                    <div class="summary-card">
                        <h4>V2.0 Scans</h4>
                        <div class="number">{len(scan_data['v2_scans'])}</div>
                    </div>
                    <div class="summary-card">
                        <h4>Scan Modules</h4>
                        <div class="number">{len(module_data)}</div>
                    </div>
                    <div class="summary-card">
                        <h4>Analysis Results</h4>
                        <div class="number">{len(results_data)}</div>
                    </div>
                    <div class="summary-card">
                        <h4>Customers</h4>
                        <div class="number">{len(scan_data['customers'])}</div>
                    </div>
                    <div class="summary-card">
                        <h4>Sites (V1+V2)</h4>
                        <div class="number">{len(scan_data['v1_sites']) + len(scan_data['v2_sites'])}</div>
                    </div>
                    <div class="summary-card">
                        <h4>Sitecore Sites</h4>
                        <div class="number">{content_analysis['sites_count']}</div>
                    </div>
                    <div class="summary-card">
                        <h4>Content Items</h4>
                        <div class="number">{content_analysis['total_content_items']}</div>
                    </div>
                    <div class="summary-card">
                        <h4>Schema Types</h4>
                        <div class="number">{content_analysis['schema_types']}</div>
                    </div>
                    <div class="summary-card">
                        <h4>Field Definitions</h4>
                        <div class="number">{content_analysis['field_definitions']}</div>
                    </div>
                </div>

                <!-- Sitecore Content Analysis Section -->
                <div class="section">
                    <h2>🌍 Sitecore Content Analysis</h2>

                    <h3>Sites Discovered ({content_analysis['sites_count']} total)</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Site Name</th>
                                <th>Content Items</th>
                                <th>Sample Items</th>
                            </tr>
                        </thead>
                        <tbody>
        """

        # Add site-by-site breakdown
        for site_name, items in content_analysis['content_by_site'].items():
            item_count = len(items)

            # Create meaningful sample display
            sample_items = []
            site_url = "N/A"
            template_count = 0

            for item in items[:3]:
                if item.get('type') == 'sitecore_site':
                    site_path = item.get('path', 'N/A')
                    template = item.get('template', 'Unknown')
                    child_count = item.get('child_count', 0)
                    sample_items.append(f"Sitecore Site (Path: {site_path}, Template: {template}, Children: {child_count})")
                elif item.get('type') == 'site_summary':
                    site_url = item.get('url', 'N/A')
                    template_count = item.get('template_count', 0)
                    sample_items.append(f"Site Info (URL: {site_url}, {template_count} templates)")
                else:
                    item_name = item.get('name', item.get('title', 'Untitled'))
                    sample_items.append(item_name)

            sample_text = ', '.join(sample_items) if sample_items else 'No items'
            if len(items) > 3:
                sample_text += f" (and {len(items) - 3} more)"

            html += f"""
                            <tr>
                                <td><strong>{site_name}</strong></td>
                                <td>{item_count}</td>
                                <td>{sample_text}</td>
                            </tr>
            """

        html += """
                        </tbody>
                    </table>

                    <h3>Extraction Module Analysis</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Module</th>
                                <th>Confidence</th>
                                <th>Data Size</th>
                                <th>Data Keys Found</th>
                            </tr>
                        </thead>
                        <tbody>
        """

        # Add module analysis
        for module_info in content_analysis['extraction_modules']:
            confidence = float(module_info.get('confidence', 0))
            confidence_class = 'success' if confidence > 0.8 else 'warning' if confidence > 0.5 else 'error'
            data_size = module_info.get('data_size', 0)
            keys = ', '.join(module_info.get('keys', [])[:5])  # Show first 5 keys
            if len(module_info.get('keys', [])) > 5:
                keys += " (and more...)"

            html += f"""
                            <tr>
                                <td><strong>{module_info.get('module', 'unknown')}</strong></td>
                                <td><span class="{confidence_class}">{confidence:.2f}</span></td>
                                <td>{data_size:,} chars</td>
                                <td>{keys}</td>
                            </tr>
            """

        html += """
                        </tbody>
                    </table>

                    <h3>🔧 Debug Information</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Module</th>
                                <th>Data Size</th>
                                <th>Top-Level Keys Found</th>
                                <th>Confidence</th>
                            </tr>
                        </thead>
                        <tbody>
        """

        # Add debug information
        for debug_info in content_analysis['debug_info']:
            keys_str = ', '.join(debug_info.get('top_keys', [])[:8])  # Show first 8 keys
            if len(debug_info.get('top_keys', [])) > 8:
                keys_str += "..."

            html += f"""
                            <tr>
                                <td><strong>{debug_info.get('module', 'unknown')}</strong></td>
                                <td>{debug_info.get('data_size', 0):,} chars</td>
                                <td><code>{keys_str}</code></td>
                                <td>{debug_info.get('confidence', 0):.2f}</td>
                            </tr>
            """

        html += """
                        </tbody>
                    </table>
                </div>
        """

        # Recent Scans Section
        html += """
                <div class="section">
                    <h2>📊 Recent V1.0 Scans</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Scan ID</th>
                                <th>Site ID</th>
                                <th>Status</th>
                                <th>Created</th>
                                <th>Finished</th>
                                <th>Subscription</th>
                            </tr>
                        </thead>
                        <tbody>
        """

        for scan in scan_data['v1_scans']:
            status_class = 'success' if scan.get('status') == 'complete' else 'warning' if scan.get('status') == 'running' else 'error'
            html += f"""
                            <tr>
                                <td>{str(scan.get('id', ''))[:8]}...</td>
                                <td>{str(scan.get('site_id', ''))[:8]}...</td>
                                <td><span class="{status_class}">{scan.get('status', 'unknown')}</span></td>
                                <td>{scan.get('created_at', '')}</td>
                                <td>{scan.get('finished_at', 'N/A')}</td>
                                <td>{scan.get('subscription_tier', 'free')}</td>
                            </tr>
            """

        html += """
                        </tbody>
                    </table>
                </div>
        """

        # Scan Modules Section
        html += """
                <div class="section">
                    <h2>🔧 Scan Modules</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Module</th>
                                <th>Data Source</th>
                                <th>Confidence</th>
                                <th>Duration (ms)</th>
                                <th>Created</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
        """

        for module in module_data:
            confidence = module.get('confidence', 0)
            confidence_class = 'success' if confidence > 0.8 else 'warning' if confidence > 0.5 else 'error'
            status = 'success' if not module.get('error') else 'error'
            status_text = 'Success' if not module.get('error') else 'Error'

            html += f"""
                            <tr>
                                <td><strong>{module.get('module', 'unknown')}</strong></td>
                                <td>{module.get('data_source', 'unknown')}</td>
                                <td><span class="{confidence_class}">{confidence:.2f}</span></td>
                                <td>{module.get('duration_ms', 0)}</td>
                                <td>{module.get('created_at', '')}</td>
                                <td><span class="{status}">{status_text}</span></td>
                            </tr>
            """

        html += """
                        </tbody>
                    </table>
                </div>
        """

        # Analysis Results Section
        html += """
                <div class="section">
                    <h2>📄 Analysis Results</h2>
        """

        for i, result in enumerate(results_data):
            result_json = result.get('result', '{}')
            if isinstance(result_json, str):
                try:
                    result_obj = json.loads(result_json)
                    result_preview = json.dumps(result_obj, indent=2)[:500] + "..." if len(result_json) > 500 else json.dumps(result_obj, indent=2)
                except:
                    result_preview = str(result_json)[:500] + "..." if len(str(result_json)) > 500 else str(result_json)
            else:
                result_preview = str(result_json)[:500] + "..." if len(str(result_json)) > 500 else str(result_json)

            html += f"""
                    <div style="border: 1px solid #ddd; margin-bottom: 20px; border-radius: 5px;">
                        <div style="background: #f8f9fa; padding: 10px; border-bottom: 1px solid #ddd;">
                            <strong>Module:</strong> {result.get('module', 'unknown')} |
                            <strong>Confidence:</strong> {result.get('confidence', 0):.2f} |
                            <strong>Duration:</strong> {result.get('duration_ms', 0)}ms |
                            <strong>Size:</strong> {len(str(result_json))} chars
                            <button id="result_{i}_btn" class="expandable" onclick="toggleContent('result_{i}')" style="float: right; background: #e30613; color: white; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">Show Content</button>
                        </div>
                        <div id="result_{i}" style="display: none;">
                            <div class="json-content">{result_preview}</div>
                        </div>
                    </div>
            """

        html += """
                </div>
        """

        # Sites Section
        html += f"""
                <div class="section">
                    <h2>🌐 Sites</h2>
                    <h3>V1.0 Sites ({len(scan_data['v1_sites'])})</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Site ID</th>
                                <th>URL</th>
                                <th>Created</th>
                            </tr>
                        </thead>
                        <tbody>
        """

        for site in scan_data['v1_sites']:
            html += f"""
                            <tr>
                                <td>{str(site.get('id', ''))[:8]}...</td>
                                <td><a href="{site.get('url', '')}" target="_blank">{site.get('url', '')}</a></td>
                                <td>{site.get('created_at', '')}</td>
                            </tr>
            """

        html += f"""
                        </tbody>
                    </table>

                    <h3>V2.0 Customer Sites ({len(scan_data['v2_sites'])})</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Site ID</th>
                                <th>Customer ID</th>
                                <th>Name</th>
                                <th>Sitecore URL</th>
                                <th>Status</th>
                                <th>Created</th>
                            </tr>
                        </thead>
                        <tbody>
        """

        for site in scan_data['v2_sites']:
            html += f"""
                            <tr>
                                <td>{str(site.get('id', ''))[:8]}...</td>
                                <td>{str(site.get('customer_id', ''))[:8]}...</td>
                                <td><strong>{site.get('name', '')}</strong></td>
                                <td><a href="{site.get('sitecore_url', '')}" target="_blank">{site.get('sitecore_url', '')}</a></td>
                                <td><span class="success">{site.get('status', 'active')}</span></td>
                                <td>{site.get('created_at', '')}</td>
                            </tr>
            """

        html += """
                        </tbody>
                    </table>
                </div>

                <div class="section">
                    <h2>🔍 Data Analysis</h2>
                    <div class="json-content">
        """

        # Add data analysis with safe type handling
        try:
            total_data_size = sum(len(str(result.get('result', ''))) for result in results_data) if results_data else 0
            recent_modules = [m for m in module_data if m.get('created_at') and '2025-09-22' in str(m.get('created_at'))] if module_data else []
            avg_confidence = sum(float(m.get('confidence', 0)) for m in module_data) / len(module_data) if module_data else 0.0

            # Create summary text safely
            summary_text = f"""
EXTRACTION SUMMARY:
==================
Total Analysis Results: {len(results_data)}
Total Data Size: {total_data_size:,} characters
Recent Modules (today): {len(recent_modules)}
Average Confidence: {avg_confidence:.2f}

MOST RECENT EXTRACTIONS:
========================
"""

            # Add module details safely
            for module in (module_data[:5] if module_data else []):
                module_confidence = float(module.get('confidence', 0))
                module_duration = int(module.get('duration_ms', 0))
                summary_text += f"""Module: {module.get('module', 'unknown')}
  Confidence: {module_confidence:.2f}
  Duration: {module_duration}ms
  Created: {module.get('created_at', 'unknown')}
  Error: {module.get('error', 'None')}
"""

            html += summary_text

        except Exception as e:
            html += f"Error generating data analysis: {e}"

        html += """
                    </div>
                </div>

                <div style="text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #666;">
                    <p>Generated by Smart Sitecore Analysis Platform v2.0</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html


async def main():
    """Main entry point for report generation"""

    generator = DatabaseReportGenerator()
    success = await generator.generate_report()

    if success:
        print("\n[SUCCESS] Database extraction report generated!")
        print("Open the HTML file in your browser to view detailed results")
    else:
        print("\n[ERROR] Report generation failed")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)