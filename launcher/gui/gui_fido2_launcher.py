#!/usr/bin/env python3
"""
FIDO2 GUI Launcher - Enterprise Edition

Handles FIDO2 dependency installation and GUI launching using the existing
configured virtual environment (outlook_venv).

Features:
- Uses existing outlook_venv virtual environment
- Installs FIDO2 dependencies if needed
- Launches FIDO2 GUI POC with proper timeout support
- Comprehensive error handling and logging
- Cross-platform compatibility

Author: Multi-Agent Security Team
Date: August 14, 2025
"""

import sys
import os
import subprocess
import logging
import argparse
import time
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
VENV_PATH = PROJECT_ROOT / "outlook_venv"
GUI_SCRIPT = PROJECT_ROOT / "gui_fido2_poc.py"


class FIDO2GUILauncher:
    """Launcher for FIDO2 GUI with dependency management"""
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        self.logger = logging.getLogger("FIDO2GUILauncher")
        self.venv_python = self._get_venv_python()
        
    def _get_venv_python(self):
        """Get path to virtual environment Python executable"""
        if sys.platform == "win32":
            python_exe = VENV_PATH / "Scripts" / "python.exe"
        else:
            python_exe = VENV_PATH / "bin" / "python"
            
        return python_exe
        
    def check_venv_exists(self):
        """Check if virtual environment exists"""
        if not VENV_PATH.exists() or not self.venv_python.exists():
            self.logger.error(f"Virtual environment not found at {VENV_PATH}")
            return False
        return True
        
    def install_fido2_dependencies(self):
        """Install FIDO2 dependencies in existing virtual environment"""
        self.logger.info("Installing FIDO2 dependencies...")
        
        # Basic required packages
        basic_packages = [
            'FreeSimpleGUI>=5.0.0',  # Ensure we have GUI support
            'cryptography>=41.0.0',   # Basic crypto support
            'argon2-cffi>=23.1.0',    # Password hashing
        ]
        
        # FIDO2 packages (optional - may fail on some systems)
        fido2_packages = [
            'fido2>=1.1.0',
            'pyscard>=2.0.7',
            'pyusb>=1.2.1',
        ]
        
        # Platform-specific packages
        platform_packages = []
        if sys.platform == "darwin":  # macOS
            platform_packages = [
                'pyobjc-core>=9.2',
                'pyobjc-framework-LocalAuthentication>=9.2',
                'pyobjc-framework-Security>=9.2'
            ]
        elif sys.platform == "win32":  # Windows
            platform_packages = [
                'pywin32>=306',
                'wincred>=1.1.0',
            ]
            
        # Install basic packages (required)
        success = True
        for package in basic_packages:
            if not self._install_package(package, required=True):
                success = False
                break
                
        # Install FIDO2 packages (optional)
        fido2_success = True
        for package in fido2_packages:
            if not self._install_package(package, required=False):
                fido2_success = False
                
        # Install platform packages (optional)  
        platform_success = True
        for package in platform_packages:
            if not self._install_package(package, required=False):
                platform_success = False
                
        # Summary
        if success:
            self.logger.info("✅ Basic dependencies installed successfully")
        else:
            self.logger.error("❌ Failed to install required dependencies")
            return False
            
        if fido2_success:
            self.logger.info("✅ FIDO2 hardware support installed")
        else:
            self.logger.warning("⚠️ FIDO2 hardware support not available (will use mock authentication)")
            
        if platform_packages and platform_success:
            self.logger.info(f"✅ Platform-specific support ({sys.platform}) installed")
        elif platform_packages:
            self.logger.warning(f"⚠️ Platform-specific support ({sys.platform}) not available")
            
        return True
        
    def _install_package(self, package: str, required: bool = False) -> bool:
        """Install a single package"""
        try:
            cmd = [str(self.venv_python), "-m", "pip", "install", package]
            
            if self.debug:
                self.logger.debug(f"Installing: {package}")
                result = subprocess.run(cmd, check=True, capture_output=False)
            else:
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                
            return result.returncode == 0
            
        except subprocess.CalledProcessError as e:
            if required:
                self.logger.error(f"❌ Failed to install required package {package}: {e}")
            else:
                self.logger.warning(f"⚠️ Optional package {package} not available: {e}")
            return False
        except Exception as e:
            if required:
                self.logger.error(f"❌ Error installing {package}: {e}")
            else:
                self.logger.warning(f"⚠️ Error installing optional package {package}: {e}")
            return False
            
    def verify_gui_dependencies(self):
        """Verify that GUI dependencies are available"""
        self.logger.info("Verifying GUI dependencies...")
        
        # Test FreeSimpleGUI import
        test_script = '''
import sys
try:
    import FreeSimpleGUI as sg
    print("✅ FreeSimpleGUI: Available")
    gui_available = True
except ImportError as e:
    print(f"❌ FreeSimpleGUI: Not available - {e}")
    gui_available = False

try:
    from pathlib import Path
    print("✅ pathlib: Available") 
    pathlib_available = True
except ImportError:
    print("❌ pathlib: Not available")
    pathlib_available = False

try:
    import secrets
    import hashlib
    print("✅ Cryptographic modules: Available")
    crypto_available = True
except ImportError:
    print("❌ Cryptographic modules: Not available")
    crypto_available = False

# Test our FIDO2 modules
try:
    sys.path.insert(0, "''' + str(PROJECT_ROOT) + '''")
    from test_hardware_fido2 import MockHardwareFIDO2Authenticator
    print("✅ FIDO2 Authenticator: Available")
    auth_available = True
except ImportError as e:
    print(f"⚠️ FIDO2 Authenticator: Mock only - {e}")
    auth_available = False

if gui_available and pathlib_available and crypto_available:
    print("\\n🎉 All required dependencies verified!")
    sys.exit(0)
else:
    print("\\n❌ Some required dependencies missing")  
    sys.exit(1)
'''
        
        try:
            result = subprocess.run([str(self.venv_python), "-c", test_script], 
                                  capture_output=True, text=True, check=False)
            
            print(result.stdout)
            if result.stderr:
                print("Warnings/Errors:", result.stderr)
                
            return result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"❌ Dependency verification failed: {e}")
            return False
            
    def launch_gui(self, timeout: int = 0):
        """Launch the FIDO2 GUI application"""
        if not GUI_SCRIPT.exists():
            self.logger.error(f"GUI script not found: {GUI_SCRIPT}")
            return 1
            
        self.logger.info(f"Launching FIDO2 GUI POC...")
        if timeout > 0:
            self.logger.info(f"⏱️ Auto-close timeout: {timeout} seconds")
            
        try:
            cmd = [str(self.venv_python), str(GUI_SCRIPT)]
            
            if timeout > 0:
                cmd.extend(["--timeout", str(timeout)])
                
            if self.debug:
                cmd.append("--debug")
                
            # Launch GUI
            start_time = time.time()
            result = subprocess.run(cmd, check=False)
            elapsed = time.time() - start_time
            
            self.logger.info(f"GUI completed after {elapsed:.1f} seconds")
            return result.returncode
            
        except Exception as e:
            self.logger.error(f"❌ Failed to launch GUI: {e}")
            return 1


