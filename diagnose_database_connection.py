#!/usr/bin/env python3
"""
Database Connection Diagnostics
Test different connection methods to identify the exact issue
"""

import asyncio
import socket
import time
from datetime import datetime

def test_network_connectivity():
    """Test basic network connectivity to database server"""
    print("=" * 60)
    print("NETWORK CONNECTIVITY TEST")
    print("=" * 60)

    host = "10.0.0.196"
    port = 5432

    print(f"Testing connection to {host}:{port}...")

    try:
        # Test basic TCP connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5 second timeout

        start_time = time.time()
        result = sock.connect_ex((host, port))
        end_time = time.time()

        sock.close()

        if result == 0:
            print(f"[SUCCESS] TCP connection successful ({end_time - start_time:.2f}s)")
            return True
        else:
            print(f"[FAILED] TCP connection failed - Error code: {result}")
            return False

    except socket.timeout:
        print(f"[TIMEOUT] Connection timed out after 5 seconds")
        return False
    except Exception as e:
        print(f"[ERROR] Network test failed: {e}")
        return False

async def test_asyncpg_connection():
    """Test asyncpg connection with detailed error reporting"""
    print("\n" + "=" * 60)
    print("ASYNCPG CONNECTION TEST")
    print("=" * 60)

    # Test credentials to try
    credentials = [
        {
            'name': 'postgres',
            'user': 'postgres',
            'password': 'boTW1PbupfnkXRdlXr1RFdL7qqyi43wm',
            'database': 'postgres'
        },
        {
            'name': 'supabase',
            'user': 'supabase',
            'password': 'yRPHDq9MaQt6JIDl3kSkoR2E',
            'database': 'postgres'
        }
    ]

    try:
        import asyncpg
    except ImportError:
        print("[ERROR] asyncpg not installed")
        return False

    for cred in credentials:
        print(f"\nTesting {cred['name']} credentials...")

        try:
            print(f"  Attempting connection to 10.0.0.196:5432...")

            # Try with very short timeout first
            start_time = time.time()

            conn = await asyncio.wait_for(
                asyncpg.connect(
                    host="10.0.0.196",
                    port=5432,
                    database=cred['database'],
                    user=cred['user'],
                    password=cred['password']
                ),
                timeout=10.0  # 10 second timeout
            )

            end_time = time.time()
            print(f"  [SUCCESS] Connected with {cred['name']} ({end_time - start_time:.2f}s)")

            # Test a simple query
            try:
                version = await conn.fetchval("SELECT version()")
                print(f"  [SUCCESS] Query successful: {version[:50]}...")

                # Test table listing
                tables = await conn.fetch(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public' LIMIT 5"
                )
                print(f"  [SUCCESS] Found {len(tables)} tables")

                await conn.close()
                return True

            except Exception as query_error:
                print(f"  [ERROR] Query failed: {query_error}")
                await conn.close()

        except asyncio.TimeoutError:
            print(f"  [TIMEOUT] Connection timed out after 10 seconds")

        except Exception as e:
            print(f"  [ERROR] Connection failed: {e}")

    return False

def test_alternative_ports():
    """Test if database is running on alternative ports"""
    print("\n" + "=" * 60)
    print("ALTERNATIVE PORT TEST")
    print("=" * 60)

    host = "10.0.0.196"
    ports_to_test = [5432, 8000, 5433, 5434, 3306]

    for port in ports_to_test:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()

            if result == 0:
                print(f"  [OPEN] Port {port} is accessible")
            else:
                print(f"  [CLOSED] Port {port} is not accessible")

        except Exception as e:
            print(f"  [ERROR] Could not test port {port}: {e}")

async def test_web_api_access():
    """Test if Supabase REST API is accessible"""
    print("\n" + "=" * 60)
    print("SUPABASE REST API TEST")
    print("=" * 60)

    try:
        import aiohttp
    except ImportError:
        print("[ERROR] aiohttp not installed")
        return False

    url = "http://10.0.0.196:8000/rest/v1/"

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            print(f"Testing REST API at {url}...")

            async with session.get(url) as response:
                print(f"  [SUCCESS] HTTP {response.status} - API accessible")
                return True

    except asyncio.TimeoutError:
        print(f"  [TIMEOUT] REST API timed out")
    except Exception as e:
        print(f"  [ERROR] REST API failed: {e}")

    return False

async def main():
    """Run comprehensive database diagnostics"""
    print("DATABASE CONNECTION DIAGNOSTICS")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Test 1: Basic network connectivity
    network_ok = test_network_connectivity()

    # Test 2: Alternative ports
    test_alternative_ports()

    # Test 3: REST API access
    api_ok = await test_web_api_access()

    # Test 4: Direct PostgreSQL connection
    if network_ok:
        postgres_ok = await test_asyncpg_connection()
    else:
        postgres_ok = False
        print("\n[SKIPPED] PostgreSQL test - network connectivity failed")

    # Summary and recommendations
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY & RECOMMENDATIONS")
    print("=" * 60)

    if postgres_ok:
        print("[SUCCESS] PostgreSQL connection working!")
        print("  The database cleanup should work now.")
        print("  Try running: python launch.py clear_database")

    elif network_ok and not postgres_ok:
        print("[PARTIAL] Network OK but PostgreSQL failed")
        print("  Possible issues:")
        print("  - Wrong database credentials")
        print("  - PostgreSQL not configured for external connections")
        print("  - Authentication method mismatch")
        print("  - Database server overloaded")

    elif api_ok:
        print("[ALTERNATIVE] REST API accessible")
        print("  Consider using REST API instead of direct PostgreSQL")
        print("  The database cleanup might work with modifications")

    else:
        print("[CRITICAL] No database connectivity")
        print("  Possible issues:")
        print("  - Database server is down")
        print("  - Network/firewall blocking connections")
        print("  - Wrong server IP address")
        print("  - Supabase instance not running")
        print()
        print("  Recommendations:")
        print("  1. Verify 10.0.0.196 is the correct database server")
        print("  2. Check if database server is running")
        print("  3. Test from a different machine/network")
        print("  4. Contact database administrator")

if __name__ == "__main__":
    asyncio.run(main())