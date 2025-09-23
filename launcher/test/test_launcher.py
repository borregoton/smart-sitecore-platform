#!/usr/bin/env python3
"""
Test Launcher for Outlook Extractor
Manages test execution with proper test dependencies
"""

import sys
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from launcher.core.base_launcher import BaseLauncher

class TestLauncher(BaseLauncher):
    """Launcher for running tests"""
    
    def __init__(self):
        super().__init__("test")
        self.tests_dir = self.project_root / "tests"
        
        # Test needs test dependencies
        self.needs_security_deps = False
        self.needs_test_deps = True
    
    def launch(self, venv_python: Path, *args, **kwargs):
        """Launch test suite"""
        test_type = kwargs.get('test_type', 'all')
        
        self.logger.info(f"Running {test_type} tests")
        
        # Make sure pytest is installed
        installed = self.dep_manager.get_installed_packages(venv_python)
        
        if 'pytest' not in installed:
            self.logger.info("Installing test dependencies...")
            if not self.dep_manager.install_dependencies('test', venv_python):
                self.logger.error("Failed to install test dependencies")
                return 1
        
        # Build pytest command
        cmd = [str(venv_python), "-m", "pytest"]
        
        # Add test directory or specific test
        if test_type == 'all':
            cmd.append(str(self.tests_dir))
        elif test_type == 'unit':
            cmd.append(str(self.tests_dir / "unit"))
        elif test_type == 'integration':
            cmd.append(str(self.tests_dir / "integration"))
        elif test_type == 'gui':
            cmd.append(str(self.tests_dir / "gui"))
        else:
            # Assume it's a specific test file
            cmd.append(test_type)
        
        # Add pytest options
        if kwargs.get('verbose'):
            cmd.append('-v')
        if kwargs.get('coverage'):
            cmd.extend(['--cov=.', '--cov-report=html'])
        if kwargs.get('markers'):
            cmd.extend(['-m', kwargs['markers']])
        
        # Add any additional arguments
        if args:
            cmd.extend(args)
        
        try:
            self.logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd)
            
            return result.returncode
            
        except Exception as e:
            self.logger.error(f"Failed to run tests: {e}")
            return 1


def main():
    """Main entry point"""
    import argparse
    import textwrap
    
    parser = argparse.ArgumentParser(
        prog='test_launcher',
        description=textwrap.dedent('''
            🧪 TEST SUITE LAUNCHER FOR OUTLOOK EXTRACTOR
            ─────────────────────────────────────────────
            
            Automated test execution with pytest framework.
            
            Features:
              • Automatic pytest installation
              • Coverage report generation
              • Test categorization (unit/integration/gui)
              • Marker-based test selection
              • Isolated test environment
            
            Test Organization:
              tests/
              ├── unit/        # Fast, isolated unit tests
              ├── integration/ # Integration tests
              ├── gui/         # GUI component tests
              └── fixtures/    # Test data and fixtures
            '''),
        epilog=textwrap.dedent('''
            TEST CATEGORIES:
            
              all (default):
                Run complete test suite
                Includes: unit + integration + gui
            
              unit:
                Fast, isolated component tests
                No external dependencies
                Runtime: ~30 seconds
            
              integration:
                Cross-component tests
                May use test database
                Runtime: ~2 minutes
            
              gui:
                GUI component tests
                Tests windows, dialogs, events
                Runtime: ~1 minute
            
              [specific file]:
                Run specific test file
                Example: tests/test_export.py
            
            PYTEST MARKERS:
            
              @pytest.mark.slow     - Long-running tests
              @pytest.mark.gui      - GUI-related tests
              @pytest.mark.db       - Database tests
              @pytest.mark.ai       - AI feature tests
              @pytest.mark.critical - Critical path tests
            
            EXAMPLES:
            
              Run all tests with coverage:
                %(prog)s all --coverage
            
              Run unit tests verbosely:
                %(prog)s unit -v
            
              Run specific test file:
                %(prog)s tests/unit/test_email_parser.py
            
              Run tests by marker:
                %(prog)s all -m "not slow"
                %(prog)s all -m "critical"
            
              Generate HTML coverage report:
                %(prog)s all --coverage --html-report
            
            COVERAGE OUTPUT:
              Terminal: Coverage percentage displayed
              HTML: htmlcov/index.html (if --html-report)
              XML: coverage.xml (for CI/CD)
            
            EXIT CODES:
              0 - All tests passed
              1 - Test failures
              2 - Test errors
              3 - Environment setup failed
            
            For test writing guide, see: docs/TESTING.md
            '''),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('test_type', 
                       nargs='?', 
                       default='all',
                       help='Test category (all/unit/integration/gui) or specific test file')
    
    parser.add_argument('-v', '--verbose', 
                       action='store_true',
                       help='Verbose test output with detailed assertions')
    
    parser.add_argument('--coverage', 
                       action='store_true',
                       help='Generate code coverage report')
    
    parser.add_argument('--html-report',
                       action='store_true',
                       help='Generate HTML coverage report in htmlcov/')
    
    parser.add_argument('-m', '--markers',
                       help='Run tests matching marker expression (e.g., "not slow")')
    
    parser.add_argument('--force-recreate', 
                       action='store_true',
                       help='Force recreation of test virtual environment')
    
    parser.add_argument('--fail-fast', '-x',
                       action='store_true',
                       help='Stop on first test failure')
    
    parser.add_argument('--last-failed',
                       action='store_true',
                       help='Run only tests that failed last time')
    
    parser.add_argument('--parallel', '-n',
                       type=int,
                       metavar='NUM',
                       help='Run tests in parallel with NUM workers')
    
    args, unknown_args = parser.parse_known_args()
    
    launcher = TestLauncher()
    
    return launcher.run(
        *unknown_args,
        test_type=args.test_type,
        verbose=args.verbose,
        coverage=args.coverage,
        markers=args.markers,
        force_recreate=args.force_recreate
    )


if __name__ == "__main__":
    sys.exit(main())