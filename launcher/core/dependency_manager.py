#!/usr/bin/env python3
"""
Enterprise Dependency Manager for Outlook Extractor
Handles separation of application, build, and security dependencies
Ensures clean builds without contamination from development/security tools
"""

import os
import sys
import subprocess
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DependencyManager:
    """
    Manages different dependency sets for various purposes:
    - Application dependencies (for runtime)
    - Build dependencies (for PyInstaller)
    - Security dependencies (for validation)
    - Test dependencies (for testing)
    """
    
    # Dependency sets that should NEVER be in production builds
    EXCLUDE_FROM_BUILD = {
        # Security tools
        'safety', 'bandit', 'pip-audit', 'gitleaks',
        'safety-schemas', 'dparse', 'cyclonedx-python-lib',
        'license-expression', 'packageurl-python',
        
        # Testing tools
        'pytest', 'pytest-cov', 'pytest-mock', 'pytest-timeout',
        'coverage', 'tox', 'hypothesis',
        
        # Development tools
        'black', 'flake8', 'mypy', 'pylint', 'isort',
        'pre-commit', 'autopep8', 'yapf',
        
        # Build tools (not needed in final executable)
        # Note: pyinstaller is needed for building, moved to CORE_DEPENDENCIES
        'py2exe', 'cx-freeze', 'nuitka',
        'wheel', 'build', 'twine',
        
        # Documentation tools
        'sphinx', 'mkdocs', 'pdoc', 'pydoc-markdown'
    }
    
    # Core application dependencies (always needed)
    CORE_DEPENDENCIES = {
        'setuptools': '>=65.0.0',  # Required for pkg_resources
        'pyinstaller': '>=6.0.0',  # Required for building executables
        'FreeSimpleGUI': '>=5.0.0',
        'pandas': '>=2.0.0',
        'openpyxl': '>=3.1.0',
        'matplotlib': '>=3.5.0',
        'numpy': '>=1.24.0',
        'requests': '>=2.28.0',
        'python-dateutil': '>=2.8.0',
        'pytz': '*',
        'xlsxwriter': '>=3.0.0',
        'beautifulsoup4': '>=4.12.0',
        'lxml': '>=4.9.0',
        'colorama': '>=0.4.6',
        'tqdm': '>=4.65.0',
        'psutil': '>=5.9.0',           # Process and system utilities
        'tzlocal': '>=5.2.0',          # Local timezone information
        'chardet': '>=5.2.0',          # Character encoding detection
        'jsonschema': '>=4.0.0',       # JSON schema validation
        'coloredlogs': '>=15.0',       # Colored logging output
        'html2text': '>=2020.1.16',    # HTML to text conversion
        'pyperclip': '>=1.8.2',        # Clipboard operations
        'unicodedata2': '>=14.0.0',    # Unicode character database
        'textstat': '>=0.7.0',         # Text readability metrics
        'seaborn': '>=0.12.0',         # Statistical data visualization
        # Office 365 / Microsoft Graph API dependencies (CRITICAL FOR OWA)
        'msal': '>=1.24.0',           # Microsoft Authentication Library
        'msal-extensions': '>=1.0.0', # MSAL token caching extensions
        'exchangelib': '>=5.4.0',     # Exchange Web Services support
    }
    
    # Platform-specific core dependencies
    PLATFORM_DEPENDENCIES = {
        'win32': {
            'pywin32': '>=305',
            'pywin32-ctypes': '>=0.2.0'
        },
        'darwin': {
            # macOS specific if needed
        },
        'linux': {
            # Linux specific if needed
        }
    }
    
    # AI dependencies (optional based on edition)
    AI_DEPENDENCIES = {
        'cpu': {
            'transformers': '>=4.30.0',
            'nltk': '>=3.8',
            'sumy': '>=0.11.0',
            'scikit-learn': '>=1.3.0',
            'tokenizers': '>=0.13.0',
            'sentencepiece': '>=0.1.99'
        },
        'cuda': {
            'torch': {'index': 'https://download.pytorch.org/whl/cu121'},
            'torchvision': {'index': 'https://download.pytorch.org/whl/cu121'},
            'accelerate': '>=0.20.0',
            'datasets': '>=2.12.0',
            'spacy': '>=3.5.0'
        },
        'mps': {
            'torch': {'index': 'https://download.pytorch.org/whl/cpu'},  # MPS uses CPU wheel
            'accelerate': '>=0.20.0',
            'datasets': '>=2.12.0'
        }
    }
    
    # Security/validation dependencies (never in production)
    SECURITY_DEPENDENCIES = {
        'safety': '>=3.0.0',
        'bandit': '>=1.7.0',
        'pip-audit': '>=2.0.0'
    }
    
    # Testing dependencies
    TEST_DEPENDENCIES = {
        'pytest': '>=7.0.0',
        'pytest-cov': '>=4.0.0',
        'pytest-timeout': '>=2.1.0',
        'pytest-mock': '>=3.10.0'
    }
    
    def __init__(self, project_root: Path = None):
        """Initialize dependency manager"""
        self.project_root = project_root or Path(__file__).parent.parent.parent
        self.venv_path = self.project_root / "outlook_venv"
        self.dep_cache_file = self.project_root / ".dependency_cache.json"
        self.load_cache()
        
    def load_cache(self):
        """Load dependency cache for faster operations"""
        if self.dep_cache_file.exists():
            try:
                with open(self.dep_cache_file, 'r') as f:
                    self.cache = json.load(f)
            except:
                self.cache = {}
        else:
            self.cache = {}
    
    def save_cache(self):
        """Save dependency cache"""
        with open(self.dep_cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def get_venv_python(self) -> Path:
        """Get the Python executable in the virtual environment"""
        if sys.platform == "win32":
            return self.venv_path / "Scripts" / "python.exe"
        else:
            return self.venv_path / "bin" / "python"
    
    def get_installed_packages(self, venv_python: Path = None) -> Dict[str, str]:
        """Get currently installed packages in the venv"""
        if venv_python is None:
            venv_python = self.get_venv_python()
        
        try:
            result = subprocess.run(
                [str(venv_python), "-m", "pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                packages = json.loads(result.stdout)
                return {pkg['name'].lower(): pkg['version'] for pkg in packages}
        except Exception as e:
            logger.error(f"Failed to get installed packages: {e}")
        
        return {}
    
    def install_dependencies(self, dep_set: str, venv_python: Path = None) -> bool:
        """
        Install a specific set of dependencies
        
        Args:
            dep_set: One of 'core', 'ai_cpu', 'ai_cuda', 'ai_mps', 'security', 'test'
            venv_python: Path to venv Python executable
        """
        if venv_python is None:
            venv_python = self.get_venv_python()
        
        deps_to_install = {}
        
        # Determine which dependencies to install
        if dep_set == 'core':
            deps_to_install = self.CORE_DEPENDENCIES.copy()
            # Add platform-specific dependencies
            platform = sys.platform
            if platform in self.PLATFORM_DEPENDENCIES:
                deps_to_install.update(self.PLATFORM_DEPENDENCIES[platform])
                
        elif dep_set.startswith('ai_'):
            ai_type = dep_set.replace('ai_', '')
            if ai_type in self.AI_DEPENDENCIES:
                deps_to_install = self.AI_DEPENDENCIES[ai_type].copy()
            else:
                logger.error(f"Unknown AI dependency set: {ai_type}")
                return False
                
        elif dep_set == 'security':
            deps_to_install = self.SECURITY_DEPENDENCIES.copy()
            
        elif dep_set == 'test':
            deps_to_install = self.TEST_DEPENDENCIES.copy()
        else:
            logger.error(f"Unknown dependency set: {dep_set}")
            return False
        
        # Install the dependencies
        total_packages = len(deps_to_install)
        logger.info(f"Installing {dep_set} dependencies ({total_packages} packages)...")
        print(f"\n{'='*60}")
        print(f"Installing {dep_set.upper()} dependencies")
        print(f"Total packages to install: {total_packages}")
        print(f"This may take 5-10 minutes on first setup...")
        print(f"{'='*60}\n")
        
        current_package = 0
        for package, version_spec in deps_to_install.items():
            current_package += 1
            # Handle special cases (like PyTorch with index URL)
            if isinstance(version_spec, dict):
                index_url = version_spec.get('index', '')
                cmd = [str(venv_python), "-m", "pip", "install"]
                if index_url:
                    cmd.extend(["-f", index_url])
                cmd.append(package)
            else:
                if version_spec and version_spec != '*':
                    package_spec = f"{package}{version_spec}"
                else:
                    package_spec = package
                cmd = [str(venv_python), "-m", "pip", "install", package_spec]
            
            try:
                # Display progress to user
                print(f"[{current_package}/{total_packages}] Installing {package}...", end='', flush=True)
                logger.info(f"Installing {package}...")
                
                # Run pip install
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode != 0:
                    print(f" [FAILED]")
                    logger.error(f"Failed to install {package}: {result.stderr}")
                    print(f"  Error: {result.stderr[:200]}..." if len(result.stderr) > 200 else f"  Error: {result.stderr}")
                    return False
                else:
                    print(f" [OK]")
                    
            except subprocess.TimeoutExpired:
                print(f" [TIMEOUT]")
                logger.error(f"Installation of {package} timed out")
                return False
            except Exception as e:
                print(f" [ERROR]")
                logger.error(f"Failed to install {package}: {e}")
                return False
        
        print(f"\n{'='*60}")
        print(f"[SUCCESS] All {dep_set} dependencies installed!")
        print(f"{'='*60}\n")
        logger.info(f"Successfully installed {dep_set} dependencies")
        return True
    
    def remove_excluded_packages(self, venv_python: Path = None) -> bool:
        """
        Remove packages that should not be in production builds
        This is called before building executables
        """
        if venv_python is None:
            venv_python = self.get_venv_python()
        
        installed = self.get_installed_packages(venv_python)
        to_remove = []
        
        # Find packages to remove
        for package in installed:
            if package.lower() in {p.lower() for p in self.EXCLUDE_FROM_BUILD}:
                to_remove.append(package)
        
        if not to_remove:
            logger.info("No excluded packages to remove")
            return True
        
        logger.info(f"Removing {len(to_remove)} excluded packages for clean build...")
        
        for package in to_remove:
            try:
                logger.info(f"Removing {package}...")
                result = subprocess.run(
                    [str(venv_python), "-m", "pip", "uninstall", "-y", package],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode != 0:
                    logger.warning(f"Failed to remove {package}: {result.stderr}")
                    
            except Exception as e:
                logger.warning(f"Failed to remove {package}: {e}")
        
        logger.info("Package cleanup completed")
        return True
    
    def create_clean_build_env(self, edition: str = 'standard') -> Optional[Path]:
        """
        Create a clean virtual environment for building
        This ensures no contamination from dev/security tools
        
        Args:
            edition: 'lite', 'standard', 'pro_mac', 'pro_cuda'
        
        Returns:
            Path to the clean venv Python executable
        """
        build_venv = self.project_root / f"build_env_{edition}"
        
        # Determine which Python version to use based on edition
        if edition in ['pro', 'pro_cuda']:
            # Pro edition needs Python 3.11 for AI library compatibility
            python_exe = r"C:\Program Files\Python311\python.exe"
            required_version = "3.11"
        else:
            # lite, standard, pro_mac use Python 3.12
            python_exe = r"C:\Program Files\Python312\python.exe"
            required_version = "3.12"
        
        # Check if the Python executable exists
        if sys.platform == "win32" and not Path(python_exe).exists():
            logger.error(f"Python {required_version} not found at {python_exe}")
            logger.info(f"Falling back to system Python: {sys.executable}")
            python_exe = sys.executable
        elif sys.platform != "win32":
            # On non-Windows, use system Python
            python_exe = sys.executable
        
        # Check if build env already exists and reuse it
        if build_venv.exists():
            logger.info(f"Found existing build environment: {build_venv}")
            # Get venv Python
            if sys.platform == "win32":
                build_python = build_venv / "Scripts" / "python.exe"
            else:
                build_python = build_venv / "bin" / "python"
            
            # Verify it's valid and has the right Python version
            if build_python.exists():
                # Check Python version in the venv
                try:
                    result = subprocess.run(
                        [str(build_python), "--version"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    venv_version = result.stdout.strip()
                    logger.info(f"Existing build environment has {venv_version}")
                    
                    # Check if it's the right major.minor version
                    if f"Python {required_version}" in venv_version:
                        logger.info(f"Reusing existing build environment with correct Python version")
                        return build_python
                    else:
                        logger.warning(f"Build environment has wrong Python version, recreating with Python {required_version}...")
                        import shutil
                        shutil.rmtree(build_venv)
                except Exception as e:
                    logger.warning(f"Could not check Python version: {e}, recreating...")
                    import shutil
                    shutil.rmtree(build_venv)
            else:
                logger.warning(f"Build environment exists but Python not found, recreating...")
                import shutil
                shutil.rmtree(build_venv)
        
        # Create new clean environment only if needed
        logger.info(f"Creating new build environment: {build_venv} using Python {required_version}")
        try:
            subprocess.run(
                [python_exe, "-m", "venv", str(build_venv)],
                check=True,
                timeout=120
            )
        except Exception as e:
            logger.error(f"Failed to create build environment: {e}")
            return None
        
        # Get venv Python
        if sys.platform == "win32":
            build_python = build_venv / "Scripts" / "python.exe"
        else:
            build_python = build_venv / "bin" / "python"
        
        # Upgrade pip
        subprocess.run(
            [str(build_python), "-m", "pip", "install", "--upgrade", "pip"],
            capture_output=True,
            timeout=60
        )
        
        # Install only necessary dependencies based on edition
        logger.info(f"Installing dependencies for {edition} edition...")
        
        # Always install core
        if not self.install_dependencies('core', build_python):
            logger.error("Failed to install core dependencies")
            return None
        
        # Install AI dependencies based on edition
        if edition == 'standard':
            self.install_dependencies('ai_cpu', build_python)
        elif edition == 'pro_mac':
            self.install_dependencies('ai_mps', build_python)
        elif edition == 'pro_cuda':
            self.install_dependencies('ai_cuda', build_python)
        # 'lite' gets only core dependencies
        
        logger.info(f"Clean build environment ready: {build_venv}")
        return build_python
    
    def validate_build_env(self, venv_python: Path) -> bool:
        """
        Validate that a build environment is clean (no dev/security tools)
        """
        installed = self.get_installed_packages(venv_python)
        
        contamination = []
        for package in installed:
            if package.lower() in {p.lower() for p in self.EXCLUDE_FROM_BUILD}:
                contamination.append(package)
        
        if contamination:
            logger.warning(f"Build environment contaminated with: {contamination}")
            return False
        
        logger.info("Build environment is clean")
        return True
    
    def get_requirements_for_edition(self, edition: str) -> List[str]:
        """
        Get the list of requirements for a specific edition
        Returns a list of package specifications
        """
        requirements = []
        
        # Add core dependencies
        for package, version in self.CORE_DEPENDENCIES.items():
            if version and version != '*':
                requirements.append(f"{package}{version}")
            else:
                requirements.append(package)
        
        # Add platform-specific
        platform = sys.platform
        if platform in self.PLATFORM_DEPENDENCIES:
            for package, version in self.PLATFORM_DEPENDENCIES[platform].items():
                if version and version != '*':
                    requirements.append(f"{package}{version}")
                else:
                    requirements.append(package)
        
        # Add AI dependencies based on edition
        if edition == 'standard':
            for package, version in self.AI_DEPENDENCIES['cpu'].items():
                if isinstance(version, dict):
                    requirements.append(package)  # Special handling needed
                elif version and version != '*':
                    requirements.append(f"{package}{version}")
                else:
                    requirements.append(package)
                    
        elif edition == 'pro_mac':
            for package, version in self.AI_DEPENDENCIES['mps'].items():
                if isinstance(version, dict):
                    requirements.append(package)
                elif version and version != '*':
                    requirements.append(f"{package}{version}")
                else:
                    requirements.append(package)
                    
        elif edition == 'pro_cuda':
            for package, version in self.AI_DEPENDENCIES['cuda'].items():
                if isinstance(version, dict):
                    requirements.append(package)
                elif version and version != '*':
                    requirements.append(f"{package}{version}")
                else:
                    requirements.append(package)
        
        return requirements