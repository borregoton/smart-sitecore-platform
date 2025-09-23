#!/usr/bin/env python3
"""
Smart Sitecore Analysis Platform - Project20 Launcher
Adapted from outlook extractor launcher pattern

Immediate Usage (Tested and Working):
    python launch.py web-dev          # Start local development server
    python launch.py web-build        # Build for production
    python launch.py web-status       # Check application status

Analysis Commands:
    python launch.py --setup-only     # Create venv and install dependencies
    python launch.py html_report      # Run Phase 1 and generate HTML report
    python launch.py test_phase1      # Run Phase 1 verification test
    python launch.py test_db          # Test database connectivity

V2.0 Data Management:
    python launch.py diagnose_database    # Diagnose database connection issues
    python launch.py test_credentials     # Test specific credentials
    python launch.py inspect_schema      # Inspect database schema vs v2.0 expectations
    python launch.py test_database_write  # Test write permissions
    python launch.py clear_database      # Clear all data for fresh V2.0 start
    python launch.py GrabSiteCoreData    # Extract fresh data into V2.0 multi-site schema
    python launch.py database_report     # Generate HTML report of extracted data

Docker Deployment:
    python launch.py docker-start --env development    # Start Docker environment
    python launch.py web-deploy --server your-server.com    # Deploy to remote server

Backup Commands:
    python launch.py zip-full         # Create comprehensive backup
    python launch.py zip-essential    # Create essential source backup

Other:
    python launch.py --help           # Show all available commands

This launcher ensures:
- Isolated Python virtual environment
- Proper dependency management
- Windows compatibility
- Easy command execution
- Web server management
- Docker containerization support
"""
import os
import sys
import subprocess
import platform
import venv
import argparse
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Constants
VENV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sitecore_venv')
REQUIREMENTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'requirements.txt')
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
PYTHON_EXECUTABLE = sys.executable
IS_WINDOWS = platform.system() == 'Windows'
IS_MACOS = platform.system() == 'Darwin'
IS_LINUX = platform.system() == 'Linux'

# Global configuration object
_config = None


