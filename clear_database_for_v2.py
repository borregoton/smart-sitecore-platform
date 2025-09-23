#!/usr/bin/env python3
"""
Clear Database for V2.0 - Safe Database Cleanup
Removes old schema data to prepare for fresh GrabSiteCoreData extraction
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List, Dict

# Add the cli directory to the path
sys.path.insert(0, 'cli')

try:
    from smart_sitecore.supabase_client_v2 import SupabaseClientV2
except ImportError as e:
    print(f"[ERROR] Missing CLI module: {e}")
    print("Run: python launch.py --setup-only")
    sys.exit(1)


class DatabaseCleaner:
    """Safe database cleanup for V2.0 transition"""

    def __init__(self):
        self.db_client = SupabaseClientV2()
        self.tables_to_clear = [
            # Old schema tables (v1.0)
            'sites',
            'scans',
            'graphql_types',
            'content_items',
            'template_definitions',
            'scan_results',

            # New schema tables (v2.0) - clear for fresh start
            'customers',
            'customer_sites',
            'scans_v2',
            'site_relationships',
            'cross_site_comparisons',
            'portfolio_insights',
            'benchmark_data'
        ]

        # Track what we actually clear
        self.cleared_tables = []
        self.skipped_tables = []
        self.row_counts = {}

    async def clear_database(self, confirm: bool = False):
        """Main cleanup workflow"""

        print("SMART SITECORE ANALYSIS PLATFORM - V2.0")
        print("Database Cleanup for Fresh Start")
        print("=" * 55)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        if not confirm:
            print("WARNING: This will permanently delete ALL Sitecore extraction data!")
            print("This includes:")
            print("  - All customer and site records")
            print("  - All scan history and results")
            print("  - All extracted Sitecore content")
            print("  - All analysis data and templates")
            print()
            print("This prepares the database for a fresh v2.0 multi-site extraction.")
            print()

            response = input("Are you sure you want to proceed? Type 'YES' to confirm: ")
            if response != 'YES':
                print("Cleanup cancelled.")
                return False

        try:
            # Step 1: Initialize database connection
            print("[1/4] Connecting to database...")
            db_result = await self.db_client.initialize()

            # Check if we have a working connection
            if self.db_client.connection_method is None:
                raise Exception(f"Database connection failed: {db_result.get('pg_error', 'Unknown error')}")

            print(f"[OK] Connected via {self.db_client.connection_method}")
            if db_result.get('status') == 'using_local_files':
                print(f"[WARNING] Using local fallback - database operations may not work")

            # Step 2: Analyze current data
            print("[2/4] Analyzing current data...")
            await self._analyze_current_data()

            # Step 3: Clear tables
            print("[3/4] Clearing tables...")
            await self._clear_tables()

            # Step 4: Verify cleanup
            print("[4/4] Verifying cleanup...")
            await self._verify_cleanup()

            # Display cleanup report
            self._display_cleanup_report()

            return True

        except Exception as e:
            print(f"[ERROR] Cleanup failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            # Clean up database connection
            await self._cleanup_connection()

    async def _analyze_current_data(self):
        """Analyze what data currently exists"""

        if self.db_client.connection_method == 'postgresql' and self.db_client.pool:
            async with self.db_client.pool.acquire() as conn:
                for table in self.tables_to_clear:
                    try:
                        # Check if table exists and get row count
                        result = await conn.fetchval(
                            f"SELECT COUNT(*) FROM {table}"
                        )
                        self.row_counts[table] = result
                        print(f"   {table}: {result} rows")
                    except Exception as e:
                        self.skipped_tables.append(table)
                        print(f"   {table}: table not found (will skip)")
        else:
            print("   [WARNING] No PostgreSQL connection - cannot analyze data")
            # Add all tables to skipped list
            self.skipped_tables.extend(self.tables_to_clear)

    async def _clear_tables(self):
        """Clear all identified tables"""

        if self.db_client.connection_method == 'postgresql' and self.db_client.pool:
            async with self.db_client.pool.acquire() as conn:
                for table in self.tables_to_clear:
                    if table in self.skipped_tables:
                        continue

                    try:
                        # Delete all rows from table
                        await conn.execute(f"DELETE FROM {table}")

                        # Reset any auto-increment sequences
                        await conn.execute(f"ALTER SEQUENCE IF EXISTS {table}_id_seq RESTART WITH 1")

                        self.cleared_tables.append(table)
                        print(f"   [OK] Cleared {table}")

                    except Exception as e:
                        print(f"   [ERROR] Failed to clear {table}: {e}")
        else:
            print("   [WARNING] No PostgreSQL connection - cannot clear tables")

    async def _verify_cleanup(self):
        """Verify tables are actually empty"""

        verification_failed = []

        if self.db_client.connection_method == 'postgresql' and self.db_client.pool:
            async with self.db_client.pool.acquire() as conn:
                for table in self.cleared_tables:
                    try:
                        count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                        if count > 0:
                            verification_failed.append(f"{table} ({count} rows remaining)")
                    except Exception as e:
                        verification_failed.append(f"{table} (verification error)")

            if verification_failed:
                print(f"   [WARNING] Verification issues:")
                for issue in verification_failed:
                    print(f"      - {issue}")
            else:
                print(f"   [OK] All cleared tables verified empty")
        else:
            print("   [INFO] Skipping verification - no PostgreSQL connection")

    async def _cleanup_connection(self):
        """Clean up database connections to avoid warnings"""
        try:
            if hasattr(self.db_client, 'pool') and self.db_client.pool:
                await self.db_client.pool.close()

            if hasattr(self.db_client, 'session') and self.db_client.session:
                await self.db_client.session.close()
        except Exception as e:
            # Ignore cleanup errors
            pass

    def _display_cleanup_report(self):
        """Display comprehensive cleanup report"""

        print("\n" + "=" * 70)
        print("DATABASE CLEANUP REPORT")
        print("=" * 70)

        # SUMMARY
        total_rows_cleared = sum(self.row_counts.get(table, 0) for table in self.cleared_tables)

        print(f"CLEANUP SUMMARY")
        print(f"   Tables Cleared:     {len(self.cleared_tables)}")
        print(f"   Tables Skipped:     {len(self.skipped_tables)}")
        print(f"   Total Rows Deleted: {total_rows_cleared:,}")
        print()

        # CLEARED TABLES
        if self.cleared_tables:
            print(f"TABLES CLEARED")
            for table in self.cleared_tables:
                row_count = self.row_counts.get(table, 0)
                print(f"   {table:<25} {row_count:>10,} rows deleted")
            print()

        # SKIPPED TABLES
        if self.skipped_tables:
            print(f"TABLES SKIPPED (not found)")
            for table in self.skipped_tables:
                print(f"   {table}")
            print()

        print(f"READY FOR V2.0")
        print(f"   Database is now clean and ready for fresh extraction")
        print(f"   Run: python launch.py GrabSiteCoreData")
        print(f"   This will create new v2.0 multi-site data structure")

        print("=" * 70)


async def main():
    """Main entry point for database cleanup"""

    print("This script will clear ALL existing Sitecore data to prepare for v2.0")
    print("The new GrabSiteCoreData command will create fresh multi-site data.")
    print()

    cleaner = DatabaseCleaner()
    success = await cleaner.clear_database()

    if success:
        print("\n[SUCCESS] Database cleanup completed successfully!")
        print("Ready to run: python launch.py GrabSiteCoreData")
    else:
        print("\n[ERROR] Database cleanup failed!")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)