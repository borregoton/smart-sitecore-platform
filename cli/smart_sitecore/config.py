"""
Configuration Management for Smart Sitecore CLI
Project20 v2.0 - Real Data Only

Handles:
- Sitecore credentials storage
- Configuration file management
- Environment settings
- NO MOCK DATA - Real credentials only
"""

import os
import json
import keyring
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from urllib.parse import urlparse


@dataclass
class SitecoreCredentials:
    """Sitecore instance credentials"""
    url: str
    auth_type: str  # 'apikey' or 'basic'
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    domain: Optional[str] = None
    graphql_endpoint: Optional[str] = None

    def __post_init__(self):
        """Validate credentials after initialization"""
        if self.auth_type not in ['apikey', 'basic']:
            raise ValueError("auth_type must be 'apikey' or 'basic'")

        if self.auth_type == 'apikey' and not self.api_key:
            raise ValueError("api_key required for apikey auth")

        if self.auth_type == 'basic' and (not self.username or not self.password):
            raise ValueError("username and password required for basic auth")

        # Set default GraphQL endpoint if not provided
        if not self.graphql_endpoint:
            self.graphql_endpoint = '/sitecore/api/graph/edge'

    def get_full_graphql_url(self) -> str:
        """Get complete GraphQL endpoint URL"""
        base_url = self.url.rstrip('/')
        endpoint = self.graphql_endpoint.lstrip('/')
        return f"{base_url}/{endpoint}"

    def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for authentication"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Smart-Sitecore-CLI/2.0.0'
        }

        if self.auth_type == 'apikey' and self.api_key:
            headers['sc_apikey'] = self.api_key
        elif self.auth_type == 'basic' and self.username and self.password:
            import base64
            auth_string = f"{self.username}:{self.password}"
            if self.domain:
                auth_string = f"{self.domain}\\{self.username}:{self.password}"

            b64_auth = base64.b64encode(auth_string.encode()).decode()
            headers['Authorization'] = f'Basic {b64_auth}'

        return headers