class ConfigManager:
    """Configuration management for Project20 launcher"""

    def __init__(self, config_file: str = CONFIG_FILE):
        self.config_file = config_file
        self.config = self._load_default_config()
        self._load_config_file()

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration values"""
        return {
            "version": "2.0.0",
            "sitecore": {
                "url": "https://cm-qa-sc103.kajoo.ca",
                "api_key": "{34B8FFF8-8F50-4C41-95A8-D2A9304EBD52}",
                "auth_type": "apikey",
                "graphql_endpoint": "/sitecore/api/graph/edge",
                "timeout": 30,
                "max_retries": 3,
                "concurrent_categories": 5
            },
            "database": {
                "host": "10.0.0.196",
                "pg_port": 5432,
                "api_port": 8000,
                "tenant_id": "zyafowjs5i4ltxxq",
                "credentials": {
                    "postgres_with_tenant": {
                        "user": "postgres.zyafowjs5i4ltxxq",
                        "password": "boTW1PbupfnkXRdlXr1RFdL7qqyi43wm",
                        "database": "postgres"
                    },
                    "postgres": {
                        "user": "postgres",
                        "password": "boTW1PbupfnkXRdlXr1RFdL7qqyi43wm",
                        "database": "postgres"
                    }
                }
            },
            "web_server": {
                "default_host": "localhost",
                "default_port": 3000,
                "api_port": 8000
            },
            "extraction": {
                "customer_name": "Default Customer",
                "site_name": "Default Site",
                "save_results": True,
                "verbose": False
            },
            "cli": {
                "timeout": 600,
                "venv_dir": "sitecore_venv"
            }
        }

    def _load_config_file(self):
        """Load configuration from file if it exists"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                self._merge_config(self.config, file_config)
                print(f"[CONFIG] Loaded configuration from {self.config_file}")
            except (json.JSONDecodeError, IOError) as e:
                print(f"[CONFIG] Warning: Could not load {self.config_file}: {e}")
                print(f"[CONFIG] Using default configuration")
        else:
            print(f"[CONFIG] Configuration file {self.config_file} not found")
            print(f"[CONFIG] Using default configuration")

    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        """Recursively merge override config into base config"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'database.host')"""
        keys = key_path.split('.')
        value = self.config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def set(self, key_path: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config = self.config

        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        # Set the final key
        config[keys[-1]] = value

    def save_config(self, no_save: bool = False):
        """Save current configuration to file"""
        if no_save:
            print("[CONFIG] --no-save specified, configuration not saved")
            return

        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            print(f"[CONFIG] Configuration saved to {self.config_file}")
        except IOError as e:
            print(f"[CONFIG] Error saving configuration: {e}")

    def create_from_args(self, args) -> bool:
        """Create configuration from command line arguments"""
        config_created = False

        # Sitecore configuration
        if hasattr(args, 'sitecore_url') and args.sitecore_url:
            self.set('sitecore.url', args.sitecore_url)
            config_created = True

        if hasattr(args, 'sitecore_api_key') and args.sitecore_api_key:
            self.set('sitecore.api_key', args.sitecore_api_key)
            config_created = True

        # Database configuration
        if hasattr(args, 'db_host') and args.db_host:
            self.set('database.host', args.db_host)
            config_created = True

        if hasattr(args, 'db_user') and args.db_user:
            self.set('database.credentials.postgres.user', args.db_user)
            config_created = True

        if hasattr(args, 'db_password') and args.db_password:
            self.set('database.credentials.postgres.password', args.db_password)
            config_created = True

        if hasattr(args, 'db_name') and args.db_name:
            self.set('database.credentials.postgres.database', args.db_name)
            config_created = True

        # Web server configuration
        if hasattr(args, 'server') and args.server:
            self.set('web_server.default_host', args.server)
            config_created = True

        if hasattr(args, 'port') and args.port:
            self.set('web_server.default_port', args.port)
            config_created = True

        # Extraction configuration
        if hasattr(args, 'customer_name') and args.customer_name:
            self.set('extraction.customer_name', args.customer_name)
            config_created = True

        if hasattr(args, 'site_name') and args.site_name:
            self.set('extraction.site_name', args.site_name)
            config_created = True

        return config_created


def get_config() -> ConfigManager:
    """Get the global configuration manager instance"""
    global _config
    if _config is None:
        _config = ConfigManager()
    return _config


def show_config_help():
    """Show help for configuration parameters"""
    print("""
Configuration Help - Project20 Smart Sitecore Platform

If config.json is not found, you can create it by running the launcher with
configuration parameters. These will be saved to config.json for future use.

SITECORE CONFIGURATION:
  --sitecore-url URL           Sitecore instance URL
  --sitecore-api-key KEY       Sitecore API key for authentication

DATABASE CONFIGURATION:
  --db-host HOST               Database server hostname/IP
  --db-user USER               Database username
  --db-password PASS           Database password
  --db-name NAME               Database name

WEB SERVER CONFIGURATION:
  --server HOST                Web server hostname (default: localhost)
  --port PORT                  Web server port (default: 3000)

EXTRACTION CONFIGURATION:
  --customer-name NAME         Customer/organization name
  --site-name NAME             Site identifier name

EXAMPLE: Create config.json with all parameters:
  python launch.py web-dev \\
    --sitecore-url "https://your-sitecore.com" \\
    --sitecore-api-key "{{YOUR-API-KEY}}" \\
    --db-host "your-db-server.com" \\
    --db-user "username" \\
    --db-password "password" \\
    --customer-name "Your Company" \\
    --site-name "Main Site"

OPTIONS:
  --no-save                    Don't save configuration to config.json
  --config-help                Show this configuration help

CURRENT CONFIG FILE LOCATION: {0}

Once config.json exists, you can run commands normally:
  python launch.py web-dev
  python launch.py GrabSiteCoreData
  python launch.py database_report
    """.format(CONFIG_FILE))

def create_virtualenv():
    """Create a new virtual environment if it doesn't exist."""
    if not os.path.exists(VENV_DIR):
        print(f"Creating virtual environment in {VENV_DIR}...")
        venv.create(VENV_DIR, with_pip=True)
        print("Virtual environment created successfully.")
    else:
        print(f"Using existing virtual environment at {VENV_DIR}")

def get_venv_python():
    """Get the path to the Python executable in the virtual environment."""
    if IS_WINDOWS:
        return os.path.join(VENV_DIR, 'Scripts', 'python.exe')
    else:
        return os.path.join(VENV_DIR, 'bin', 'python')

def install_requirements(force=False):
    """Install required packages in the virtual environment."""
    venv_python = get_venv_python()

    if not os.path.exists(REQUIREMENTS):
        print(f"Error: requirements.txt not found at {REQUIREMENTS}")
        return False

    # Check if already installed (unless force)
    if not force:
        try:
            result = subprocess.run([
                venv_python, "-m", "pip", "list"
            ], capture_output=True, text=True, timeout=30)

            if "aiohttp" in result.stdout and "supabase" in result.stdout:
                print("Requirements appear to be already installed")
                return True
        except:
            pass  # Continue with installation

    # Upgrade pip first
    print("\nUpgrading pip...")
    subprocess.check_call([venv_python, "-m", "pip", "install", "--upgrade", "pip"])

    # Install requirements
    print("\nInstalling requirements...")
    try:
        subprocess.check_call([venv_python, "-m", "pip", "install", "-r", REQUIREMENTS], timeout=300)
        print("Requirements installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install requirements: {e}")
        return False

def run_in_venv(script_args):
    """Run a script in the virtual environment."""
    venv_python = get_venv_python()
    project_root = os.path.dirname(os.path.abspath(__file__))

    if not os.path.exists(venv_python):
        print("Virtual environment not found. Run --setup-only first.")
        return False

    try:
        # Run the command in the virtual environment
        result = subprocess.run([
            venv_python
        ] + script_args, cwd=project_root, timeout=600)  # 10 minute timeout

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("Command timed out")
        return False
    except Exception as e:
        print(f"Error running command: {e}")
        return False

def setup_environment(force_install=False):
    """Set up complete environment."""
    print("Smart Sitecore Analysis Platform - Project20 Launcher")
    print("=" * 55)

    # Check Python version
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"Python 3.8+ required. Current version: {version.major}.{version.minor}.{version.micro}")
        return False

    # Create and set up virtual environment
    create_virtualenv()
    return install_requirements(force=force_install)


