# Smart Sitecore Analysis Platform v2.0 - Development Guide

## 🔧 Technical Architecture

### System Overview
The platform consists of three main components:
1. **Python Extraction Engine** - Extracts data from Sitecore GraphQL APIs
2. **PostgreSQL Database** - Stores extracted data with v2.0 multi-site schema
3. **Next.js Web Platform** - Interactive dashboard for data visualization

### Data Flow
```
Sitecore API (configured via config.json)
    ↓ GraphQL Introspection + Content Queries
EnhancedPhase1Extractor
    ↓ JSON Results (schema + sites discovered)
PostgreSQL Database (configured via config.json)
    ↓ v2.0 Tables: scans_v2, analysis_results
Next.js Web Platform (configurable host:port)
    ↓ REST APIs + React Components
Interactive Dashboard
```

## 🗄️ Database Configuration

### Configuration Management
Database settings are managed through the centralized `config.json` file:

```bash
# Configure database connection
python launch.py --config-help  # See all database options
python launch.py diagnose_database \
  --db-host "your-database.com" \
  --db-user "your-username" \
  --db-password "your-password" \
  --db-name "your-database"
```

### Schema Structure
- **v2.0 Tables**: `scans_v2`, `analysis_results`, `scan_modules`
- **v1.0 Compatibility**: `sites`, `scans`, existing tables
- **Key Columns**: `confidence_score` (not `average_confidence`)

### Configuration File Structure
File: `config.json` (database section)
```json
{
  "database": {
    "host": "your-database-host",
    "pg_port": 5432,
    "api_port": 8000,
    "credentials": {
      "postgres": {
        "user": "your-username",
        "password": "your-password",
        "database": "your-database"
      }
    }
  }
}
```

### Web Platform Configuration
The web platform automatically reads database settings from config.json through environment variables set by the launch script.

## 🐍 Python Extraction Engine

### Core Files
- **`enhanced_phase1_extractor.py`**: Main extraction logic
- **`supabase_client_v2.py`**: Database connection handling
- **`grab_sitecore_data.py`**: Direct extraction script
- **`launch.py`**: Command launcher with new web-dev command

### Key Dependencies
```python
# Verified working versions
requests>=2.31.0
psycopg2-binary>=2.9.0
click>=8.1.0
```

### Extraction Process
1. **GraphQL Introspection**: Extracts full schema (1.1MB+ data)
2. **Content Discovery**: Finds sites using `/sitecore/content` path
3. **Site Analysis**: Gets templates, child counts, field samples
4. **Database Storage**: Saves to `scans_v2` and `analysis_results` tables

## 🌐 Web Platform Architecture

### Technology Stack
- **Framework**: Next.js 14 with TypeScript
- **Database**: PostgreSQL via `pg` library (direct connection)
- **UI**: React components with Tailwind CSS
- **State**: Custom hooks with `useState` and `useEffect`

### Key Files Created
```
web-platform/src/
├── app/api/sitecore/
│   ├── extracted-sites/route.ts      # GET API for site data
│   └── trigger-extraction/route.ts   # POST API for triggering extraction
├── components/sitecore/
│   └── sitecore-dashboard.tsx        # Main dashboard component
├── hooks/
│   └── use-sitecore-data.ts          # Data fetching hooks
├── lib/services/
│   └── sitecore-data-service.ts      # PostgreSQL service layer
└── components/ui/
    └── tabs.tsx                      # Tab navigation component
```

### Database Service Layer
File: `src/lib/services/sitecore-data-service.ts`

**Key Methods:**
- `getRecentScans()`: Fetches scan history from `scans_v2`
- `getExtractedSiteData()`: Parses JSON results for site information
- `getScanStatistics()`: Aggregates scan metrics
- `triggerExtraction()`: Executes Python extraction script

**Connection Pattern:**
```typescript
// Environment variables automatically set from config.json by launch.py
const pool = new Pool({
  host: process.env.POSTGRES_HOST,        // From config.json database.host
  port: parseInt(process.env.POSTGRES_PORT || '5432'),  // From config.json database.pg_port
  database: process.env.POSTGRES_DATABASE, // From config.json database.credentials.postgres.database
  user: process.env.POSTGRES_USER,         // From config.json database.credentials.postgres.user
  password: process.env.POSTGRES_PASSWORD, // From config.json database.credentials.postgres.password
  ssl: false
})
```

### API Endpoints

#### GET `/api/sitecore/extracted-sites`
Returns extracted Sitecore site data and statistics.

**Response Format:**
```json
{
  "sites": [
    {
      "siteName": "nextjs-app-21",
      "sitePath": "/sitecore/content/nextjs-app-21",
      "templateName": "App",
      "childCount": 4,
      "hasChildren": true,
      "fieldSamples": {}
    }
  ],
  "statistics": {
    "totalScans": 9,
    "successfulScans": 2,
    "averageConfidence": 0.9,
    "totalSitesDiscovered": 4,
    "lastScanDate": "2025-09-22T21:54:46.832Z"
  },
  "connected": true
}
```

#### POST `/api/sitecore/trigger-extraction`
Triggers Python extraction script via `exec()`.

**Implementation:**
```typescript
// Uses existing config.json for all parameters
const pythonCommand = `cd "${projectPath}" && python launch.py GrabSiteCoreData`
const { stdout, stderr } = await execPromise(pythonCommand, {
  timeout: 60000,
  cwd: projectPath
})
```

