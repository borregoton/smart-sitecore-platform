#!/usr/bin/env python3
"""
Essential Backup Handler for Outlook Extractor
Creates minimal backups containing only source code and documentation
"""

import os
import sys
import zipfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional


def create_essential_backup(
    output_dir: str = '.',
    custom_name: Optional[str] = None,
    include_tests: bool = False,
    include_docs: bool = False,
    quiet: bool = False
) -> Optional[str]:
    """
    Create an essential backup of the project containing only necessary files.
    
    Args:
        output_dir: Directory to save the backup zip file
        custom_name: Custom name for the zip file (without extension)
        include_tests: Include test files in backup
        include_docs: Include all documentation including PDFs
        quiet: Suppress progress output
        
    Returns:
        Path to created zip file or None if failed
    """
    try:
        # Get project root (parent of launcher directory)
        project_root = Path(__file__).parent.parent.parent
        project_name = project_root.name
        
        # Ensure output directory exists
        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if custom_name:
            zip_filename = f"{custom_name}.zip"
        else:
            zip_filename = f"{project_name}-essential-{timestamp}.zip"
        
        zip_path = output_path / zip_filename
        
        if not quiet:
            print(f"[ZIP] Creating essential backup of {project_name}...")
            print(f"   Project: {project_root}")
            print(f"   Output: {zip_path}")
        
        # Define file patterns to include
        include_patterns = [
            '*.py',     # Python source files
            '*.txt',    # Text files (but NOT .md unless docs requested)
            '*.json',   # JSON configs
            '*.ini',    # INI configs
            '*.yaml',   # YAML configs
            '*.yml',    # YAML configs (alternate extension)
            '*.toml',   # TOML configs
            '*.cfg',    # Config files
            '*.conf',   # Config files
            '*.bat',    # Batch scripts
            '*.sh',     # Shell scripts
            '*.ps1',    # PowerShell scripts
            'LICENSE',  # License file
            '.gitignore',  # Git ignore file
            '.dockerignore',  # Docker ignore file
            'requirements*.txt',  # Requirements files
            'package.json',  # Node package file
            'package-lock.json',  # Node lock file
            'tsconfig.json',  # TypeScript config
            'next.config.js',  # Next.js config
            'tailwind.config.js',  # Tailwind config
            'postcss.config.js',  # PostCSS config
            '*.tsx',    # TypeScript React files
            '*.ts',     # TypeScript files
            '*.jsx',    # React files
            '*.js',     # JavaScript files
            '*.css',    # Stylesheets
            'Dockerfile*',  # Docker files
            'docker-compose*.yml',  # Docker compose files
            'Dockerfile',  # Main Dockerfile
            'CLAUDE.md',  # Claude project instructions
        ]
        
        # Only add documentation if explicitly requested
        if include_docs:
            include_patterns.extend(['*.md', '*.pdf', '*.docx', '*.doc'])
        
        # Define exclusion patterns
        exclude_dirs = [
            '__pycache__',
            '.git',
            '.vscode',
            '.idea',
            'node_modules',
            '.next',
            'build',
            'dist',
            'out',
            'sitecore_venv',
            'sitecore_venv_*',  # Any venv variant
            'venv',
            'venv_*',
            'env',
            'build_env_*',
            'backups',
            'archive',
            'archived',
            'output',
            'reports',
            'exported_emails',
            'test_output',
            '.pytest_cache',
            '*.egg-info',
            'coverage',
            '.nyc_output',
            'logs',
            'traces',
        ]
        
        if not include_tests:
            exclude_dirs.extend(['tests', 'test_*'])
        
        exclude_files = [
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '*.so',
            '*.dll',
            '*.dylib',
            '*.sqlite',
            '*.sqlite-*',
            '*.db',
            '*.log',
            '*.csv',
            '*.xlsx',
            '*.xls',
            '*.html',
            '*.zip',
            '*.7z',
            '*.tar',
            '*.gz',
            '*.bz2',
            '*.rar',
            '.DS_Store',
            'Thumbs.db',
            '*.swp',
            '*.swo',
            '*~',
        ]
        
        # Use Python's zipfile module for cross-platform compatibility
        if not quiet:
            print("   Creating zip archive...")
        
        # Import for pattern matching
        import fnmatch
        
        # Function to check if path should be excluded
        def should_exclude(path_str):
            # Normalize path for comparison
            norm_path = path_str.replace('\\', '/')
            
            # Check directory exclusions
            for pattern in exclude_dirs:
                # Handle wildcard patterns
                if '*' in pattern:
                    # Check each part of the path
                    for path_part in norm_path.split('/'):
                        if fnmatch.fnmatch(path_part, pattern):
                            return True
                else:
                    # Check if path starts with or contains the excluded dir
                    if norm_path == pattern or norm_path.startswith(f'{pattern}/') or f'/{pattern}/' in norm_path:
                        return True
            
            # Check file exclusions
            for pattern in exclude_files:
                if fnmatch.fnmatch(os.path.basename(path_str), pattern):
                    return True
            
            return False
        
        # Function to check if path should be included
        def should_include(path_str):
            if not include_patterns:
                return True
            
            basename = os.path.basename(path_str)
            for pattern in include_patterns:
                # Match against basename for file patterns
                if fnmatch.fnmatch(basename, pattern):
                    return True
                # Also check full path for patterns like requirements*.txt
                if '*' in pattern and fnmatch.fnmatch(path_str, pattern):
                    return True
            return False
        
        # Create zip file
        file_count = 0
        try:
            # Use str for zip_path to ensure compatibility
            with zipfile.ZipFile(str(zip_path), 'w', zipfile.ZIP_DEFLATED) as zf:
                # Walk through project directory
                for root, dirs, files in os.walk(project_root):
                    # Get relative path
                    rel_root = os.path.relpath(root, project_root)
                    
                    # Skip if this directory should be excluded
                    if rel_root != '.' and should_exclude(rel_root.replace('\\', '/')):
                        dirs.clear()  # Don't walk subdirectories
                        continue
                    
                    # Filter directories to walk
                    dirs[:] = [d for d in dirs if not should_exclude(f'{rel_root}/{d}'.replace('\\', '/'))]
                    
                    # Add files
                    for file in files:
                        # Skip Windows reserved names at file level
                        file_lower = file.lower()
                        if file_lower in ['nul', 'con', 'prn', 'aux', 'com1', 'com2', 'com3', 'com4',
                                        'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9',
                                        '_nul', '_con', '_prn', '_aux']:
                            if not quiet:
                                print(f"   Skipping Windows reserved name: {file}")
                            continue
                        
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, project_root).replace('\\', '/')
                        
                        # Check if file should be included
                        if should_exclude(rel_path):
                            continue
                        
                        if not should_include(rel_path):
                            continue
                        
                        # Add file to zip
                        try:
                            # Use os.path.abspath instead of Path.resolve() to avoid mount issues
                            abs_file_path = os.path.abspath(file_path)
                            # Skip Windows reserved names
                            basename = os.path.basename(rel_path).lower()
                            if basename in ['nul', 'con', 'prn', 'aux', 'com1', 'com2', 'com3', 'com4', 
                                          'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9']:
                                if not quiet:
                                    print(f"   Skipping Windows reserved name: {rel_path}")
                                continue
                            zf.write(abs_file_path, rel_path)
                            file_count += 1
                        except Exception as write_err:
                            if not quiet:
                                print(f"   Warning: Could not add {rel_path}: {write_err}")
                            continue
                        
                        # Show progress for large archives
                        if not quiet and file_count % 100 == 0:
                            print(f"   Added {file_count} files...")
            
            # Get file size
            size_mb = zip_path.stat().st_size / (1024 * 1024)
            
            if not quiet:
                print(f"   Size: {size_mb:.1f}MB")
                print(f"   Files: {file_count}")
            
            return str(zip_path)
            
        except Exception as e:
            print(f"[ERROR] Failed to create zip: {e}")
            if zip_path.exists():
                zip_path.unlink()
            return None
            
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_development_backup(
    output_dir: str = '.',
    custom_name: Optional[str] = None,
    exclude_tests: bool = False,
    quiet: bool = False
) -> Optional[str]:
    """
    Create a comprehensive development backup including all development infrastructure.
    
    This backup includes all essential files plus:
    - Build system and deployment scripts
    - Agent specifications and orchestration
    - CI/CD configurations
    - PyInstaller specifications
    - Test infrastructure (unless excluded)
    - Development requirements
    - Security validation scripts
    
    Args:
        output_dir: Directory to save the backup zip file
        custom_name: Custom name for the zip file (without extension)
        exclude_tests: Exclude test files from backup
        quiet: Suppress progress output
        
    Returns:
        Path to created zip file or None if failed
    """
    try:
        # Get project root (parent of launcher directory)
        project_root = Path(__file__).parent.parent.parent
        project_name = project_root.name
        
        # Ensure output directory exists
        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if custom_name:
            zip_filename = f"{custom_name}.zip"
        else:
            zip_filename = f"{project_name}-development-{timestamp}.zip"
        
        zip_path = output_path / zip_filename
        
        if not quiet:
            print(f"[ZIP] Creating development backup of {project_name}...")
            print(f"   Project: {project_root}")
            print(f"   Output: {zip_path}")
            print(f"   Type: Development (includes all infrastructure)")
        
        # Define file patterns to include (comprehensive list)
        include_patterns = [
            '*.py',     # Python source files
            '*.md',     # Markdown documentation
            '*.txt',    # Text files
            '*.json',   # JSON configs
            '*.ini',    # INI configs
            '*.yaml',   # YAML configs
            '*.yml',    # YAML configs (alternate extension)
            '*.toml',   # TOML configs
            '*.cfg',    # Config files
            '*.conf',   # Config files
            '*.bat',    # Batch scripts
            '*.sh',     # Shell scripts
            '*.ps1',    # PowerShell scripts
            'LICENSE',  # License file
            '.gitignore',  # Git ignore file
            '.pylintrc',  # Pylint configuration
            '.pre-commit-config.yaml',  # Pre-commit hooks
            '.editorconfig',  # Editor configuration
            'MANIFEST.in',  # Package manifest
            'setup.py',  # Setup script
            'setup.cfg',  # Setup configuration
            'pyproject.toml',  # Modern Python project config
            'pytest.ini',  # Pytest configuration
            '.env.example',  # Environment template
            'requirements*.txt',  # All requirements files
            'package.json',  # Node package file
            'package-lock.json',  # Node lock file
            '*.spec',  # PyInstaller specifications
            'Dockerfile',  # Docker configurations
            'docker-compose.yml',
            '.dockerignore',
            'Makefile',  # Make configurations
            'CLAUDE.md',  # Claude project instructions
            'MODULE_USAGE_GUIDE.md',  # Module usage documentation
            'DEVELOPMENT_FILES.md',  # Development files documentation
            '*.html',  # HTML templates and reports
            '*.css',   # Stylesheets
            '*.js',    # JavaScript files
        ]
        
        # Define exclusion patterns
        exclude_dirs = [
            '__pycache__',
            '.git',
            '.vscode',
            '.idea',
            'node_modules',
            'outlook_venv',
            'outlook_venv_*',  # Any venv variant
            'venv',
            'venv_*',
            'env',
            'build',
            'dist',
            'build_env_*',
            'backups',
            'archive',
            'archived',
            'output',
            'reports/ultimate_suite_*',  # Exclude large generated report suites
            'exported_emails',
            'extracted_emails',
            'exports',
            'test_output',
            '.pytest_cache',
            '*.egg-info',
            'htmlcov',  # Coverage reports
            '.coverage',
            '.tox',
            '.mypy_cache',
            '.ruff_cache',
            'traces',  # Debug traces
            'outlook-extractor-main-essential-*',  # Exclude legacy archived folders
        ]
        
        if exclude_tests:
            exclude_dirs.extend(['tests', 'test_*', 'benchmarks'])
        
        exclude_files = [
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '*.so',
            '*.dll',
            '*.dylib',
            '*.sqlite',
            '*.sqlite-*',
            '*.db',
            '*.log',
            '*.csv',
            '*.xlsx',
            '*.xls',
            '*.html',
            '*.zip',
            '*.7z',
            '*.tar',
            '*.gz',
            '*.bz2',
            '*.rar',
            '.DS_Store',
            'Thumbs.db',
            '*.swp',
            '*.swo',
            '*~',
            '*.bak',
            '*.tmp',
            '*.temp',
        ]
        
        # Use Python's zipfile module for cross-platform compatibility
        if not quiet:
            print("   Creating development zip archive...")
            print("   Including: Build system, agents, CI/CD, tests, benchmarks...")
        
        # Import for pattern matching
        import fnmatch
        
        # Important directories to specifically include
        important_dirs = [
            'scripts/build',  # Build system
            '.claude/agents',  # Agent specifications
            'agents',  # Agent orchestration
            'launcher',  # Launcher infrastructure
            'benchmarks',  # Performance benchmarks
            'docs',  # Documentation
            'admin_report_generator',  # Admin report generator system
            'report_scripts',  # Enhanced reporting components
            'core',  # Core modules including WPM, productivity, threading
            'gui',  # GUI components and modular structure
            'exporters',  # Export functionality
            'outlook_extractor',  # Outlook extractor modules
            'secure_database',  # Secure database operations
            'reports',  # Generated reports (for reference/templates)
            'migrations',  # Database migrations
            'config',  # Configuration files
        ]
        
        if not exclude_tests:
            important_dirs.extend(['tests', 'test_*'])
        
        # Function to check if path should be excluded
        def should_exclude(path_str):
            # Normalize path for comparison
            norm_path = path_str.replace('\\', '/')
            
            # Check directory exclusions
            for pattern in exclude_dirs:
                # Handle wildcard patterns
                if '*' in pattern:
                    # Check each part of the path
                    for path_part in norm_path.split('/'):
                        if fnmatch.fnmatch(path_part, pattern):
                            return True
                else:
                    # Check if path starts with or contains the excluded dir
                    if norm_path == pattern or norm_path.startswith(f'{pattern}/') or f'/{pattern}/' in norm_path:
                        return True
            
            # Check file exclusions
            for pattern in exclude_files:
                if fnmatch.fnmatch(os.path.basename(path_str), pattern):
                    return True
            
            return False
        
        # Function to check if path should be included
        def should_include(path_str):
            # Normalize path separators for comparison
            normalized_path = path_str.replace('\\', '/')
            
            # First check if in important directories - if yes, include ALL files
            for imp_dir in important_dirs:
                normalized_dir = imp_dir.replace('\\', '/')
                if normalized_path.startswith(normalized_dir + '/') or normalized_path == normalized_dir:
                    return True
            
            # Check file patterns for files not in important directories
            basename = os.path.basename(path_str)
            for pattern in include_patterns:
                # Match against basename for file patterns
                if fnmatch.fnmatch(basename, pattern):
                    return True
                # Also check full path for patterns with wildcards
                if '*' in pattern and fnmatch.fnmatch(path_str, pattern):
                    return True
            
            return False
        
        # Create zip file
        file_count = 0
        dev_file_count = 0
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Walk through project directory
                for root, dirs, files in os.walk(project_root):
                    # Get relative path
                    rel_root = os.path.relpath(root, project_root)
                    
                    # Skip if this directory should be excluded
                    if rel_root != '.' and should_exclude(rel_root.replace('\\', '/')):
                        dirs.clear()  # Don't walk subdirectories
                        continue
                    
                    # Filter directories to walk
                    dirs[:] = [d for d in dirs if not should_exclude(f'{rel_root}/{d}'.replace('\\', '/'))]
                    
                    # Add files
                    for file in files:
                        # Skip Windows reserved names at file level
                        file_lower = file.lower()
                        if file_lower in ['nul', 'con', 'prn', 'aux', 'com1', 'com2', 'com3', 'com4',
                                        'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9',
                                        '_nul', '_con', '_prn', '_aux']:
                            if not quiet:
                                print(f"   Skipping Windows reserved name: {file}")
                            continue
                        
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, project_root).replace('\\', '/')
                        
                        # Check if file should be included
                        if should_exclude(rel_path):
                            continue
                        
                        if not should_include(rel_path):
                            continue
                        
                        # Add file to zip
                        try:
                            # Use os.path.abspath instead of Path.resolve() to avoid mount issues
                            abs_file_path = os.path.abspath(file_path)
                            # Skip Windows reserved names
                            basename = os.path.basename(rel_path).lower()
                            if basename in ['nul', 'con', 'prn', 'aux', 'com1', 'com2', 'com3', 'com4', 
                                          'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9']:
                                if not quiet:
                                    print(f"   Skipping Windows reserved name: {rel_path}")
                                continue
                            zf.write(abs_file_path, rel_path)
                            file_count += 1
                        except Exception as write_err:
                            if not quiet:
                                print(f"   Warning: Could not add {rel_path}: {write_err}")
                            continue
                        
                        # Count development files
                        if any(keyword in rel_path for keyword in [
                            'scripts/build', '.claude/agents', '.pylintrc',
                            '.pre-commit', '.spec', 'pytest.ini', 'benchmarks'
                        ]):
                            dev_file_count += 1
                        
                        # Show progress for large archives
                        if not quiet and file_count % 100 == 0:
                            print(f"   Added {file_count} files...")
            
            # Get file size
            size_mb = zip_path.stat().st_size / (1024 * 1024)
            
            if not quiet:
                print(f"   Size: {size_mb:.1f}MB")
                print(f"   Files: {file_count}")
                if dev_file_count > 0:
                    print(f"   Development files included: {dev_file_count} infrastructure files")
            
            return str(zip_path)
            
        except Exception as e:
            print(f"[ERROR] Failed to create development zip: {e}")
            if zip_path.exists():
                zip_path.unlink()
            return None
            
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_full_backup(
    output_dir: str = '.',
    custom_name: Optional[str] = None,
    quiet: bool = False
) -> Optional[str]:
    """
    Create a comprehensive full backup of the project including all code, tests, 
    databases, documentation, and configuration files.
    
    This backup includes EVERYTHING except:
    - Virtual environments (venv, outlook_venv, etc.)
    - Build artifacts (dist/, build/)
    - Node modules
    - Python cache files
    - Git repository data
    - Windows reserved names (nul, con, etc.)
    
    Perfect for:
    - Complete project archival
    - Transferring entire project state
    - Disaster recovery scenarios
    - Creating project snapshots before major changes
    
    Args:
        output_dir: Directory to save the backup zip file
        custom_name: Custom name for the zip file (without extension)
        quiet: Suppress progress output
        
    Returns:
        Path to created zip file or None if failed
    """
    try:
        # Get project root (parent of launcher directory)
        project_root = Path(__file__).parent.parent.parent
        project_name = project_root.name
        
        # Ensure output directory exists
        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if custom_name:
            zip_filename = f"{custom_name}.zip"
        else:
            zip_filename = f"{project_name}-full-{timestamp}.zip"
        
        zip_path = output_path / zip_filename
        
        if not quiet:
            print(f"[ZIP] Creating FULL backup of {project_name}...")
            print(f"   Project: {project_root}")
            print(f"   Output: {zip_path}")
            print(f"   Type: Full (includes code, tests, databases, docs, configs)")
        
        # Define exclusion patterns - minimal exclusions for full backup
        exclude_dirs = [
            '__pycache__',
            '.git',
            'node_modules',
            'outlook_venv',
            'outlook_venv_*',  # Any venv variant
            'venv',
            'venv_*',
            'env',
            'build',
            'dist',
            'build_env_*',
            '.pytest_cache',
            '*.egg-info',
            '.tox',
            '.mypy_cache',
            '.ruff_cache',
            'htmlcov',  # Coverage HTML reports
            '.coverage',
        ]
        
        # Much more limited file exclusions for full backup
        exclude_files = [
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '*.zip',    # Exclude zip files to prevent recursive backups
            '*.7z',     # Exclude other archives
            '*.tar',
            '*.gz',
            '*.bz2',
            '*.rar',
            '.DS_Store',
            'Thumbs.db',
            '*.swp',
            '*.swo',
            '*~',
            # Windows reserved names
            'nul', 'NUL', '_nul',
            'con', 'CON', '_con',
            'prn', 'PRN', '_prn',
            'aux', 'AUX', '_aux',
            'com1', 'com2', 'com3', 'com4',
            'COM1', 'COM2', 'COM3', 'COM4',
            'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9',
        ]
        
        if not quiet:
            print("   Creating comprehensive zip archive...")
            print("   Including: Source code, tests, databases, exports, reports, docs...")
        
        # Import for pattern matching
        import fnmatch
        
        # Function to check if path should be excluded
        def should_exclude(path_str):
            # Normalize path for comparison
            norm_path = path_str.replace('\\', '/')
            
            # Check directory exclusions
            for pattern in exclude_dirs:
                # Handle wildcard patterns
                if '*' in pattern:
                    # Check each part of the path
                    for path_part in norm_path.split('/'):
                        if fnmatch.fnmatch(path_part, pattern):
                            return True
                else:
                    # Check if path starts with or contains the excluded dir
                    if norm_path == pattern or norm_path.startswith(f'{pattern}/') or f'/{pattern}/' in norm_path:
                        return True
            
            # Check file exclusions
            basename = os.path.basename(path_str)
            for pattern in exclude_files:
                if fnmatch.fnmatch(basename, pattern) or basename == pattern:
                    return True
            
            return False
        
        # Track statistics
        file_count = 0
        db_count = 0
        test_count = 0
        doc_count = 0
        total_size = 0
        
        try:
            with zipfile.ZipFile(str(zip_path), 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
                # Walk through project directory
                for root, dirs, files in os.walk(project_root):
                    # Get relative path - handle Windows special files
                    try:
                        rel_root = os.path.relpath(root, project_root)
                    except ValueError as e:
                        # Skip paths that can't be made relative (e.g., Windows special files)
                        if not quiet:
                            print(f"   Warning: Skipping problematic path {root}: {e}")
                        continue
                    
                    # Skip if this directory should be excluded
                    if rel_root != '.' and should_exclude(rel_root.replace('\\', '/')):
                        dirs.clear()  # Don't walk subdirectories
                        continue
                    
                    # Filter directories to walk
                    dirs[:] = [d for d in dirs if not should_exclude(f'{rel_root}/{d}'.replace('\\', '/'))]
                    
                    # Add files
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            rel_path = os.path.relpath(file_path, project_root).replace('\\', '/')
                        except ValueError as e:
                            # Skip files with problematic paths (e.g., Windows reserved names)
                            if not quiet:
                                print(f"   Warning: Skipping file {file}: {e}")
                            continue
                        
                        # Check if file should be excluded
                        if should_exclude(rel_path):
                            if not quiet:
                                # Only report skipping of Windows reserved names
                                file_lower = file.lower()
                                if file_lower in ['nul', 'con', 'prn', 'aux', '_nul', '_con', '_prn', '_aux'] or \
                                   file_lower.startswith(('com', 'lpt')):
                                    print(f"   Skipping Windows reserved name: {file}")
                            continue
                        
                        # Add file to zip
                        try:
                            abs_file_path = os.path.abspath(file_path)
                            
                            # Get file size for statistics
                            file_size = os.path.getsize(abs_file_path)
                            total_size += file_size
                            
                            # Add to zip
                            zf.write(abs_file_path, rel_path)
                            file_count += 1
                            
                            # Track file types for statistics
                            ext = os.path.splitext(file)[1].lower()
                            if ext in ['.sqlite', '.db']:
                                db_count += 1
                            elif 'test' in rel_path.lower():
                                test_count += 1
                            elif ext in ['.md', '.txt', '.pdf', '.docx', '.doc']:
                                doc_count += 1
                            
                        except Exception as write_err:
                            if not quiet:
                                print(f"   Warning: Could not add {rel_path}: {write_err}")
                            continue
                        
                        # Show progress for large archives
                        if not quiet and file_count % 100 == 0:
                            print(f"   Added {file_count} files...")
            
            # Get final zip size
            zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
            total_size_mb = total_size / (1024 * 1024)
            
            if not quiet:
                print(f"\n[SUCCESS] Full backup created successfully!")
                print(f"   Archive: {zip_path}")
                print(f"   Compressed size: {zip_size_mb:.1f}MB")
                print(f"   Original size: {total_size_mb:.1f}MB")
                print(f"   Compression ratio: {(1 - zip_size_mb/total_size_mb)*100:.1f}%")
                print(f"   Total files: {file_count}")
                if db_count > 0:
                    print(f"   Database files: {db_count}")
                if test_count > 0:
                    print(f"   Test files: {test_count}")
                if doc_count > 0:
                    print(f"   Documentation files: {doc_count}")
            
            return str(zip_path)
            
        except Exception as e:
            print(f"[ERROR] Failed to create full backup zip: {e}")
            if zip_path.exists():
                zip_path.unlink()
            return None
            
    except Exception as e:
        print(f"[ERROR] Unexpected error creating full backup: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Simple test
    import sys
    
    if len(sys.argv) > 1:
        output = sys.argv[1]
    else:
        output = "."
    
    result = create_essential_backup(output_dir=output)
    if result:
        print(f"[SUCCESS] Backup created: {result}")
    else:
        print("[ERROR] Backup failed")