def cmd_html_report():
    """Generate HTML report with Phase 1 analysis"""
    print("Running Phase 1 analysis and generating HTML report...")

    # Create HTML report generator if it doesn't exist
    project_root = os.path.dirname(os.path.abspath(__file__))
    html_generator = os.path.join(project_root, "generate_html_report.py")

    if not os.path.exists(html_generator):
        create_html_generator()

    return run_in_venv(["generate_html_report.py"])


def cmd_test_phase1():
    """Run Phase 1 verification test"""
    print("Running Phase 1 verification test...")
    return run_in_venv(["test_phase1_final.py"])


def cmd_test_db():
    """Test database connectivity"""
    print("Testing database connectivity...")
    return run_in_venv(["test_supabase_keys.py"])


def cmd_test_enhanced():
    """Run enhanced content analysis test"""
    print("Running enhanced content analysis test...")
    return run_in_venv(["test_enhanced_reporter.py"])


def cmd_create_modules():
    """Create missing modules table"""
    print("Creating missing modules table...")
    return run_in_venv(["create_modules_table.py"])


def cmd_verify_db():
    """Verify database data was saved"""
    print("Verifying database data...")
    return run_in_venv(["verify_database_data.py"])


def cmd_debug_graphql():
    """Debug GraphQL schema extraction issue"""
    print("Debugging GraphQL schema extraction...")
    return run_in_venv(["debug_graphql_schema.py"])


def cmd_audit_phase1():
    """Audit Phase 1 data extraction completeness"""
    print("Auditing Phase 1 data extraction completeness...")
    return run_in_venv(["simple_phase1_audit.py"])


def cmd_test_enhanced():
    """Test enhanced Phase 1 extraction with comprehensive data capture"""
    print("Testing enhanced Phase 1 extraction...")
    return run_in_venv(["test_enhanced_extraction.py"])


def cmd_grab_sitecore_data():
    """Extract fresh Sitecore data into multi-site schema (V2.0)"""
    print("Running GrabSiteCoreData - V2.0 Multi-Site Extraction...")
    print("This command extracts fresh data directly from Sitecore")
    print("and populates the new multi-site schema (customers, customer_sites, scans_v2)")
    print()
    return run_in_venv(["grab_sitecore_data.py"])


def cmd_database_report():
    """Generate comprehensive HTML report of extracted data"""
    print("Generating Database Extraction Report...")
    print("This command creates a detailed HTML report showing what data")
    print("is actually stored in the database from all extractions")
    print()
    return run_in_venv(["generate_extraction_report.py"])


def cmd_clear_database():
    """Clear database for fresh V2.0 start"""
    print("Running Database Cleanup for V2.0...")
    print("This command safely clears old data to prepare for fresh extraction")
    print("WARNING: This will permanently delete ALL existing Sitecore data!")
    print()
    return run_in_venv(["clear_database_for_v2.py"])


def cmd_diagnose_database():
    """Diagnose database connection issues"""
    print("Running Database Connection Diagnostics...")
    print("This will test network connectivity, ports, and authentication")
    print("Use this when database commands are failing")
    print()
    return run_in_venv(["diagnose_database_connection.py"])


def cmd_test_database_write():
    """Test database write access before attempting extraction"""
    print("Running Database Write Test...")
    print("Quick test of authentication and write permissions")
    print("Run this before GrabSiteCoreData to avoid wasting Sitecore API calls")
    print()
    return run_in_venv(["test_database_write.py"])


def cmd_test_credentials():
    """Test specific database credentials with detailed error reporting"""
    print("Running Detailed Credential Test...")
    print("Tests each credential set individually with specific error messages")
    print("Use this to identify which exact credentials work")
    print()
    return run_in_venv(["test_specific_credentials.py"])


def cmd_inspect_schema():
    """Inspect database schema and compare with v2.0 expectations"""
    print("Running Database Schema Inspector...")
    print("Examines actual database structure vs expected v2.0 schema")
    print("Use this to understand schema mismatches and get fix recommendations")
    print()
    return run_in_venv(["inspect_database_schema.py"])