def main():
    """Main launcher function"""
    parser = argparse.ArgumentParser(description='FIDO2 GUI Launcher')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode')
    parser.add_argument('--timeout', type=int, default=10,
                       help='GUI auto-close timeout in seconds (default: 10)')
    parser.add_argument('--skip-install', action='store_true',
                       help='Skip dependency installation')
    parser.add_argument('--force-install', action='store_true',
                       help='Force reinstall all dependencies')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 FIDO2 GUI Launcher - Enterprise Edition")
    print("=" * 50)
    print(f"🐍 Python: {sys.version.split()[0]}")
    print(f"🖥️ Platform: {sys.platform}")
    print(f"📁 Project Root: {PROJECT_ROOT}")
    print(f"🔧 Virtual Environment: {VENV_PATH}")
    print()
    
    launcher = FIDO2GUILauncher(debug=args.debug)
    
    # Check virtual environment
    if not launcher.check_venv_exists():
        print("❌ Virtual environment not found!")
        print(f"Expected location: {VENV_PATH}")
        print("Please run the main launcher to create the environment first:")
        print("  python launcher.py gui --force-recreate")
        return 1
        
    print("✅ Virtual environment found")
    
    # Install dependencies if needed
    if not args.skip_install:
        print("\n📦 Installing/updating dependencies...")
        if not launcher.install_fido2_dependencies():
            print("❌ Dependency installation failed!")
            return 1
            
        print("\n🔍 Verifying dependencies...")
        if not launcher.verify_gui_dependencies():
            print("❌ Dependency verification failed!")
            print("Some features may not work correctly.")
            # Continue anyway - mock authentication should still work
            
    else:
        print("⏭️ Skipping dependency installation")
        
    # Launch GUI
    print(f"\n🖥️ Launching FIDO2 GUI (timeout: {args.timeout}s)...")
    result = launcher.launch_gui(timeout=args.timeout)
    
    if result == 0:
        print("✅ FIDO2 GUI completed successfully")
    else:
        print(f"❌ FIDO2 GUI exited with code {result}")
        
    return result


if __name__ == "__main__":
    sys.exit(main())