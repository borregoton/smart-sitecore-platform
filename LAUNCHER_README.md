# Smart Sitecore Analysis Platform - Project20 Launcher

## Overview
The Project20 launcher provides a clean, isolated environment for running Sitecore analysis tasks without affecting your primary Python environment. It automatically manages virtual environments and dependencies.

## Quick Start

### First-Time Setup
```bash
python launch.py --setup-only
```
This will:
- Create a virtual environment (`sitecore_venv/`)
- Install all required dependencies
- Verify Python 3.8+ compatibility

### Generate Analysis Report
```bash
python launch.py html_report
```
This runs a complete Phase 1 Sitecore analysis and generates an HTML report.

## Available Commands

| Command | Description |
|---------|-------------|
| `--setup-only` | Create virtual environment and install dependencies only |
| `html_report` | Run Phase 1 analysis and generate HTML report |
| `test_phase1` | Run Phase 1 verification test |
| `test_db` | Test database connectivity |
| `test_enhanced` | Run enhanced content analysis test |
| `--help` | Show all available commands |

## What Gets Analyzed

### Phase 1 Extraction includes:
1. **GraphQL Schema Extraction** - Sitecore GraphQL API structure
2. **Content Tree Extraction** - Site structure and content hierarchy
3. **Template Extraction** - Content templates and usage patterns
4. **Data Persistence** - Results saved to local JSON database

### Sample Output
```
PHASE 1: SITECORE DATA EXTRACTION
============================================================

[1/4] GraphQL Schema Extraction
------------------------------
   [SUCCESS] GraphQL introspection successful
      Types: 15 objects, 8 enums
      Query fields: 12

[2/4] Content Tree Extraction
------------------------------
   [SUCCESS] Content tree extracted successfully
      Sites: 4
      Estimated items: 258

[3/4] Template Extraction
------------------------------
   [SUCCESS] Template extraction completed
      System templates: 0
      Content templates: 7

[4/4] Data Persistence Verification
------------------------------
   [SUCCESS] Data persistence verified
      Modules saved: 3
      Successful: 3
      Average confidence: 0.82

[SUCCESS] Phase 1 extraction completed successfully!
   Total time: 3.03s
   Scan ID: 386a96e8-a387-4a5e-b514-7a6100ad1191
```

## Output Files

### HTML Report
- **File**: `phase1_report.html`
- **Contains**: Complete analysis results with summary and details
- **Format**: Web-ready HTML with styling

### Local Database
- **Location**: `local_database/`
- **Files**:
  - `sites.json` - Site information
  - `scans.json` - Scan history and status
  - `modules.json` - Detailed analysis results

## Target Sitecore Instance

The launcher is pre-configured to analyze:
- **URL**: `https://cm-qa-sc103.kajoo.ca`
- **API Key**: `{34B8FFF8-8F50-4C41-95A8-D2A9304EBD52}`

## Dependencies Managed

The virtual environment includes:
- `aiohttp` - Async HTTP client
- `asyncpg` - PostgreSQL async driver
- `supabase` - Database client
- `requests` - HTTP library
- `pydantic` - Data validation
- `jinja2` - Template engine
- `beautifulsoup4` - HTML parsing
- `rich` - Enhanced CLI output
- Plus testing and utility libraries

## Environment Isolation

### Benefits:
- ✅ Keeps your main Python environment clean
- ✅ Ensures consistent dependency versions
- ✅ Eliminates version conflicts
- ✅ Easy to remove (just delete `sitecore_venv/` folder)

### Virtual Environment Location:
```
Project20/
├── sitecore_venv/          # Isolated Python environment
├── requirements.txt        # Dependency specifications
├── launch.py              # Main launcher script
└── phase1_report.html     # Generated analysis report
```

## Troubleshooting

### Common Issues:

**"Virtual environment not found"**
```bash
python launch.py --setup-only
```

**"Module not found" errors**
```bash
python launch.py --setup-only --force-install
```

**Permission errors on Windows**
- Run Command Prompt as Administrator
- Or use PowerShell with execution policy: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

## Next Steps

After successful Phase 1 analysis:
1. Review the HTML report in your browser
2. Check the local database files for detailed results
3. Use the scan ID to reference specific analysis runs
4. Proceed with Phase 2 analysis modules (when API keys are configured)

## Technical Notes

- **Platform**: Cross-platform (Windows, macOS, Linux)
- **Python**: Requires 3.8 or higher
- **Storage**: Local JSON files (no external database required for Phase 1)
- **Unicode**: Windows-compatible ASCII output (no special characters)
- **Timeout**: 10-minute maximum execution time per command