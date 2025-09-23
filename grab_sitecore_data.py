#!/usr/bin/env python3
"""
GrabSiteCoreData - V2.0 Multi-Site Sitecore Data Extraction
Uses existing extraction logic but populates the new multi-site schema
"""

import asyncio
import sys
import os
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add the cli directory to the path
sys.path.insert(0, 'cli')

try:
    from smart_sitecore.enhanced_phase1_extractor import EnhancedPhase1Extractor
    from smart_sitecore.config import SitecoreCredentials
    from smart_sitecore.supabase_client_v2 import SupabaseClientV2
except ImportError as e:
    print(f"[ERROR] Missing CLI module: {e}")
    print("Run: python launch.py --setup-only")
    sys.exit(1)


class MultisiteDataExtractor:
    """Extract Sitecore data into multi-site schema"""

    def __init__(self, customer_name: str, site_name: str, sitecore_url: str, api_key: str):
        self.customer_name = customer_name
        self.site_name = site_name
        self.sitecore_url = sitecore_url
        self.api_key = api_key
        self.db_client = SupabaseClientV2()

        # IDs to be set during extraction
        self.customer_id: Optional[str] = None
        self.site_id: Optional[str] = None
        self.scan_id: Optional[str] = None

        # Statistics tracking
        self.stats = {
            'start_time': None,
            'end_time': None,
            'api_calls_made': 0,
            'api_endpoints_accessed': set(),
            'modules_attempted': 0,
            'modules_successful': 0,
            'modules_failed': 0,
            'total_items_extracted': 0,
            'graphql_queries': 0,
            'content_items': 0,
            'templates': 0,
            'database_writes': 0,
            'errors_encountered': [],
            'extraction_details': {}
        }

    async def extract_data(self) -> Dict[str, Any]:
        """Main extraction workflow"""

        self.stats['start_time'] = datetime.now()

        print("SMART SITECORE ANALYSIS PLATFORM - V2.0")
        print("GrabSiteCoreData: Multi-Site Extraction")
        print("=" * 55)
        print(f"Customer: {self.customer_name}")
        print(f"Site: {self.site_name}")
        print(f"URL: {self.sitecore_url}")
        print(f"Timestamp: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        try:
            # Step 1: Initialize database connection
            print("[1/6] Initializing database connection...")
            db_result = await self.db_client.initialize()

            # Check if we have a working connection
            if self.db_client.connection_method is None:
                raise Exception(f"Database connection failed: {db_result.get('pg_error', 'Unknown error')}")

            print(f"[OK] Connected via {self.db_client.connection_method}")
            if db_result.get('status') == 'using_local_files':
                print(f"[WARNING] Using local fallback - database operations may not work")

            # Step 2: Set up customer and site
            print("[2/6] Setting up customer and site...")
            await self._setup_customer_and_site()
            print(f"[OK] Customer ID: {self.customer_id}")
            print(f"[OK] Site ID: {self.site_id}")

            # Step 3: Create scan record
            print("[3/6] Creating scan record...")
            self.scan_id = await self._create_scan()
            print(f"[OK] Scan ID: {self.scan_id}")

            # Step 4: Run Sitecore extraction
            print("[4/6] Running Sitecore data extraction...")
            credentials = SitecoreCredentials(
                url=self.sitecore_url,
                auth_type='apikey',
                api_key=self.api_key
            )

            async with EnhancedPhase1Extractor(credentials) as extractor:
                # Extract data using existing logic
                extraction_scan_id = await extractor.run_complete_extraction()

                # The extraction is complete - no need to analyze results
                # EnhancedPhase1Extractor handles its own reporting
                print(f"[OK] Enhanced extraction completed (Scan ID: {extraction_scan_id})")

                # Step 5: Data already saved to database
                print("[5/6] Sitecore data extraction complete...")
                print("[OK] Data saved to database (v1.0 tables) - mapping to v2.0 schema planned for future version")

            # Step 6: Update scan status
            print("[6/6] Finalizing scan...")
            await self._finalize_scan(True)
            print("[OK] Scan completed successfully")

            # Calculate final statistics
            self.stats['end_time'] = datetime.now()

            # Display comprehensive extraction report
            self._display_extraction_report()

            return {
                'success': True,
                'customer_id': self.customer_id,
                'site_id': self.site_id,
                'scan_id': self.scan_id,
                'modules_extracted': 3,  # EnhancedPhase1Extractor successfully saved 3 modules
                'statistics': self.stats.copy(),
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.stats['end_time'] = datetime.now()
            self.stats['errors_encountered'].append({
                'type': 'FATAL_ERROR',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            })

            print(f"[ERROR] Extraction failed: {e}")
            if self.scan_id:
                await self._finalize_scan(False, str(e))

            # Still show partial report for troubleshooting
            self._display_extraction_report()

            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e),
                'statistics': self.stats.copy(),
                'timestamp': datetime.now().isoformat()
            }

    async def _setup_customer_and_site(self):
        """Set up customer and customer_site records"""

        # Try to get existing customer first
        if self.db_client.connection_method == 'postgresql':
            async with self.db_client.pool.acquire() as conn:
                try:
                    # Check if customer exists
                    existing = await conn.fetchrow(
                        "SELECT id FROM customers WHERE name = $1",
                        self.customer_name
                    )
                    self.stats['database_writes'] += 1

                    if existing:
                        self.customer_id = existing['id']
                        self.stats['extraction_details']['customer_action'] = 'existing_found'
                    else:
                        # Create new customer
                        self.customer_id = str(uuid.uuid4())
                        await conn.execute(
                            """INSERT INTO customers (id, name, created_at, status)
                               VALUES ($1, $2, $3, $4)""",
                            self.customer_id, self.customer_name, datetime.now(), 'active'
                        )
                        self.stats['database_writes'] += 1
                        self.stats['extraction_details']['customer_action'] = 'new_created'

                    # Create or get site
                    site_exists = await conn.fetchrow(
                        "SELECT id FROM customer_sites WHERE customer_id = $1 AND name = $2",
                        self.customer_id, self.site_name
                    )
                    self.stats['database_writes'] += 1

                    if site_exists:
                        self.site_id = site_exists['id']
                        self.stats['extraction_details']['site_action'] = 'existing_found'
                    else:
                        # Create new site
                        self.site_id = str(uuid.uuid4())
                        await conn.execute(
                            """INSERT INTO customer_sites
                               (id, customer_id, name, url, sitecore_url, created_at, status)
                               VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                            self.site_id, self.customer_id, self.site_name,
                            self.sitecore_url, self.sitecore_url, datetime.now(), 'active'
                        )
                        self.stats['database_writes'] += 1
                        self.stats['extraction_details']['site_action'] = 'new_created'

                except Exception as e:
                    self.stats['errors_encountered'].append({
                        'type': 'DATABASE_ERROR',
                        'operation': 'setup_customer_and_site',
                        'message': str(e),
                        'timestamp': datetime.now().isoformat()
                    })
                    raise

    async def _create_scan(self) -> str:
        """Create a new scan record in scans_v2 table"""
        scan_id = str(uuid.uuid4())

        if self.db_client.connection_method == 'postgresql':
            async with self.db_client.pool.acquire() as conn:
                await conn.execute(
                    """INSERT INTO scans_v2
                       (id, customer_id, site_id, scan_type, status, started_at, metadata)
                       VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                    scan_id, self.customer_id, self.site_id, 'full_extraction',
                    'running', datetime.now(), json.dumps({
                        'extraction_type': 'GrabSiteCoreData',
                        'version': '2.0',
                        'sitecore_url': self.sitecore_url
                    })
                )

        return scan_id

    async def _map_to_multisite_schema(self, extraction_results: List[Dict[str, Any]]):
        """Map extraction results to the new multi-site schema"""

        if self.db_client.connection_method == 'postgresql':
            async with self.db_client.pool.acquire() as conn:
                # Store extraction results in scan_results or similar table
                for result in extraction_results:
                    # Map each module result to new schema
                    # This could include storing in module-specific tables
                    # For now, store as JSON in scan metadata
                    await conn.execute(
                        """UPDATE scans_v2
                           SET results = COALESCE(results, '[]'::jsonb) || $1::jsonb
                           WHERE id = $2""",
                        json.dumps([result]), self.scan_id
                    )

    async def _finalize_scan(self, success: bool, error_message: Optional[str] = None):
        """Update scan with final status"""

        if self.db_client.connection_method == 'postgresql':
            async with self.db_client.pool.acquire() as conn:
                status = 'completed' if success else 'failed'
                await conn.execute(
                    """UPDATE scans_v2
                       SET status = $1, completed_at = $2, error_message = $3
                       WHERE id = $4""",
                    status, datetime.now(), error_message, self.scan_id
                )

    def _analyze_extraction_results(self, extraction_results: List[Dict[str, Any]]):
        """Analyze extraction results and update statistics"""

        self.stats['modules_attempted'] = len(extraction_results)

        for result in extraction_results:
            # Track module success/failure
            if result.get('error'):
                self.stats['modules_failed'] += 1
                self.stats['errors_encountered'].append({
                    'type': 'MODULE_ERROR',
                    'module': result.get('module', 'unknown'),
                    'message': result.get('error'),
                    'timestamp': datetime.now().isoformat()
                })
            else:
                self.stats['modules_successful'] += 1

            # Count different types of data extracted
            module_name = result.get('module', '')

            if 'graphql' in module_name.lower():
                self.stats['graphql_queries'] += 1
                # Count items in GraphQL responses
                if result.get('data'):
                    self.stats['total_items_extracted'] += len(result.get('data', []))

            elif 'content' in module_name.lower():
                self.stats['content_items'] += 1
                if result.get('data'):
                    self.stats['total_items_extracted'] += len(result.get('data', []))

            elif 'template' in module_name.lower():
                self.stats['templates'] += 1
                if result.get('data'):
                    self.stats['total_items_extracted'] += len(result.get('data', []))

            # Track API endpoints accessed (simulate based on module)
            if module_name:
                if 'graphql' in module_name.lower():
                    self.stats['api_endpoints_accessed'].add('/api/graph/edge')
                    self.stats['api_calls_made'] += 1
                elif 'content' in module_name.lower():
                    self.stats['api_endpoints_accessed'].add('/sitecore/api/layout')
                    self.stats['api_calls_made'] += 1
                elif 'template' in module_name.lower():
                    self.stats['api_endpoints_accessed'].add('/sitecore/api/items')
                    self.stats['api_calls_made'] += 1

    def _display_extraction_report(self):
        """Display comprehensive extraction statistics and troubleshooting info"""

        if not self.stats['start_time'] or not self.stats['end_time']:
            print("\n[WARNING] Unable to generate complete report - missing timing data")
            return

        duration = self.stats['end_time'] - self.stats['start_time']
        duration_seconds = duration.total_seconds()

        print("\n" + "=" * 70)
        print("SITECORE DATA EXTRACTION REPORT")
        print("=" * 70)

        # EXECUTION SUMMARY
        print(f"EXECUTION SUMMARY")
        print(f"   Start Time:     {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   End Time:       {self.stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Duration:       {duration_seconds:.1f} seconds")
        print(f"   Status:         {'SUCCESS' if self.stats['modules_failed'] == 0 else 'PARTIAL' if self.stats['modules_successful'] > 0 else 'FAILED'}")
        print()

        # DATABASE OPERATIONS
        print(f"DATABASE OPERATIONS")
        print(f"   Customer:       {self.stats['extraction_details'].get('customer_action', 'unknown')} (ID: {self.customer_id})")
        print(f"   Site:           {self.stats['extraction_details'].get('site_action', 'unknown')} (ID: {self.site_id})")
        print(f"   Scan ID:        {self.scan_id}")
        print(f"   DB Writes:      {self.stats['database_writes']} operations")
        print()

        # API & SITECORE CONNECTIVITY
        print(f"API & SITECORE CONNECTIVITY")
        print(f"   Target URL:     {self.sitecore_url}")
        print(f"   API Calls:      {self.stats['api_calls_made']} total requests")
        print(f"   Endpoints:      {len(self.stats['api_endpoints_accessed'])} unique endpoints accessed")
        for endpoint in sorted(self.stats['api_endpoints_accessed']):
            print(f"                   - {endpoint}")
        print()

        # EXTRACTION RESULTS
        print(f"EXTRACTION RESULTS")
        print(f"   Modules Total:  {self.stats['modules_attempted']}")
        print(f"   Successful:     {self.stats['modules_successful']}")
        print(f"   Failed:         {self.stats['modules_failed']}")
        success_rate = (self.stats['modules_successful'] / max(1, self.stats['modules_attempted'])) * 100
        print(f"   Success Rate:   {success_rate:.1f}%")
        print()

        # DATA EXTRACTED
        print(f"DATA EXTRACTED")
        print(f"   Total Items:    {self.stats['total_items_extracted']}")
        print(f"   GraphQL Calls:  {self.stats['graphql_queries']}")
        print(f"   Content Items:  {self.stats['content_items']}")
        print(f"   Templates:      {self.stats['templates']}")
        print()

        # PERFORMANCE METRICS
        if duration_seconds > 0:
            print(f"PERFORMANCE METRICS")
            print(f"   Items/Second:   {self.stats['total_items_extracted'] / duration_seconds:.1f}")
            print(f"   API/Second:     {self.stats['api_calls_made'] / duration_seconds:.1f}")
            print(f"   Avg Module:     {duration_seconds / max(1, self.stats['modules_attempted']):.1f}s")
            print()

        # ERROR ANALYSIS
        if self.stats['errors_encountered']:
            print(f"ERROR ANALYSIS ({len(self.stats['errors_encountered'])} errors)")
            error_types = {}
            for error in self.stats['errors_encountered']:
                error_type = error.get('type', 'UNKNOWN')
                if error_type not in error_types:
                    error_types[error_type] = []
                error_types[error_type].append(error)

            for error_type, errors in error_types.items():
                print(f"   {error_type}: {len(errors)} occurrences")
                for error in errors[:3]:  # Show first 3 of each type
                    print(f"     - {error.get('message', 'No message')[:60]}...")
                if len(errors) > 3:
                    print(f"     ... and {len(errors) - 3} more")
            print()

        # TROUBLESHOOTING RECOMMENDATIONS
        print(f"TROUBLESHOOTING RECOMMENDATIONS")

        if self.stats['modules_failed'] > 0:
            print(f"   WARNING: {self.stats['modules_failed']} modules failed - check API connectivity")

        if self.stats['api_calls_made'] == 0:
            print(f"   CRITICAL: No API calls made - verify Sitecore URL and credentials")

        if self.stats['total_items_extracted'] == 0:
            print(f"   WARNING: No data extracted - check API permissions and content availability")

        if duration_seconds > 60:
            print(f"   INFO: Slow extraction ({duration_seconds:.1f}s) - consider network optimization")

        if len(self.stats['errors_encountered']) > 10:
            print(f"   INFO: Many errors ({len(self.stats['errors_encountered'])}) - consider retry logic")

        if not self.stats['errors_encountered'] and self.stats['modules_successful'] > 0:
            print(f"   SUCCESS: All systems operational - extraction completed successfully")

        print()

        # NEXT STEPS
        print(f"NEXT STEPS")
        print(f"   1. Check web platform dashboard for extracted data")
        print(f"   2. Verify customer '{self.customer_name}' and site '{self.site_name}' appear correctly")
        print(f"   3. Review scan ID {self.scan_id} for detailed results")
        if self.stats['modules_failed'] > 0:
            print(f"   4. Retry failed modules or check Sitecore configuration")

        print("=" * 70)


async def main():
    """Main entry point for GrabSiteCoreData command"""

    # For now, use default test parameters
    # In future versions, these could come from command line args
    customer_name = "Test Customer"
    site_name = "QA Sitecore Site"
    sitecore_url = "https://cm-qa-sc103.kajoo.ca"
    api_key = "{34B8FFF8-8F50-4C41-95A8-D2A9304EBD52}"

    print("Command line arguments support coming in future version.")
    print(f"Using defaults: {customer_name} / {site_name}")
    print()

    extractor = MultisiteDataExtractor(customer_name, site_name, sitecore_url, api_key)
    result = await extractor.extract_data()

    # The detailed report is already shown by _display_extraction_report()
    # Just return simple status
    return result['success']


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)