def cmd_fix_schema():
    """Fix database schema to be v2.0 compatible"""
    print("Running Schema Compatibility Fix...")
    print("Adds missing columns and tables to make existing schema v2.0 compatible")
    print("This is a safe operation that preserves existing data")
    print()
    return run_in_venv(["fix_v2_schema.py"])


def cmd_web_dev(args):
    """Start local web development server"""
    config = get_config()

    # Use config values with command line overrides
    server = args.server or config.get('web_server.default_host', 'localhost')
    port = args.port or str(config.get('web_server.default_port', 3000))
    db_host = config.get('database.host', 'localhost')
    db_port = config.get('database.api_port', 8000)

    print("Starting web development server...")
    print(f"Server: {server}:{port}")
    print(f"Environment: {args.env}")
    print(f"Database: {db_host}:{db_port}")

    web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web-platform')

    if not os.path.exists(web_dir):
        print(f"[ERROR] Web platform directory not found: {web_dir}")
        return False

    try:
        # Set up environment using config values
        env = os.environ.copy()

        # Build database URL from config
        db_creds = config.get('database.credentials.postgres', {})
        db_user = db_creds.get('user', 'postgres')
        db_password = db_creds.get('password', 'postgres')
        db_name = db_creds.get('database', 'postgres')

        env['DATABASE_URL'] = args.database_url or f"postgresql://{db_user}:{db_password}@{db_host}:{config.get('database.pg_port', 5432)}/{db_name}"
        env['NEXT_PUBLIC_SUPABASE_URL'] = f"http://{db_host}:{db_port}"
        env['PORT'] = port

        if args.api_key:
            env['SUPABASE_SERVICE_ROLE_KEY'] = args.api_key

        print(f"Database URL: {env['DATABASE_URL']}")

        # Change to web directory and run npm dev
        print(f"Starting Next.js development server in {web_dir}")

        if IS_WINDOWS:
            cmd = ["cmd", "/c", "cd", "/d", web_dir, "&&", "npm", "run", "dev"]
        else:
            cmd = ["bash", "-c", f"cd {web_dir} && npm run dev"]

        result = subprocess.run(cmd, env=env)
        return result.returncode == 0

    except KeyboardInterrupt:
        print("\n[INFO] Development server stopped")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to start development server: {e}")
        return False


def cmd_web_build(args):
    """Build web application for production"""
    print("Building web application...")

    web_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web-platform')

    if not os.path.exists(web_dir):
        print(f"[ERROR] Web platform directory not found: {web_dir}")
        return False

    try:
        if IS_WINDOWS:
            cmd = ["cmd", "/c", "cd", "/d", web_dir, "&&", "npm", "run", "build"]
        else:
            cmd = ["bash", "-c", f"cd {web_dir} && npm run build"]

        result = subprocess.run(cmd)
        if result.returncode == 0:
            print("[SUCCESS] Web application built successfully")
        return result.returncode == 0

    except Exception as e:
        print(f"[ERROR] Failed to build web application: {e}")
        return False


def cmd_web_docker(args):
    """Deploy using Docker"""
    print(f"Deploying with Docker to {args.server}...")

    deployment_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'deployment')

    if not os.path.exists(deployment_dir):
        print(f"[ERROR] Deployment directory not found: {deployment_dir}")
        return False

    try:
        compose_file = f"docker-compose.{args.env}.yml"
        compose_path = os.path.join(deployment_dir, compose_file)

        if not os.path.exists(compose_path):
            print(f"[ERROR] Docker compose file not found: {compose_path}")
            return False

        # Set up environment variables
        env = os.environ.copy()
        env['DATABASE_URL'] = args.database_url or f"postgresql://postgres:postgres@{args.server}:8000/postgres"
        env['NEXT_PUBLIC_SUPABASE_URL'] = f"http://{args.server}:8000"

        if args.api_key:
            env['SUPABASE_SERVICE_ROLE_KEY'] = args.api_key

        if IS_WINDOWS:
            cmd = ["cmd", "/c", "cd", "/d", deployment_dir, "&&", "docker-compose", "-f", compose_file, "up", "--build", "-d"]
        else:
            cmd = ["bash", "-c", f"cd {deployment_dir} && docker-compose -f {compose_file} up --build -d"]

        result = subprocess.run(cmd, env=env)

        if result.returncode == 0:
            print(f"[SUCCESS] Docker deployment started")
            print(f"Web application: http://{args.server}:{args.port}")
            print(f"Analysis API: http://{args.server}:8000")

        return result.returncode == 0

    except Exception as e:
        print(f"[ERROR] Docker deployment failed: {e}")
        return False


