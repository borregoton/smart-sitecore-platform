#!/usr/bin/env python3
"""
Find Supabase API Keys
Try to discover the actual API keys needed for this Supabase instance
"""

import asyncio
import aiohttp
import json


async def extract_keys_from_studio():
    """Try to extract API keys from Supabase Studio"""

    print("EXTRACTING KEYS FROM SUPABASE STUDIO")
    print("=" * 35)

    host = "10.0.0.196"
    studio_endpoints = [
        f"http://{host}:8000/dashboard",
        f"http://{host}:8000/project/default",
        f"http://{host}:8000/project/default/settings/api",
        f"http://{host}:8000/project/default/api",
        f"http://{host}:8000/project/default/auth",
        f"http://{host}:8000/dashboard/project/default/settings/api"
    ]

    timeout = aiohttp.ClientTimeout(total=10)

    async with aiohttp.ClientSession(timeout=timeout) as session:

        for endpoint in studio_endpoints:
            print(f"\nTrying: {endpoint}")

            try:
                async with session.get(endpoint) as response:
                    text = await response.text()
                    print(f"  Status: {response.status}")

                    if response.status == 200:
                        # Look for API key patterns in the response
                        if 'eyJ' in text:  # JWT pattern
                            import re
                            jwt_pattern = r'eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+'
                            tokens = re.findall(jwt_pattern, text)
                            if tokens:
                                print(f"  Found JWT tokens: {len(tokens)}")
                                for i, token in enumerate(tokens[:3]):  # Show first 3
                                    print(f"    Token {i+1}: {token[:50]}...")
                                return tokens

                        # Look for other patterns
                        patterns = [
                            r'service_role["\s:]+([a-zA-Z0-9_-]+)',
                            r'anon["\s:]+([a-zA-Z0-9_-]+)',
                            r'SUPABASE_[A-Z_]+["\s:]+([a-zA-Z0-9_-]+)'
                        ]

                        for pattern in patterns:
                            import re
                            matches = re.findall(pattern, text, re.IGNORECASE)
                            if matches:
                                print(f"  Found keys matching {pattern}: {matches}")

                    elif response.status == 401:
                        print(f"  Needs authentication")
                    else:
                        print(f"  Response length: {len(text)}")

            except Exception as e:
                print(f"  Error: {e}")

    return None


async def test_default_local_keys():
    """Test known default keys for local Supabase instances"""

    print(f"\nTESTING DEFAULT LOCAL SUPABASE KEYS")
    print(f"=" * 35)

    host = "10.0.0.196"

    # These are the standard local development keys from Supabase documentation
    # They should work for any local Supabase instance unless changed
    default_keys = {
        'anon': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0',
        'service_role': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU'
    }

    # Install and test Supabase client
    try:
        from supabase import create_client, Client

        for key_name, key in default_keys.items():
            print(f"\nTesting {key_name} key...")
            url = f'http://{host}:8000'

            try:
                # Create client
                supabase: Client = create_client(url, key)

                # Test basic operation - list tables/get one record
                print(f"  Testing connection to {url}")

                # Try a simple select
                result = supabase.table('sites').select("*").limit(1).execute()

                print(f"  SUCCESS! Connected with {key_name} key")
                print(f"  Query result: {result}")

                # Try to insert test data
                try:
                    insert_result = supabase.table('sites').insert({
                        'url': f'https://test-{key_name}-key.example.com'
                    }).execute()

                    print(f"  INSERT SUCCESS: {insert_result}")

                    return {
                        'working_key': key,
                        'key_type': key_name,
                        'url': url,
                        'client': supabase
                    }

                except Exception as insert_e:
                    print(f"  Insert failed: {insert_e}")
                    # Even if insert fails, read might work
                    return {
                        'working_key': key,
                        'key_type': key_name,
                        'url': url,
                        'client': supabase,
                        'readonly': True
                    }

            except Exception as e:
                print(f"  Failed with {key_name}: {e}")

        print(f"\nDefault keys didn't work - need to find instance-specific keys")
        return None

    except ImportError:
        print(f"Supabase client import failed")
        return None


async def test_jwt_decode():
    """Decode JWT tokens to understand what we're working with"""

    print(f"\nDECODING JWT TOKENS")
    print(f"=" * 18)

    keys_to_decode = [
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0',
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImV4cCI6MTk4MzgxMjk5Nn0.EGIM96RAZx35lJzdJsyH-qQwv8Hdp7fsn3W0YpN81IU'
    ]

    try:
        import jwt
        import base64

        for token in keys_to_decode:
            try:
                # Decode without verification to see payload
                decoded = jwt.decode(token, options={"verify_signature": False})
                print(f"Token: {token[:30]}...")
                print(f"  Payload: {decoded}")
                print()

            except Exception as e:
                print(f"Failed to decode token: {e}")

    except ImportError:
        print(f"PyJWT not available for decoding")

        # Manual base64 decode of JWT payload
        for token in keys_to_decode:
            try:
                import base64
                import json

                # JWT format: header.payload.signature
                parts = token.split('.')
                if len(parts) >= 2:
                    payload_part = parts[1]
                    # Add padding if needed
                    padding = len(payload_part) % 4
                    if padding:
                        payload_part += '=' * (4 - padding)

                    decoded_bytes = base64.urlsafe_b64decode(payload_part)
                    payload = json.loads(decoded_bytes)

                    print(f"Token: {token[:30]}...")
                    print(f"  Payload: {payload}")
                    print()

            except Exception as e:
                print(f"Manual decode failed: {e}")


if __name__ == "__main__":
    print("Starting Supabase API key discovery...")

    # Try to extract from Studio
    studio_keys = asyncio.run(extract_keys_from_studio())

    # Test default keys
    working_config = asyncio.run(test_default_local_keys())

    # Decode tokens to understand structure
    asyncio.run(test_jwt_decode())

    if working_config:
        print(f"\n🎯 SUCCESS: FOUND WORKING CONFIGURATION!")
        print(f"Key Type: {working_config['key_type']}")
        print(f"URL: {working_config['url']}")
        print(f"Working Key: {working_config['working_key'][:50]}...")

        if working_config.get('readonly'):
            print(f"Note: Read-only access (insert failed)")
        else:
            print(f"Note: Full read/write access")

    else:
        print(f"\n❌ NO WORKING CONFIGURATION FOUND")
        print(f"\nNext steps:")
        print(f"1. Check if Supabase instance uses custom JWT secret")
        print(f"2. Look for instance-specific configuration files")
        print(f"3. Check Docker logs or environment variables")
        print(f"4. Ask for help with the specific Supabase setup")