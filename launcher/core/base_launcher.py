#!/usr/bin/env python3
"""
Base Launcher for Outlook Extractor
Provides common functionality for all launcher types (GUI, CLI, Build, Test)
"""

import os
import sys
import subprocess
import logging
import json
import time
from pathlib import Path
from typing import Optional, Tuple, List, Dict
from abc import ABC, abstractmethod

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from launcher.core.dependency_manager import DependencyManager

class BaseLauncher(ABC):
    """
    Abstract base class for all launchers
    Handles common tasks like venv management, dependency checking, etc.
    """
    
    def __init__(self, launcher_type: str = "base"):
        """
        Initialize base launcher
        
        Args:
            launcher_type: Type of launcher ('gui', 'cli', 'build', 'test', 'security')
        """
        self.launcher_type = launcher_type
        self.project_root = Path(__file__).parent.parent.parent
        self.venv_name = "outlook_venv"
        self.venv_path = self.project_root / self.venv_name
        
        # Setup logging
        self.setup_logging()
        
        # Initialize dependency manager
        self.dep_manager = DependencyManager(self.project_root)
        
        # Track if we need special dependencies
        self.needs_security_deps = launcher_type in ['build', 'security', 'test']
        self.needs_test_deps = launcher_type == 'test'
        self.needs_build_deps = launcher_type == 'build'
        
        self.logger.info(f"Initializing {launcher_type} launcher")
    
    def setup_logging(self):
        """Setup logging for the launcher"""
        log_file = self.project_root / f"{self.launcher_type}_launcher.log"
        
        # Create logger
        self.logger = logging.getLogger(f"{self.launcher_type}_launcher")
        self.logger.setLevel(logging.INFO)
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def find_python(self) -> Tuple[Optional[str], Optional[str]]:
        """Find suitable Python installation"""
        import shutil
        
        # Supported versions
        supported_versions = ["3.13", "3.12", "3.11", "3.10", "3.9", "3.8"]
        
        # Try py launcher on Windows
        if sys.platform == "win32":
            for version in supported_versions:
                try:
                    result = subprocess.run(
                        ['py', f'-{version}', '-c', 'import sys; print(sys.executable)'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        python_path = result.stdout.strip()
                        if Path(python_path).exists():
                            self.logger.info(f"Found Python {version}: {python_path}")
                            return python_path, version
                except Exception:
                    continue
        
        # Try common commands
        candidates = ["python3", "python"]
        if sys.platform == "darwin":  # macOS
            candidates = ["python3.13", "python3.12", "python3.11", "python3.10", "python3.9", "python3.8"] + candidates
        
        for candidate in candidates:
            path = shutil.which(candidate)
            if path:
                try:
                    result = subprocess.run(
                        [path, '-c', 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        version = result.stdout.strip()
                        if version in supported_versions:
                            self.logger.info(f"Found Python {version} at: {path}")
                            return path, version
                except Exception:
                    continue
        
        self.logger.error("No suitable Python version found")
        return None, None
    
    def get_venv_python(self) -> Path:
        """Get path to venv Python executable"""
        if sys.platform == "win32":
            return self.venv_path / "Scripts" / "python.exe"
        else:
            return self.venv_path / "bin" / "python"
    
    def check_venv_exists(self) -> Tuple[bool, Optional[Path]]:
        """Check if virtual environment exists and is valid"""
        venv_python = self.get_venv_python()
        
        if not venv_python.exists():
            return False, None
        
        # Check if validation is recent
        validation_file = self.venv_path / f".last_validation_{self.launcher_type}"
        skip_validation = False
        
        if validation_file.exists():
            try:
                last_validation = validation_file.stat().st_mtime
                current_time = time.time()
                days_since = (current_time - last_validation) / (24 * 3600)
                
                # Different validation periods for different launcher types
                validation_period = {
                    'gui': 7,      # Weekly for GUI
                    'cli': 7,      # Weekly for CLI
                    'build': 1,    # Daily for builds
                    'test': 3,     # Every 3 days for tests
                    'security': 1  # Daily for security
                }.get(self.launcher_type, 7)
                
                if days_since < validation_period:
                    skip_validation = True
                    self.logger.info(f"Skipping validation (checked {days_since:.1f} days ago)")
            except Exception:
                pass
        
        if not skip_validation:
            # Validate the environment
            if self.validate_venv(venv_python):
                # Update validation timestamp
                validation_file.touch()
                return True, venv_python
            else:
                return False, None
        
        return True, venv_python
    
    def validate_venv(self, venv_python: Path) -> bool:
        """
        Validate that venv has required dependencies
        Different validation for different launcher types
        """
        self.logger.info(f"Validating virtual environment for {self.launcher_type}")
        print(f"[VALIDATION] Checking virtual environment...")
        
        try:
            # Check core packages based on launcher type
            if self.launcher_type in ['gui', 'cli']:
                # Check application dependencies
                required = ['FreeSimpleGUI', 'pandas', 'openpyxl']
                check_cmd = f"import sys; import {'; import '.join(required)}"
                
            elif self.launcher_type == 'build':
                # Check build dependencies
                required = ['FreeSimpleGUI', 'pandas']
                check_cmd = f"import sys; import {'; import '.join(required)}"
                
            elif self.launcher_type == 'test':
                # Check test dependencies
                required = ['pytest']
                check_cmd = f"import sys; import {'; import '.join(required)}"
                
            elif self.launcher_type == 'security':
                # Security tools are optional (will be installed if needed)
                return True
            else:
                # Basic check
                check_cmd = "import sys; print(sys.version)"
            
            result = subprocess.run(
                [str(venv_python), '-c', check_cmd],
                capture_output=True,
                timeout=30
            )
            
            if result.returncode != 0:
                self.logger.warning("Validation failed - missing dependencies")
                print(f"[VALIDATION] Missing required packages - will install")
                return False
            
            self.logger.info("Virtual environment validated successfully")
            print(f"[VALIDATION] All required packages found")
            return True
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            return False
    
    def create_venv(self, force_recreate: bool = False) -> Optional[Path]:
        """Create virtual environment"""
        python_path, version = self.find_python()
        
        if not python_path:
            self.logger.error("Cannot create venv - no Python found")
            return None
        
        if self.venv_path.exists() and force_recreate:
            self.logger.info("Removing existing virtual environment")
            import shutil
            shutil.rmtree(self.venv_path)
        
        if not self.venv_path.exists():
            self.logger.info(f"Creating virtual environment with Python {version}")
            print(f"\n[SETUP] Creating virtual environment...")
            print(f"[SETUP] Using Python {version} at {python_path}")
            print(f"[SETUP] Location: {self.venv_path}")
            print(f"[SETUP] This may take a minute...\n")
            try:
                result = subprocess.run(
                    [python_path, '-m', 'venv', str(self.venv_path)],
                    timeout=120
                )
                
                if result.returncode != 0:
                    self.logger.error("Virtual environment creation failed")
                    return None
                    
            except Exception as e:
                self.logger.error(f"Failed to create venv: {e}")
                return None
        
        venv_python = self.get_venv_python()
        
        # Upgrade pip
        self.logger.info("Upgrading pip...")
        print(f"[SETUP] Upgrading pip to latest version...")
        result = subprocess.run(
            [str(venv_python), "-m", "pip", "install", "--upgrade", "pip"],
            capture_output=True,
            timeout=60
        )
        if result.returncode == 0:
            print(f"[SETUP] Pip upgraded successfully")
        else:
            print(f"[SETUP] Warning: Pip upgrade had issues but continuing")
        
        return venv_python
    
    def setup_dependencies(self, venv_python: Path) -> bool:
        """
        Setup dependencies based on launcher type
        This is where we handle the separation of concerns
        """
        self.logger.info(f"Setting up dependencies for {self.launcher_type} launcher")
        
        # Always install core dependencies
        if not self.dep_manager.install_dependencies('core', venv_python):
            self.logger.error("Failed to install core dependencies")
            return False
        
        # Install additional dependencies based on launcher type
        if self.launcher_type in ['gui', 'cli']:
            # Install AI dependencies for standard usage
            self.dep_manager.install_dependencies('ai_cpu', venv_python)
            
        elif self.launcher_type == 'build' and self.needs_security_deps:
            # Install security tools for build validation
            self.dep_manager.install_dependencies('security', venv_python)
            
        elif self.launcher_type == 'test' and self.needs_test_deps:
            # Install testing tools
            self.dep_manager.install_dependencies('test', venv_python)
            
        elif self.launcher_type == 'security':
            # Install security tools
            self.dep_manager.install_dependencies('security', venv_python)
        
        self.logger.info("Dependencies setup completed")
        return True
    
    def prepare_environment(self, force_recreate: bool = False) -> Optional[Path]:
        """
        Prepare the environment for launching
        Returns path to venv Python or None on failure
        """
        print(f"\n{'='*60}")
        print(f"OUTLOOK EXTRACTOR - {self.launcher_type.upper()} LAUNCHER")
        print(f"{'='*60}")
        
        # Check if venv exists and is valid
        exists, venv_python = self.check_venv_exists()
        
        if exists and not force_recreate:
            self.logger.info("Using existing virtual environment")
            print(f"[INFO] Found existing virtual environment")
            
            # Install any missing special dependencies
            if self.launcher_type == 'security' and self.needs_security_deps:
                # Check if security tools are installed
                installed = self.dep_manager.get_installed_packages(venv_python)
                if 'safety' not in installed:
                    self.logger.info("Installing security dependencies...")
                    self.dep_manager.install_dependencies('security', venv_python)
                    
            return venv_python
        
        # Create or recreate venv
        self.logger.info("Creating new virtual environment")
        print(f"\n[INFO] Setting up new environment...")
        print(f"[INFO] First-time setup will take 5-10 minutes")
        print(f"[INFO] Subsequent launches will be much faster\n")
        venv_python = self.create_venv(force_recreate)
        
        if not venv_python:
            return None
        
        # Setup dependencies
        if not self.setup_dependencies(venv_python):
            self.logger.error("Failed to setup dependencies")
            return None
        
        # Mark as validated
        validation_file = self.venv_path / f".last_validation_{self.launcher_type}"
        validation_file.touch()
        
        return venv_python
    
    @abstractmethod
    def launch(self, *args, **kwargs):
        """
        Abstract method that must be implemented by subclasses
        This is where the actual launch logic goes
        """
        pass
    
    def run(self, *args, **kwargs):
        """
        Main entry point for the launcher
        Prepares environment then launches
        """
        self.logger.info(f"Starting {self.launcher_type} launcher")
        
        # Prepare environment
        venv_python = self.prepare_environment(
            force_recreate=kwargs.get('force_recreate', False)
        )
        
        if not venv_python:
            self.logger.error("Failed to prepare environment")
            return 1
        
        # Launch the actual application/tool
        return self.launch(venv_python, *args, **kwargs)