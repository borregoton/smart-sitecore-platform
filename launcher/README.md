# Enterprise Launcher System

The launcher system provides enterprise-grade dependency management and environment isolation for the Outlook Extractor project.

## 🎯 Key Features

### Dependency Separation
- **Application Dependencies**: Only what's needed for runtime
- **Build Dependencies**: Clean environments for PyInstaller
- **Security Dependencies**: Isolated tools for validation
- **Test Dependencies**: Separate test framework installation

### Clean Builds
- Security tools are **NEVER** included in production builds
- Build environments are created fresh for each edition
- Automatic exclusion of development/test/security packages

## 📁 Directory Structure

```
launcher/
├── README.md                   # This file
├── core/                       # Core launcher infrastructure
│   ├── base_launcher.py        # Base class for all launchers
│   └── dependency_manager.py   # Enterprise dependency management
├── gui/                        # GUI launcher
│   └── gui_launcher.py
├── cli/                        # CLI launcher (future)
│   └── cli_launcher.py
├── build/                      # Build launcher
│   └── build_launcher.py
└── test/                       # Test launcher
    └── test_launcher.py
```

## 🚀 Usage

### Universal Launcher
```bash
# GUI application
python3 launcher.py gui

# Build with security validation
python3 launcher.py build lite
python3 launcher.py build standard
python3 launcher.py build pro_mac

# Run tests
python3 launcher.py test all
python3 launcher.py test unit
python3 launcher.py test --coverage

# Security scan only
python3 launcher.py security
```

### Direct Launcher Usage
```bash
# GUI with options
python3 launcher/gui/gui_launcher.py --debug

# Build with options
python3 launcher/build/build_launcher.py standard --skip-validation
python3 launcher/build/build_launcher.py lite --keep-build-env

# Test with options
python3 launcher/test/test_launcher.py -v --coverage
```

## 🔒 Security Features

### Validation Lifecycle
1. **Security Check**: Validates dependencies for vulnerabilities
2. **Clean Build Env**: Creates isolated environment without tools
3. **Build Executable**: Produces clean binary
4. **Cleanup**: Removes temporary build environment

### Excluded from Builds
The following are **NEVER** included in production builds:
- Security tools (safety, bandit, pip-audit)
- Test frameworks (pytest, coverage)
- Development tools (black, flake8, mypy)
- Build tools (pyinstaller, wheel)
- Documentation tools (sphinx, mkdocs)

## 🏗️ Build Process

### Standard Build Flow
```python
# 1. Main venv with security tools
outlook_venv/
  ├── Application dependencies ✓
  ├── Security tools ✓ (for validation)
  └── Test tools ✓ (if needed)

# 2. Security validation runs
python3 scripts/build/build_security_validator.py

# 3. Clean build environment created
build_env_standard/
  ├── Application dependencies ✓
  ├── Security tools ✗ (excluded)
  └── Test tools ✗ (excluded)

# 4. PyInstaller builds from clean env
→ OutlookExtractor.exe (clean, no dev tools)
```

## 📦 Dependency Sets

### Core Dependencies (Always Included)
- FreeSimpleGUI
- pandas
- openpyxl
- matplotlib
- numpy
- requests

### AI Dependencies (Edition-Based)
- **Lite**: None
- **Standard**: transformers, nltk, scikit-learn
- **Pro Mac**: torch (MPS), accelerate
- **Pro CUDA**: torch (CUDA), accelerate, spacy

### Security Dependencies (Build/Test Only)
- safety
- bandit
- pip-audit

### Test Dependencies (Test Only)
- pytest
- pytest-cov
- pytest-timeout

## 🔧 Configuration

### Environment Variables
```bash
# Force recreation of venv
LAUNCHER_FORCE_RECREATE=1 python3 launcher.py gui

# Skip validation (not recommended)
LAUNCHER_SKIP_VALIDATION=1 python3 launcher.py build lite

# Keep build environment for debugging
LAUNCHER_KEEP_BUILD_ENV=1 python3 launcher.py build standard
```

### Validation Periods
Different launchers have different validation cache periods:
- **GUI/CLI**: 7 days
- **Build**: 1 day (daily validation)
- **Test**: 3 days
- **Security**: 1 day

## 🐛 Troubleshooting

### Issue: Security tools in production build
```bash
# Solution: Use launcher system
python3 launcher/build/build_launcher.py lite

# NOT: python3 scripts/build/secure_build.py lite
```

### Issue: Missing dependencies during build
```bash
# Solution: Force recreate environment
python3 launcher/build/build_launcher.py standard --force-recreate
```

### Issue: Tests fail with import errors
```bash
# Solution: Use test launcher
python3 launcher/test/test_launcher.py

# NOT: pytest tests/
```

## 🎭 Launcher Types

### GUI Launcher
- Installs core + AI dependencies
- No security/test tools
- Validates every 7 days

### Build Launcher
- Uses main venv for security validation
- Creates clean build env for each edition
- Excludes all dev/test/security tools from build

### Test Launcher
- Installs pytest and coverage tools
- Validates every 3 days
- Isolated from build dependencies

### Security Launcher
- Installs security scanning tools
- Daily validation
- Never contaminates build environments

## 📊 Benefits

1. **Clean Builds**: No dev tool contamination
2. **Smaller Executables**: No unnecessary dependencies
3. **Security**: Validated but not bundled
4. **Maintainability**: Consistent patterns
5. **Enterprise Ready**: Proper separation of concerns

## 🔗 Integration

### With CI/CD
```yaml
# GitHub Actions example
- name: Build with security validation
  run: python3 launcher.py build standard

- name: Run tests
  run: python3 launcher.py test --coverage

- name: Security scan
  run: python3 launcher.py security
```

### With existing scripts
The launcher system is compatible with existing scripts:
- `launch_outlook_extractor.py` → `launcher/gui/gui_launcher.py`
- `secure_build.py` → `launcher/build/build_launcher.py`
- Direct pytest → `launcher/test/test_launcher.py`

## 🚨 Important Notes

1. **Always use launchers** for consistency
2. **Never install security tools** in build environments
3. **Validate before production** builds
4. **Clean environments** = smaller, safer executables
5. **Separate concerns** = maintainable codebase