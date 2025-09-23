#!/usr/bin/env python3
"""
Test Supabase API Key Discovery
Try to find the correct API key and URL for Supabase access
"""

import asyncio
import aiohttp
import json


async def test_supabase_endpoints():
    """Test different Supabase endpoint configurations"""

    host = "10.0.0.196"

    # Common Supabase ports and paths
    endpoints = [
        f"http://{host}:8000/rest/v1/",
        f"http://{host}:54321/rest/v1/",
        f"http://{host}:3000/rest/v1/",
        f"http://{host}:8000/",
        f"http://{host}:54321/",
    ]

    # API keys to try (from your credentials)
    api_keys = [
        "yRPHDq9MaQt6JIDl3kSkoR2E",  # supabase password
        "boTW1PbupfnkXRdlXr1RFdL7qqyi43wm",  # postgres password
    ]

    print("SUPABASE API ENDPOINT DISCOVERY")
    print("=" * 35)

    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(timeout=timeout) as session:

        for endpoint in endpoints:
            print(f"\nTesting endpoint: {endpoint}")
            print("-" * 40)

            # Test without auth first
            try:
                async with session.get(endpoint) as response:
                    text = await response.text()
                    print(f"  No auth: HTTP {response.status}")
                    if response.status == 401:
                        print(f"    Response: {text[:100]}")
                    elif response.status == 200:
                        print(f"    SUCCESS: {text[:100]}")
                        return endpoint
            except Exception as e:
                print(f"  No auth: CONNECTION FAILED - {e}")
                continue

            # Test with different API key formats
            for api_key in api_keys:
                print(f"    Testing API key: {api_key[:8]}...")

                # Test different header formats
                auth_methods = [
                    {"apikey": api_key},
                    {"Authorization": f"Bearer {api_key}"},
                    {
                        "apikey": api_key,
                        "Authorization": f"Bearer {api_key}"
                    },
                    {
                        "Authorization": f"Basic {api_key}",
                        "apikey": api_key
                    }
                ]

                for auth in auth_methods:
                    try:
                        async with session.get(endpoint, headers=auth) as response:
                            text = await response.text()

                            if response.status == 200:
                                print(f"      SUCCESS: {auth}")
                                print(f"      Response: {text[:100]}")

                                # Test a simple table query
                                tables_url = endpoint.rstrip('/') + '/sites'
                                try:
                                    async with session.get(tables_url, headers=auth) as tables_response:
                                        tables_text = await tables_response.text()
                                        print(f"      Tables query: HTTP {tables_response.status}")
                                        if tables_response.status == 200:
                                            print(f"      SUCCESS: Can query sites table!")
                                            return {
                                                'endpoint': endpoint,
                                                'auth': auth,
                                                'working': True
                                            }
                                except Exception as e:
                                    print(f"      Tables query failed: {e}")

                            elif response.status == 401:
                                print(f"      Auth failed: {text[:50]}")
                            else:
                                print(f"      HTTP {response.status}: {text[:50]}")

                    except Exception as e:
                        print(f"      Connection failed: {e}")
                        continue

    print(f"\nNO WORKING API CONFIGURATION FOUND")
    return None


async def test_supabase_url_discovery():
    """Try to discover the correct Supabase URL format"""

    host = "10.0.0.196"

    # Try to find Supabase project info
    info_endpoints = [
        f"http://{host}:8000/rest/v1/",
        f"http://{host}:8000/",
        f"http://{host}:8000/health",
        f"http://{host}:8000/status",
    ]

    print(f"\nSUPABASE URL DISCOVERY")
    print(f"=" * 22)

    timeout = aiohttp.ClientTimeout(total=5)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        for endpoint in info_endpoints:
            try:
                async with session.get(endpoint) as response:
                    text = await response.text()
                    print(f"GET {endpoint}")
                    print(f"  Status: {response.status}")
                    print(f"  Headers: {dict(response.headers)}")
                    if text:
                        print(f"  Body: {text[:200]}")
                    print()

            except Exception as e:
                print(f"GET {endpoint} - FAILED: {e}")


if __name__ == "__main__":
    print("Starting Supabase API discovery...")

    # Test endpoint discovery
    result = asyncio.run(test_supabase_endpoints())

    if result:
        print(f"\nFOUND WORKING CONFIGURATION:")
        print(f"  Endpoint: {result['endpoint']}")
        print(f"  Auth: {result['auth']}")
    else:
        print(f"\nNo working API configuration found")
        print(f"Running URL discovery...")
        asyncio.run(test_supabase_url_discovery())

        print(f"\nPOSSIBLE NEXT STEPS:")
        print(f"1. Check if Supabase requires a project-specific URL")
        print(f"2. Verify if we need a service role key (not user password)")
        print(f"3. Check Supabase documentation for local instance setup")
        print(f"4. Continue with local JSON files (which work perfectly)")