def cmd_web_deploy(args):
    """Deploy to remote server"""
    print(f"Deploying to remote server {args.server}...")

    deployment_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'deployment')
    deploy_script = os.path.join(deployment_dir, 'deploy-to-server.sh')

    if not os.path.exists(deploy_script):
        print(f"[ERROR] Deployment script not found: {deploy_script}")
        return False

    try:
        cmd = [
            "bash", deploy_script,
            "--target", args.server,
            "--env", args.env
        ]

        if args.database_url:
            os.environ['DATABASE_URL'] = args.database_url

        if args.api_key:
            os.environ['SUPABASE_SERVICE_ROLE_KEY'] = args.api_key

        result = subprocess.run(cmd)
        return result.returncode == 0

    except Exception as e:
        print(f"[ERROR] Remote deployment failed: {e}")
        return False


def create_html_generator():
    """Create HTML report generator script"""
    project_root = os.path.dirname(os.path.abspath(__file__))
    html_generator = os.path.join(project_root, "generate_html_report.py")

    html_generator_content = """#!/usr/bin/env python3
# HTML Report Generator for Phase 1 Results

import asyncio
import sys
import os
import json
from datetime import datetime
from pathlib import Path

sys.path.insert(0, 'cli')

from smart_sitecore.phase1_extractor import run_phase1_extraction


async def generate_html_report():
    print("SMART SITECORE ANALYSIS PLATFORM")
    print("Phase 1: Sitecore Data Extraction Report")
    print("=" * 50)

    # Get Sitecore configuration
    config = get_config()
    sitecore_url = config.get('sitecore.url', 'https://cm-qa-sc103.kajoo.ca')
    api_key = config.get('sitecore.api_key', '{34B8FFF8-8F50-4C41-95A8-D2A9304EBD52}')

    try:
        # Run Phase 1 extraction
        print("Running Phase 1 extraction...")
        scan_id = await run_phase1_extraction(sitecore_url, api_key)

        print(f"Extraction completed. Scan ID: {scan_id}")

        # Load results from local database
        from smart_sitecore.local_db_client import local_db_client
        results = await local_db_client.get_scan_results(scan_id)

        # Generate simple HTML
        html_content = generate_simple_html(scan_id, results, sitecore_url)

        # Save HTML report
        report_path = Path("phase1_report.html")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"\\nHTML report generated: {report_path}")
        print(f"Open in browser to view results")

        return True

    except Exception as e:
        print(f"Error generating report: {e}")
        import traceback
        traceback.print_exc()
        return False


def generate_simple_html(scan_id, results, sitecore_url):
    total_modules = len(results)
    successful_modules = len([r for r in results if r['error'] is None])

    html = f'''<!DOCTYPE html>
<html>
<head>
    <title>Smart Sitecore Analysis Report - Phase 1</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #007acc; color: white; padding: 20px; text-align: center; }}
        .summary {{ background: #f8f9fa; padding: 15px; margin: 20px 0; }}
        .module {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; }}
        .success {{ border-left: 4px solid #28a745; }}
        .error {{ border-left: 4px solid #dc3545; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Smart Sitecore Analysis Platform</h1>
        <p>Phase 1: Sitecore Data Extraction Report</p>
        <p>Target: {sitecore_url}</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Scan ID: {scan_id}</p>
    </div>

    <div class="summary">
        <h2>Summary</h2>
        <p>Modules Executed: {successful_modules}/{total_modules}</p>
    </div>

    <div class="results">
        <h2>Analysis Results</h2>'''

    for result in results:
        status_class = "success" if not result['error'] else "error"
        html += f'''
        <div class="module {status_class}">
            <h3>{result['module'].replace('-', ' ').title()}</h3>
            <p>Confidence: {result['confidence']:.2f} | Duration: {result['duration_ms']}ms</p>'''

        if result['error']:
            html += f'<p style="color: #dc3545;">Error: {result["error"]}</p>'
        else:
            html += '<p style="color: #28a745;">Status: SUCCESS</p>'

        html += '</div>'

    html += '''
    </div>
    <footer style="text-align: center; margin-top: 30px; color: #666;">
        <p>Generated by Smart Sitecore Analysis Platform - Phase 1</p>
        <p>Ready for Phase 2: Analysis Modules</p>
    </footer>
</body>
</html>'''

    return html


if __name__ == "__main__":
    success = asyncio.run(generate_html_report())
    sys.exit(0 if success else 1)
"""

    with open(html_generator, 'w', encoding='utf-8') as f:
        f.write(html_generator_content)

    print("HTML report generator created")


