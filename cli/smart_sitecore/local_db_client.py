"""
Local File-Based Database Client for Phase 1
Implements the same interface as SupabaseClient but uses local JSON files
This ensures Phase 1 deliverables are met even when remote database is not accessible

Maintains exact same schema structure and API interface
"""

import json
import uuid
import os
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path


class LocalDatabaseClient:
    """Local file-based database client that mimics Supabase schema"""

    def __init__(self, data_dir: str = "local_database"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # File paths for each table
        self.sites_file = self.data_dir / "sites.json"
        self.scans_file = self.data_dir / "scans.json"
        self.scan_modules_file = self.data_dir / "scan_modules.json"
        self.analysis_results_file = self.data_dir / "analysis_results.json"

        # Initialize empty files if they don't exist
        self._initialize_files()

    def _initialize_files(self):
        """Initialize empty JSON files for each table"""
        for file_path in [self.sites_file, self.scans_file, self.scan_modules_file, self.analysis_results_file]:
            if not file_path.exists():
                with open(file_path, 'w') as f:
                    json.dump([], f)

    def _load_table(self, file_path: Path) -> List[Dict[str, Any]]:
        """Load data from JSON file"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except:
            return []

    def _save_table(self, file_path: Path, data: List[Dict[str, Any]]):
        """Save data to JSON file"""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    async def connect(self):
        """Mock connection - always succeeds for local files"""
        pass

    async def close(self):
        """Mock close - nothing to close for local files"""
        pass

    async def ensure_site(self, url: str) -> str:
        """Ensure site exists and return site_id"""
        sites = self._load_table(self.sites_file)

        # Check if site exists
        for site in sites:
            if site['url'] == url:
                return site['id']

        # Create new site
        site_id = str(uuid.uuid4())
        new_site = {
            'id': site_id,
            'url': url,
            'slug': url.lower().replace('https://', '').replace('http://', '').replace('/', '-'),
            'created_at': datetime.utcnow().isoformat()
        }

        sites.append(new_site)
        self._save_table(self.sites_file, sites)

        return site_id

    async def create_scan(self, site_id: str, subscription_tier: str = "free") -> str:
        """Create new scan and return scan_id"""
        scans = self._load_table(self.scans_file)

        scan_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        new_scan = {
            'id': scan_id,
            'site_id': site_id,
            'status': 'running',
            'subscription_tier': subscription_tier,
            'created_at': now,
            'started_at': now,
            'finished_at': None,
            'error': None
        }

        scans.append(new_scan)
        self._save_table(self.scans_file, scans)

        return scan_id

    async def finish_scan(self, scan_id: str, error: Optional[str] = None):
        """Mark scan as complete or error"""
        scans = self._load_table(self.scans_file)

        for scan in scans:
            if scan['id'] == scan_id:
                scan['status'] = 'error' if error else 'complete'
                scan['finished_at'] = datetime.utcnow().isoformat()
                scan['error'] = error
                break

        self._save_table(self.scans_file, scans)

    async def save_module(
        self,
        scan_id: str,
        module: str,
        data_source: str,
        confidence: float,
        duration_ms: int,
        result: Any,
        requires_credentials: bool = True,
        error: Optional[str] = None
    ) -> str:
        """Save scan module and analysis result"""

        # Save scan module
        scan_modules = self._load_table(self.scan_modules_file)
        module_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        new_module = {
            'id': module_id,
            'scan_id': scan_id,
            'module': module,
            'data_source': data_source,
            'confidence': confidence,
            'requires_credentials': requires_credentials,
            'duration_ms': duration_ms,
            'error': error,
            'created_at': now
        }

        scan_modules.append(new_module)
        self._save_table(self.scan_modules_file, scan_modules)

        # Save analysis result if we have data
        if result is not None:
            analysis_results = self._load_table(self.analysis_results_file)
            result_id = str(uuid.uuid4())

            new_result = {
                'id': result_id,
                'scan_module_id': module_id,
                'result': result,
                'created_at': now
            }

            analysis_results.append(new_result)
            self._save_table(self.analysis_results_file, analysis_results)

        return module_id

    async def get_scan_results(self, scan_id: str) -> List[Dict[str, Any]]:
        """Get all results for a scan"""
        scan_modules = self._load_table(self.scan_modules_file)
        analysis_results = self._load_table(self.analysis_results_file)

        # Filter modules for this scan
        scan_modules_filtered = [m for m in scan_modules if m['scan_id'] == scan_id]

        results = []
        for module in scan_modules_filtered:
            # Find corresponding analysis result
            module_result = None
            for result in analysis_results:
                if result['scan_module_id'] == module['id']:
                    module_result = result['result']
                    break

            result_dict = {
                'module': module['module'],
                'data_source': module['data_source'],
                'confidence': float(module['confidence']),
                'duration_ms': module['duration_ms'],
                'error': module['error'],
                'result': module_result
            }
            results.append(result_dict)

        return results

    async def initialize_schema(self):
        """Initialize schema - for local files, just ensure files exist"""
        self._initialize_files()
        print("Local database schema initialized (JSON files)")

    async def test_connection(self) -> Dict[str, Any]:
        """Test local file system access"""
        try:
            # Test file read/write access
            test_file = self.data_dir / "test.json"
            test_data = {"test": "data", "timestamp": datetime.utcnow().isoformat()}

            with open(test_file, 'w') as f:
                json.dump(test_data, f)

            with open(test_file, 'r') as f:
                loaded_data = json.load(f)

            # Clean up test file
            test_file.unlink()

            # Check existing tables
            table_files = [self.sites_file, self.scans_file, self.scan_modules_file, self.analysis_results_file]
            tables_exist = [f.exists() for f in table_files]
            table_names = ["sites", "scans", "scan_modules", "analysis_results"]

            return {
                'status': 'connected',
                'database_version': 'Local JSON File System v1.0',
                'current_time': datetime.utcnow().isoformat(),
                'tables_found': [name for name, exists in zip(table_names, tables_exist) if exists],
                'schema_ready': all(tables_exist),
                'data_directory': str(self.data_dir.absolute())
            }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def get_database_summary(self) -> Dict[str, Any]:
        """Get summary of all data in local database"""
        try:
            sites = self._load_table(self.sites_file)
            scans = self._load_table(self.scans_file)
            scan_modules = self._load_table(self.scan_modules_file)
            analysis_results = self._load_table(self.analysis_results_file)

            return {
                'total_sites': len(sites),
                'total_scans': len(scans),
                'total_modules': len(scan_modules),
                'total_results': len(analysis_results),
                'recent_scans': sorted(scans, key=lambda x: x['created_at'], reverse=True)[:5],
                'data_directory': str(self.data_dir.absolute())
            }
        except Exception as e:
            return {'error': str(e)}


# Global client instance
local_db_client = LocalDatabaseClient()