### React Components

#### Main Dashboard (`SitecoreDashboard`)
- **Real-time data fetching** using `useSitecoreData` hook
- **Statistics overview** with database connection status
- **Site grid display** showing templates and content details
- **Extraction triggers** via web interface

#### Tab Navigation
- **"Extracted Sitecore Data"** tab: Shows real extracted data
- **"Customer Portfolio"** tab: Existing customer management interface

## 🔄 Enhanced launch.py Commands

### New Commands Added
```python
# Web platform management
@cli.command()
def web_dev():
    """Start web development server"""
    # Starts Next.js dev server in web-platform directory

# Database diagnostics
@cli.command()
def diagnose_database():
    """Test database connectivity"""
    # Tests PostgreSQL connection with working credentials

@cli.command()
def inspect_schema():
    """View database schema"""
    # Lists all tables and their column structures

@cli.command()
def database_report():
    """Generate comprehensive HTML report"""
    # Creates detailed extraction report with site breakdown
```

### Command Implementation Pattern
```python
def execute_command(command_parts, description=""):
    """Execute shell command with error handling"""
    try:
        result = subprocess.run(command_parts,
                              capture_output=True,
                              text=True,
                              check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return None
```

## 🐛 Common Development Issues

### Configuration Issues
**Problem**: Missing config.json file
**Solution**: Run any command with configuration parameters to create automatically:
```bash
python launch.py web-dev --sitecore-url "https://your-site.com" --db-host "your-db.com"
```

**Problem**: Invalid configuration parameters
**Solution**: Use configuration help to see all available options:
```bash
python launch.py --config-help
```

### Database Connection Issues
**Problem**: `column "average_confidence" does not exist`
**Solution**: Use `confidence_score` column name in queries

**Problem**: Authentication failed
**Solution**: Verify database credentials in config.json and test with:
```bash
python launch.py diagnose_database
```

### Next.js Build Issues
**Problem**: ChunkLoadError or module resolution errors
**Solution**: Clear build cache and restart:
```bash
rm -rf .next
npm run dev
```

**Problem**: Port 3000 already in use
**Solution**: Next.js automatically uses 3001, or manually kill port:
```bash
npx kill-port 3000
```

### Python Extraction Issues
**Problem**: No sites discovered
**Solution**: Verify Sitecore configuration in config.json:
```bash
python launch.py --config-help  # See Sitecore options
```

**Problem**: API authentication failures
**Solution**: Check Sitecore credentials and test with a simple command:
```bash
python launch.py inspect_schema --sitecore-url "your-url" --sitecore-api-key "your-key"
```

**Problem**: Unicode errors on Windows
**Solution**: All emojis removed from output for Windows compatibility

## 🧪 Testing and Validation

### Database Connection Test
```bash
python launch.py diagnose_database
# Expected: Connection successful, shows table count
```

### API Endpoint Test
```bash
curl -s http://localhost:3000/api/sitecore/extracted-sites
# Expected: JSON response with 4 sites
```

### Web Platform Test
1. Navigate to http://localhost:3000
2. Click "Extracted Sitecore Data" tab
3. Verify 4 sites displayed with correct details
4. Check database connection indicator (green)

## 📈 Performance Metrics

### Extraction Performance
- **Schema Extraction**: ~800ms
- **Content Extraction**: ~60ms
- **Total Extraction**: ~1.3 seconds
- **Data Volume**: 1.1MB+ GraphQL schema

### Database Performance
- **Connection Time**: <100ms
- **Query Response**: <250ms for site data
- **Write Operations**: 2-4 inserts per extraction

### Web Platform Performance
- **Page Load**: <2 seconds (initial build)
- **API Response**: <300ms for extracted sites
- **Component Render**: React.memo optimization for re-renders

## 🔐 Security Considerations

### Database Security
- **Direct PostgreSQL connection** (not REST API)
- **Credentials in environment variables** only
- **Connection pooling** with timeout limits

### API Security
- **No authentication currently** (local development)
- **Input validation** on extraction triggers
- **Error message sanitization** to prevent information leakage

## 🚀 Deployment Considerations

### Environment Requirements
- **Python 3.8+** with PostgreSQL drivers
- **Node.js 18+** with npm
- **PostgreSQL 12+** database access
- **Network access** to Sitecore GraphQL endpoint

### Production Readiness Checklist
- [ ] Add authentication to API endpoints
- [ ] Implement rate limiting for extraction triggers
- [ ] Add comprehensive error logging
- [ ] Set up automated extraction scheduling
- [ ] Add database connection retry logic
- [ ] Implement proper secret management

## 📝 Code Quality Standards

### TypeScript Configuration
- **Strict mode enabled** for type safety
- **No implicit any** types allowed
- **Proper error interfaces** with Result pattern

### React Best Practices
- **Functional components** with hooks
- **React.memo** for performance optimization
- **Custom hooks** for data management
- **Proper error boundaries** for graceful failures

### Database Best Practices
- **Connection pooling** for performance
- **Prepared statements** for security
- **Proper error handling** with connection cleanup
- **Transaction management** for data consistency

This technical guide provides everything needed for a developer to understand, modify, and extend the Smart Sitecore Analysis Platform v2.0.