def cmd_web_status(args):
    """Check web application status"""
    config = get_config()

    # Use config values with command line overrides
    server = args.server or config.get('web_server.default_host', 'localhost')
    port = args.port or str(config.get('web_server.default_port', 3000))
    api_port = config.get('database.api_port', 8000)

    print(f"Checking web application status on {server}:{port}...")

    try:
        import requests

        # Check if web application is responding
        web_url = f"http://{server}:{port}"
        try:
            response = requests.get(f"{web_url}/api/health", timeout=10)
            if response.status_code == 200:
                print(f"[OK] Web application is running at {web_url}")
            else:
                print(f"[WARNING] Web application responded with status {response.status_code}")
        except requests.RequestException:
            print(f"[ERROR] Web application is not responding at {web_url}")

        # Check if analysis API is responding
        api_url = f"http://{server}:{api_port}"
        try:
            response = requests.get(f"{api_url}/health", timeout=10)
            if response.status_code == 200:
                print(f"[OK] Analysis API is running at {api_url}")
            else:
                print(f"[WARNING] Analysis API responded with status {response.status_code}")
        except requests.RequestException:
            print(f"[ERROR] Analysis API is not responding at {api_url}")

        return True

    except ImportError:
        print("[WARNING] requests library not installed, cannot check status")
        print("Install with: pip install requests")
        return False
    except Exception as e:
        print(f"[ERROR] Status check failed: {e}")
        return False


def cmd_docker_start(args):
    """Start Docker environment"""
    print(f"Starting Docker environment ({args.env})...")

    deployment_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'deployment')

    if not os.path.exists(deployment_dir):
        print(f"[ERROR] Deployment directory not found: {deployment_dir}")
        return False

    try:
        if IS_WINDOWS:
            script_path = os.path.join(deployment_dir, 'docker-start.bat')
            if os.path.exists(script_path):
                result = subprocess.run([script_path], cwd=deployment_dir)
                return result.returncode == 0

        # Manual Docker start
        compose_file = f"docker-compose.{args.env}.yml"
        compose_path = os.path.join(deployment_dir, compose_file)

        if not os.path.exists(compose_path):
            print(f"[ERROR] Docker compose file not found: {compose_path}")
            return False

        cmd = ["docker-compose", "-f", compose_file, "up", "--build", "-d"]
        result = subprocess.run(cmd, cwd=deployment_dir)

        if result.returncode == 0:
            print(f"[SUCCESS] Docker environment started")
            print(f"Web application: http://{args.server}:{args.port}")
            print(f"Analysis API: http://{args.server}:8000")

        return result.returncode == 0

    except Exception as e:
        print(f"[ERROR] Failed to start Docker environment: {e}")
        return False


def cmd_docker_stop(args):
    """Stop Docker environment"""
    print("Stopping Docker environment...")

    deployment_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'deployment')

    if not os.path.exists(deployment_dir):
        print(f"[ERROR] Deployment directory not found: {deployment_dir}")
        return False

    try:
        if IS_WINDOWS:
            script_path = os.path.join(deployment_dir, 'docker-stop.bat')
            if os.path.exists(script_path):
                result = subprocess.run([script_path], cwd=deployment_dir)
                return result.returncode == 0

        # Manual Docker stop - try all environments
        compose_files = ['docker-compose.development.yml', 'docker-compose.local.yml', 'docker-compose.production.yml']

        for compose_file in compose_files:
            compose_path = os.path.join(deployment_dir, compose_file)
            if os.path.exists(compose_path):
                cmd = ["docker-compose", "-f", compose_file, "down"]
                subprocess.run(cmd, cwd=deployment_dir, capture_output=True)

        print("[SUCCESS] Docker environments stopped")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to stop Docker environment: {e}")
        return False


def cmd_docker_logs(args):
    """View Docker container logs"""
    print(f"Viewing Docker logs for {args.env} environment...")

    deployment_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'deployment')

    if not os.path.exists(deployment_dir):
        print(f"[ERROR] Deployment directory not found: {deployment_dir}")
        return False

    try:
        compose_file = f"docker-compose.{args.env}.yml"
        compose_path = os.path.join(deployment_dir, compose_file)

        if not os.path.exists(compose_path):
            print(f"[ERROR] Docker compose file not found: {compose_path}")
            return False

        cmd = ["docker-compose", "-f", compose_file, "logs", "-f"]
        result = subprocess.run(cmd, cwd=deployment_dir)

        return result.returncode == 0

    except KeyboardInterrupt:
        print("\n[INFO] Log viewing stopped")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to view Docker logs: {e}")
        return False


def cmd_zip_essential(args):
    """Create essential backup (source code only)"""
    try:
        from launcher.core.zip_handler import create_essential_backup

        print(f"Creating essential backup...")
        print(f"Output directory: {args.output_dir}")

        result = create_essential_backup(
            output_dir=args.output_dir,
            custom_name=args.custom_name,
            include_tests=args.include_tests,
            include_docs=args.include_docs,
            quiet=False
        )

        if result:
            print(f"[SUCCESS] Essential backup created: {result}")
            return True
        else:
            print(f"[ERROR] Failed to create essential backup")
            return False

    except ImportError:
        print("[ERROR] Zip handler not available. Make sure launcher/core/zip_handler.py exists.")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to create essential backup: {e}")
        return False