class Config:
    """Configuration manager for Smart Sitecore CLI"""

    def __init__(self):
        self.config_dir = Path.home() / '.smart-sitecore'
        self.config_file = self.config_dir / 'config.json'
        self.data_dir = self.config_dir / 'data'

        # Create directories if they don't exist
        self.config_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)

        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        # Default configuration
        return {
            'version': '2.0.0',
            'settings': {
                'timeout': 30,
                'max_retries': 3,
                'concurrent_categories': 5,
                'save_results': True,
                'verbose': False
            },
            'sites': {}
        }

    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
        except IOError as e:
            raise RuntimeError(f"Failed to save configuration: {e}")

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting"""
        return self._config.get('settings', {}).get(key, default)

    def set_setting(self, key: str, value: Any):
        """Set a configuration setting"""
        if 'settings' not in self._config:
            self._config['settings'] = {}

        self._config['settings'][key] = value
        self._save_config()

    def get_data_dir(self) -> str:
        """Get data directory path"""
        return str(self.data_dir)

    def save_credentials(self, url: str, credentials: SitecoreCredentials):
        """Save credentials for a Sitecore site

        Args:
            url: Site URL (used as identifier)
            credentials: SitecoreCredentials object
        """
        # Normalize URL to use as key
        parsed = urlparse(url)
        site_key = f"{parsed.scheme}://{parsed.netloc}"

        # Store non-sensitive data in config file
        site_config = {
            'url': credentials.url,
            'auth_type': credentials.auth_type,
            'domain': credentials.domain,
            'graphql_endpoint': credentials.graphql_endpoint,
            'username': credentials.username if credentials.auth_type == 'basic' else None
        }

        self._config['sites'][site_key] = site_config
        self._save_config()

        # Store sensitive data in keyring
        service_name = f"smart-sitecore-{site_key}"

        if credentials.auth_type == 'apikey' and credentials.api_key:
            keyring.set_password(service_name, 'api_key', credentials.api_key)
        elif credentials.auth_type == 'basic' and credentials.password:
            keyring.set_password(service_name, 'password', credentials.password)

    def get_credentials(self, url: str) -> Optional[SitecoreCredentials]:
        """Get credentials for a Sitecore site

        Args:
            url: Site URL

        Returns:
            SitecoreCredentials if found, None otherwise
        """
        # Normalize URL to use as key
        parsed = urlparse(url)
        site_key = f"{parsed.scheme}://{parsed.netloc}"

        if site_key not in self._config.get('sites', {}):
            return None

        site_config = self._config['sites'][site_key]
        service_name = f"smart-sitecore-{site_key}"

        try:
            credentials = SitecoreCredentials(
                url=site_config['url'],
                auth_type=site_config['auth_type'],
                domain=site_config.get('domain'),
                graphql_endpoint=site_config.get('graphql_endpoint'),
                username=site_config.get('username')
            )

            # Retrieve sensitive data from keyring
            if credentials.auth_type == 'apikey':
                credentials.api_key = keyring.get_password(service_name, 'api_key')
            elif credentials.auth_type == 'basic':
                credentials.password = keyring.get_password(service_name, 'password')

            return credentials

        except (ValueError, KeyError):
            return None

    def list_sites(self) -> Dict[str, Dict[str, Any]]:
        """List all configured sites"""
        return self._config.get('sites', {})

    def remove_site(self, url: str) -> bool:
        """Remove a site configuration

        Args:
            url: Site URL

        Returns:
            True if removed, False if not found
        """
        parsed = urlparse(url)
        site_key = f"{parsed.scheme}://{parsed.netloc}"

        if site_key in self._config.get('sites', {}):
            # Remove from config
            del self._config['sites'][site_key]
            self._save_config()

            # Remove from keyring
            service_name = f"smart-sitecore-{site_key}"
            try:
                keyring.delete_password(service_name, 'api_key')
                keyring.delete_password(service_name, 'password')
            except keyring.errors.PasswordDeleteError:
                pass  # Password may not exist

            return True

        return False

    def validate_environment(self) -> Dict[str, bool]:
        """Validate CLI environment and dependencies"""
        checks = {}

        # Check Python version
        import sys
        checks['python_version'] = sys.version_info >= (3, 8)

        # Check keyring availability
        try:
            keyring.get_keyring()
            checks['keyring'] = True
        except Exception:
            checks['keyring'] = False

        # Check network connectivity (basic)
        try:
            import urllib.request
            urllib.request.urlopen('https://www.google.com', timeout=5)
            checks['network'] = True
        except Exception:
            checks['network'] = False

        # Check write permissions
        checks['config_writable'] = os.access(self.config_dir, os.W_OK)

        return checks


# Environment detection utilities
def is_sitecore_url(url: str) -> Dict[str, Any]:
    """Detect if URL is likely a Sitecore instance

    Args:
        url: URL to check

    Returns:
        Dict with detection results
    """
    import requests
    from urllib.parse import urljoin

    detection_result = {
        'is_sitecore': False,
        'confidence': 0,
        'evidence': [],
        'suggested_endpoints': []
    }

    try:
        # Check common Sitecore endpoints
        endpoints_to_check = [
            '/sitecore/api/graph/edge',
            '/sitecore/service/notfound.ashx',
            '/sitecore/shell/sitecore.version.xml',
            '/-/speak/v1/assets/favicon.ico'
        ]

        for endpoint in endpoints_to_check:
            try:
                test_url = urljoin(url, endpoint)
                response = requests.head(test_url, timeout=5)

                if response.status_code in [200, 401, 403]:
                    detection_result['evidence'].append(f"Found {endpoint}")
                    detection_result['confidence'] += 25

                    if 'graph/edge' in endpoint:
                        detection_result['suggested_endpoints'].append({
                            'type': 'GraphQL',
                            'url': test_url
                        })

            except requests.RequestException:
                continue

        # Check HTML for Sitecore indicators
        try:
            response = requests.get(url, timeout=10)
            html = response.text.lower()

            sitecore_indicators = [
                'sitecore',
                '/sitecore/shell',
                'scTrackingId',
                '__NEXT_DATA__',  # Next.js JSS
                'experience editor'
            ]

            for indicator in sitecore_indicators:
                if indicator in html:
                    detection_result['evidence'].append(f"Found '{indicator}' in HTML")
                    detection_result['confidence'] += 10

        except requests.RequestException:
            pass

        detection_result['is_sitecore'] = detection_result['confidence'] >= 50

    except Exception as e:
        detection_result['error'] = str(e)

    return detection_result


# Global config instance
_config_instance = None

def get_config() -> Config:
    """Get global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance