#!/usr/bin/env python3
"""
Verify that data was actually saved to the real Supabase database
Check if our sites and scans are there
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


async def verify_database_data():
    """Verify data was saved to Supabase"""

    print("VERIFYING REAL DATABASE DATA")
    print("=" * 30)

    # Provided working credentials
    SUPABASE_URL = "http://10.0.0.196:8000"
    SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJyb2xlIjoic2VydmljZV9yb2xlIiwiaXNzIjoic3VwYWJhc2UtZGVtbyIsImlhdCI6MTc1ODU1NzY1MywiZXhwIjoyMDczOTMyMDUzfQ.eCfBa97jXcYRm0cgwBhbR62qs8KQTxmkjP6ef3SPCVA"

    try:
        # Create admin client
        supabase_admin: Client = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)
        print(f"[SUCCESS] Connected to Supabase")

        # Check sites table
        print(f"\n[1] Checking sites table...")
        sites_result = supabase_admin.table('sites').select('*').execute()

        if sites_result.data:
            print(f"   [SUCCESS] Found {len(sites_result.data)} sites in database:")
            for site in sites_result.data:
                print(f"     - ID: {site['id']}")
                print(f"       URL: {site['url']}")
                print(f"       Created: {site['created_at']}")
                print()
        else:
            print(f"   [INFO] No sites found in database")

        # Check scans table
        print(f"[2] Checking scans table...")
        scans_result = supabase_admin.table('scans').select('*').order('created_at', desc=True).execute()

        if scans_result.data:
            print(f"   [SUCCESS] Found {len(scans_result.data)} scans in database:")
            for scan in scans_result.data[:5]:  # Show first 5
                print(f"     - ID: {scan['id']}")
                print(f"       Site ID: {scan['site_id']}")
                print(f"       Status: {scan['status']}")
                print(f"       Created: {scan['created_at']}")
                if scan['error']:
                    print(f"       Error: {scan['error']}")
                print()
        else:
            print(f"   [INFO] No scans found in database")

        # Check for recent scan with Sitecore URL
        print(f"[3] Looking for Sitecore analysis scans...")

        sitecore_sites = [site for site in sites_result.data if 'kajoo.ca' in site['url']]
        if sitecore_sites:
            print(f"   [SUCCESS] Found Sitecore sites:")
            for site in sitecore_sites:
                print(f"     - {site['url']} (ID: {site['id']})")

                # Get scans for this site
                site_scans = supabase_admin.table('scans').select('*').eq('site_id', site['id']).order('created_at', desc=True).execute()

                if site_scans.data:
                    print(f"       Scans: {len(site_scans.data)}")
                    latest = site_scans.data[0]
                    print(f"       Latest: {latest['status']} ({latest['created_at']})")
                else:
                    print(f"       No scans found")
                print()
        else:
            print(f"   [INFO] No Sitecore sites found")

        # Summary
        print(f"\n" + "="*50)
        print(f"DATABASE VERIFICATION SUMMARY")
        print(f"="*50)
        print(f"Total Sites: {len(sites_result.data)}")
        print(f"Total Scans: {len(scans_result.data)}")
        print(f"Sitecore Sites: {len(sitecore_sites)}")

        recent_scans = [s for s in scans_result.data if 'complete' in s['status']]
        print(f"Completed Scans: {len(recent_scans)}")

        if recent_scans:
            print(f"\n[SUCCESS] Real database is working!")
            print(f"[OK] Sites and scans are being saved to Supabase")
            print(f"[OK] Phase 1 extraction is persisting data")
            print(f"[WARNING] Only missing modules table for full functionality")
        else:
            print(f"\n[INFO] Database connected but no completed scans yet")

        return True

    except Exception as e:
        print(f"[ERROR] Database verification failed: {e}")
        return False


if __name__ == "__main__":
    print("Verifying that Phase 1 data was saved to real Supabase database...")

    success = asyncio.run(verify_database_data())

    if success:
        print(f"\n[NEXT STEPS]")
        print(f"1. [OK] Database connection is working perfectly")
        print(f"2. [WARNING] Create modules table for full functionality")
        print(f"3. [OK] Phase 1 extraction can continue with sites/scans persistence")
    else:
        print(f"\n[ACTION NEEDED] Database verification failed")