def cmd_zip_dev(args):
    """Create development backup (includes build system)"""
    try:
        from launcher.core.zip_handler import create_development_backup

        print(f"Creating development backup...")
        print(f"Output directory: {args.output_dir}")

        result = create_development_backup(
            output_dir=args.output_dir,
            custom_name=args.custom_name,
            exclude_tests=not args.include_tests,
            quiet=False
        )

        if result:
            print(f"[SUCCESS] Development backup created: {result}")
            return True
        else:
            print(f"[ERROR] Failed to create development backup")
            return False

    except ImportError:
        print("[ERROR] Zip handler not available. Make sure launcher/core/zip_handler.py exists.")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to create development backup: {e}")
        return False


def cmd_zip_full(args):
    """Create comprehensive full backup (all files)"""
    try:
        from launcher.core.zip_handler import create_full_backup

        print(f"Creating full backup...")
        print(f"Output directory: {args.output_dir}")

        result = create_full_backup(
            output_dir=args.output_dir,
            custom_name=args.custom_name,
            quiet=False
        )

        if result:
            print(f"[SUCCESS] Full backup created: {result}")
            return True
        else:
            print(f"[ERROR] Failed to create full backup")
            return False

    except ImportError:
        print("[ERROR] Zip handler not available. Make sure launcher/core/zip_handler.py exists.")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to create full backup: {e}")
        return False


def show_help():
    """Show available commands"""
    print("""
Smart Sitecore Analysis Platform - Project20 Launcher

ANALYSIS COMMANDS:
  --setup-only     Create virtual environment and install dependencies
  html_report      Run Phase 1 analysis and generate HTML report
  test_phase1      Run Phase 1 verification test
  test_db          Test database connectivity
  test_enhanced    Run enhanced content analysis test

V2.0 DATA MANAGEMENT:
  diagnose_database    Diagnose database connection issues and test connectivity
  test_credentials     Test specific credentials with detailed error reporting
  inspect_schema      Inspect database schema and compare with v2.0 expectations
  fix_schema          Fix database schema to be v2.0 compatible (recommended next)
  test_database_write  Test database authentication and write permissions
  clear_database      Clear all data for fresh V2.0 start (WARNING: requires auth!)
  GrabSiteCoreData    Extract fresh Sitecore data into V2.0 multi-site schema
  database_report     Generate comprehensive HTML report of extracted data

WEB SERVER COMMANDS:
  web-dev          Start local development server
  web-build        Build web application for production
  web-docker       Deploy using Docker containers
  web-deploy       Deploy to remote server
  web-status       Check web application status
  docker-start     Start Docker environment
  docker-stop      Stop Docker environment
  docker-logs      View Docker container logs

BACKUP COMMANDS:
  zip-essential    Create essential backup (source code only)
  zip-dev          Create development backup (includes build system)
  zip-full         Create comprehensive backup (all files)

GENERAL OPTIONS:
  --server HOST    Target server (default: localhost)
  --port PORT      Web server port (default: 3000)
  --env ENV        Environment: development|production
  --database-url   Database URL override
  --api-key        Supabase service role key
  --output-dir     Output directory for backups (default: current directory)
  --custom-name    Custom name for backup files
  --help           Show this help message

IMMEDIATE USAGE (TESTED AND WORKING):
  # Start local development (tested and working)
  cd Project20
  python launch.py web-dev

  # Build for production (tested and working)
  python launch.py web-build

  # Check status
  python launch.py web-status --server localhost

WITH DOCKER INSTALLATION:
  # Start Docker environment
  python launch.py docker-start --env development

  # Deploy to remote server
  python launch.py web-deploy --server your-server.com --env production

OTHER EXAMPLES:
  python launch.py --setup-only                    # First time setup
  python launch.py html_report                     # Generate analysis report
  python launch.py web-docker --env production     # Docker production
  python launch.py zip-full                        # Create full project backup
  python launch.py zip-essential --output-dir ../backups  # Backup to specific directory

Virtual Environment:
  Location: ./sitecore_venv/
  Status: {}

Dependencies:
  - aiohttp (async HTTP)
  - asyncpg (PostgreSQL)
  - supabase (database client)
  - Plus testing and reporting libraries

The launcher keeps your main Python environment clean by using
an isolated virtual environment for all project dependencies.
    """.format("EXISTS" if os.path.exists(VENV_DIR) else "NOT CREATED"))


