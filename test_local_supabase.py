#!/usr/bin/env python3
"""
Test Local Supabase Instance Connection
Research common local Supabase patterns and try to connect
"""

import asyncio
import aiohttp
import json


async def test_local_supabase_patterns():
    """Test common local Supabase connection patterns"""

    print("LOCAL SUPABASE CONNECTION RESEARCH")
    print("=" * 35)

    host = "10.0.0.196"

    # Common local Supabase default keys (from documentation)
    common_keys = [
        # Default local development keys
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0",
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU",
        # Your provided credentials (might be encoded)
        "yRPHDq9MaQt6JIDl3kSkoR2E",
        "boTW1PbupfnkXRdlXr1RFdL7qqyi43wm"
    ]

    # Test endpoints
    endpoints = [
        f"http://{host}:8000/rest/v1/sites",
        f"http://{host}:54321/rest/v1/sites",
        f"http://{host}:8000/rest/v1/",
        f"http://{host}:54321/rest/v1/"
    ]

    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(timeout=timeout) as session:

        for endpoint in endpoints:
            print(f"\nTesting endpoint: {endpoint}")
            print("-" * 40)

            for key in common_keys:
                print(f"  Key: {key[:20]}...")

                # Standard Supabase headers
                headers = {
                    'apikey': key,
                    'Authorization': f'Bearer {key}',
                    'Content-Type': 'application/json'
                }

                try:
                    # Test GET request
                    async with session.get(endpoint, headers=headers) as response:
                        text = await response.text()

                        if response.status == 200:
                            print(f"    SUCCESS: GET {response.status}")
                            print(f"    Response: {text[:100]}")

                            # Try to insert test data
                            test_data = {
                                'url': 'https://test-connection.example.com'
                            }

                            try:
                                async with session.post(endpoint, headers=headers, json=test_data) as post_response:
                                    post_text = await post_response.text()
                                    print(f"    POST TEST: {post_response.status}")
                                    if post_response.status in [200, 201]:
                                        print(f"    SUCCESS: Can write data!")
                                        return {
                                            'endpoint': endpoint,
                                            'key': key,
                                            'headers': headers,
                                            'working': True
                                        }
                                    else:
                                        print(f"    POST failed: {post_text[:100]}")
                            except Exception as e:
                                print(f"    POST error: {e}")

                        elif response.status == 401:
                            print(f"    AUTH FAILED: {text[:50]}")
                        else:
                            print(f"    HTTP {response.status}: {text[:50]}")

                except Exception as e:
                    print(f"    ERROR: {e}")

    print(f"\nNO WORKING CONFIGURATION FOUND")
    return None


async def test_supabase_python_client():
    """Test with official Supabase Python client"""

    print(f"\nTESTING OFFICIAL SUPABASE CLIENT")
    print(f"=" * 32)

    try:
        # Try to import supabase client
        from supabase import create_client, Client

        host = "10.0.0.196"

        # Common local development URLs and keys
        configs = [
            {
                'url': f'http://{host}:8000',
                'key': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0'
            },
            {
                'url': f'http://{host}:8000',
                'key': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU'
            },
            {
                'url': f'http://{host}:54321',
                'key': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0'
            }
        ]

        for config in configs:
            print(f"Testing URL: {config['url']}")
            print(f"Key: {config['key'][:30]}...")

            try:
                # Create client
                supabase: Client = create_client(config['url'], config['key'])

                # Test simple query
                response = supabase.table('sites').select("*").limit(1).execute()

                print(f"  SUCCESS: Connected to database!")
                print(f"  Tables accessible: sites")
                print(f"  Response: {response}")

                # Try to insert test data
                test_insert = supabase.table('sites').insert({
                    'url': 'https://test-supabase-client.example.com'
                }).execute()

                print(f"  INSERT SUCCESS: {test_insert}")

                return {
                    'client': supabase,
                    'config': config,
                    'working': True
                }

            except Exception as e:
                print(f"  FAILED: {e}")
                continue

        print(f"NO WORKING SUPABASE CLIENT CONFIGURATION")
        return None

    except ImportError:
        print(f"Supabase client not installed - install with: pip install supabase")
        return None


async def discover_supabase_config():
    """Look for Supabase configuration files"""

    print(f"\nSUPABASE CONFIG DISCOVERY")
    print(f"=" * 25)

    # Look for common config files
    config_paths = [
        ".env",
        ".env.local",
        "supabase/.env",
        "docker-compose.yml",
        "docker-compose.override.yml"
    ]

    import os

    for path in config_paths:
        if os.path.exists(path):
            print(f"Found config file: {path}")
            try:
                with open(path, 'r') as f:
                    content = f.read()
                    # Look for Supabase-related configs
                    lines = content.split('\n')
                    for line in lines:
                        if any(keyword in line.lower() for keyword in ['supabase', 'service_role', 'anon_key', 'jwt']):
                            print(f"  {line}")
            except Exception as e:
                print(f"  Error reading {path}: {e}")

    # Test common local development paths
    print(f"\nChecking common local development endpoints...")

    test_urls = [
        "http://10.0.0.196:8000/health",
        "http://10.0.0.196:54321/health",
        "http://10.0.0.196:8000/status",
        "http://10.0.0.196:8000/.well-known/jwks.json"
    ]

    timeout = aiohttp.ClientTimeout(total=5)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for url in test_urls:
            try:
                async with session.get(url) as response:
                    text = await response.text()
                    print(f"  GET {url}: {response.status}")
                    if response.status == 200:
                        print(f"    Response: {text[:200]}")
            except:
                print(f"  GET {url}: FAILED")


if __name__ == "__main__":
    print("Starting local Supabase connection research...")

    # Test raw HTTP patterns
    result1 = asyncio.run(test_local_supabase_patterns())

    # Test official client
    result2 = asyncio.run(test_supabase_python_client())

    # Look for config files
    asyncio.run(discover_supabase_config())

    if result1 or result2:
        print(f"\nSUCCESS: Found working database connection!")
        working_config = result1 or result2
        print(f"Config: {working_config}")
    else:
        print(f"\nNEED TO INVESTIGATE FURTHER")
        print(f"Next steps:")
        print(f"1. Check if this is Docker Compose Supabase setup")
        print(f"2. Look for .env files in parent directories")
        print(f"3. Check docker-compose logs for service keys")
        print(f"4. Ask user for Supabase project settings")