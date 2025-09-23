#!/usr/bin/env python3
"""
GUI Launcher for Outlook Extractor
Launches the main GUI application with proper dependencies
"""

import sys
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from launcher.core.base_launcher import BaseLauncher

class GUILauncher(BaseLauncher):
    """Launcher for the GUI application"""
    
    def __init__(self):
        super().__init__("gui")
        self.main_script = self.project_root / "outlook_extractor_gui.py"
        
        # GUI doesn't need security or test dependencies
        self.needs_security_deps = False
        self.needs_test_deps = False
    
    def launch(self, venv_python: Path, *args, **kwargs):
        """Launch the GUI application"""
        self.logger.info("Launching Outlook Extractor GUI")
        
        # Build command
        cmd = [str(venv_python), str(self.main_script)]
        
        # Add any additional arguments
        if args:
            cmd.extend(args)
        
        try:
            # Launch GUI
            self.logger.info(f"Executing: {' '.join(cmd)}")
            result = subprocess.run(cmd)
            
            return result.returncode
            
        except KeyboardInterrupt:
            self.logger.info("GUI terminated by user")
            return 0
        except Exception as e:
            self.logger.error(f"Failed to launch GUI: {e}")
            return 1


def main():
    """Main entry point"""
    import argparse
    import textwrap
    
    parser = argparse.ArgumentParser(
        prog='gui_launcher',
        description=textwrap.dedent('''
            🕹️  OUTLOOK EXTRACTOR GUI LAUNCHER
            ────────────────────────────────────
            
            Launch the Outlook Extractor graphical user interface.
            
            Features:
              • Email extraction from Outlook
              • AI-powered summarization
              • Multiple export formats (Excel, CSV, JSON, HTML)
              • Advanced filtering and search
              • Batch processing capabilities
            
            The GUI provides:
              • Tabbed interface for easy navigation
              • Real-time progress indicators
              • Export preview and validation
              • Comprehensive settings management
              • Integrated help system
            '''),
        epilog=textwrap.dedent('''
            GUI TABS:
            
              Email Extraction:
                - Connect to Outlook
                - Select folders and date ranges
                - Apply filters (sender, subject, etc.)
                - Extract emails with attachments
            
              AI Summary:
                - Generate intelligent summaries
                - Thread conversation analysis
                - Key points extraction
                - Sentiment analysis
            
              Export:
                - Multiple format support
                - Custom templates
                - Batch export
                - Data validation
            
              Settings:
                - AI model configuration
                - Export preferences
                - Performance tuning
                - Debug options
            
            DEBUG MODE:
            
              When --debug is enabled:
                • Verbose logging to console
                • Debug menu in GUI
                • Performance metrics
                • Memory usage tracking
                • SQL query logging
            
            ENVIRONMENT:
            
              The launcher automatically:
                1. Creates/validates virtual environment
                2. Installs required dependencies
                3. Configures platform-specific settings
                4. Launches the GUI application
            
            TROUBLESHOOTING:
            
              GUI won't start:
                - Try: %(prog)s --force-recreate
                - Check: outlook_extractor_launcher.log
            
              Import errors:
                - FreeSimpleGUI issues: Run with --force-recreate
                - Missing dependencies: Launcher will auto-install
            
              Performance issues:
                - Enable debug mode: --debug
                - Check memory usage in debug menu
                - Review SQL query performance
            
            EXAMPLES:
            
              Normal launch:
                %(prog)s
            
              Debug mode:
                %(prog)s --debug
            
              Clean reinstall:
                %(prog)s --force-recreate
            
              With custom config:
                %(prog)s --config settings.json
            
            LOG FILES:
              GUI log: outlook_extractor_gui.log
              Launcher log: gui_launcher.log
              Error log: outlook_extractor_errors.log
            
            For user manual, see: docs/USER_GUIDE.md
            '''),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--force-recreate', 
                       action='store_true',
                       help='Force recreation of virtual environment (clean install)')
    
    parser.add_argument('--debug', 
                       action='store_true',
                       help='Enable debug mode with verbose logging and debug menu')
    
    parser.add_argument('--config',
                       type=str,
                       help='Path to custom configuration file (JSON format)')
    
    parser.add_argument('--no-splash',
                       action='store_true',
                       help='Skip splash screen on startup')
    
    parser.add_argument('--theme',
                       choices=['default', 'dark', 'light', 'blue'],
                       default='default',
                       help='GUI theme (default: system theme)')
    
    parser.add_argument('--scale',
                       type=float,
                       default=1.0,
                       help='GUI scaling factor for high-DPI displays (default: 1.0)')
    
    parser.add_argument('--maximized',
                       action='store_true',
                       help='Start with maximized window')
    
    args, unknown_args = parser.parse_known_args()
    
    launcher = GUILauncher()
    
    # Pass through any unknown arguments to the GUI
    return launcher.run(
        *unknown_args,
        force_recreate=args.force_recreate
    )


if __name__ == "__main__":
    sys.exit(main())