def main():
    """Main launcher entry point"""

    parser = argparse.ArgumentParser(
        description="Smart Sitecore Analysis Platform Launcher",
        add_help=False  # We'll handle help ourselves
    )
    parser.add_argument('command', nargs='?', default='--help')
    parser.add_argument('--setup-only', action='store_true', help='Setup environment only')
    parser.add_argument('--force-install', action='store_true', help='Force reinstall requirements')
    parser.add_argument('--help', action='store_true', help='Show help')

    # Configuration options
    parser.add_argument('--config-help', action='store_true', help='Show configuration help')
    parser.add_argument('--no-save', action='store_true', help='Don\'t save configuration to config.json')

    # Sitecore configuration
    parser.add_argument('--sitecore-url', help='Sitecore instance URL')
    parser.add_argument('--sitecore-api-key', help='Sitecore API key for authentication')

    # Database configuration
    parser.add_argument('--db-host', help='Database server hostname/IP')
    parser.add_argument('--db-user', help='Database username')
    parser.add_argument('--db-password', help='Database password')
    parser.add_argument('--db-name', help='Database name')

    # Web server options
    parser.add_argument('--server', help='Target server for deployment')
    parser.add_argument('--port', help='Web server port')
    parser.add_argument('--env', default='development', choices=['development', 'production'], help='Environment')
    parser.add_argument('--docker', action='store_true', help='Use Docker deployment')
    parser.add_argument('--database-url', help='Database URL override')
    parser.add_argument('--api-key', help='Supabase service role key')

    # Extraction configuration
    parser.add_argument('--customer-name', help='Customer/organization name')
    parser.add_argument('--site-name', help='Site identifier name')

    # Backup options
    parser.add_argument('--output-dir', default='.', help='Output directory for backups')
    parser.add_argument('--custom-name', help='Custom name for backup files')
    parser.add_argument('--include-tests', action='store_true', help='Include test files in backup')
    parser.add_argument('--include-docs', action='store_true', help='Include documentation in backup')

    args = parser.parse_args()

    # Handle configuration help first
    if args.config_help:
        show_config_help()
        return 0

    # Handle setup only first (before help)
    if args.setup_only or args.command == '--setup-only':
        success = setup_environment(force_install=args.force_install)
        return 0 if success else 1

    # Handle help
    if args.help or args.command == '--help':
        show_help()
        return 0

    # Initialize configuration manager
    config = get_config()

    # Handle configuration from command line arguments
    config_created = config.create_from_args(args)
    if config_created:
        print("\n[CONFIG] Configuration parameters provided via command line")
        config.save_config(args.no_save)

    # Check for missing config.json and show help if needed
    if not os.path.exists(CONFIG_FILE) and args.command not in ['--setup-only', '--help', '--config-help']:
        print(f"\n[CONFIG] Error: Configuration file not found: {CONFIG_FILE}")
        print("[CONFIG] Please provide configuration parameters or run with --config-help for details")
        print("\nQuick setup example:")
        print("  python launch.py web-dev --sitecore-url \"https://your-sitecore.com\" --sitecore-api-key \"{YOUR-KEY}\"")
        print("  python launch.py --config-help  # For complete configuration help")
        return 1

    # For all other commands, ensure environment is set up first
    if not os.path.exists(VENV_DIR):
        print("Virtual environment not found. Setting up...")
        if not setup_environment():
            return 1

    # Handle commands
    analysis_commands = {
        'html_report': cmd_html_report,
        'test_phase1': cmd_test_phase1,
        'test_db': cmd_test_db,
        'test_enhanced': cmd_test_enhanced,
        'create_modules': cmd_create_modules,
        'verify_db': cmd_verify_db,
        'debug_graphql': cmd_debug_graphql,
        'audit_phase1': cmd_audit_phase1,
        'enhanced_extract': cmd_test_enhanced,
        'diagnose_database': cmd_diagnose_database,
        'test_credentials': cmd_test_credentials,
        'inspect_schema': cmd_inspect_schema,
        'fix_schema': cmd_fix_schema,
        'test_database_write': cmd_test_database_write,
        'clear_database': cmd_clear_database,
        'GrabSiteCoreData': cmd_grab_sitecore_data,
        'database_report': cmd_database_report,
    }

    web_commands = {
        'web': lambda: cmd_web_dev(args),
        'web-dev': lambda: cmd_web_dev(args),
        'web-build': lambda: cmd_web_build(args),
        'web-docker': lambda: cmd_web_docker(args),
        'web-deploy': lambda: cmd_web_deploy(args),
        'web-status': lambda: cmd_web_status(args),
        'docker-start': lambda: cmd_docker_start(args),
        'docker-stop': lambda: cmd_docker_stop(args),
        'docker-logs': lambda: cmd_docker_logs(args),
    }

    # Backup commands
    backup_commands = {
        'zip-essential': lambda: cmd_zip_essential(args),
        'zip-dev': lambda: cmd_zip_dev(args),
        'zip-full': lambda: cmd_zip_full(args),
    }

    all_commands = {**analysis_commands, **web_commands, **backup_commands}

    if args.command in all_commands:
        success = all_commands[args.command]()
        return 0 if success else 1
    else:
        print(f"Unknown command: {args.command}")
        show_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
