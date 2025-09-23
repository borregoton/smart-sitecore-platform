# 📁 Smart Sitecore Analysis Platform - Project Structure

## 🏗️ Repository Overview

**Smart Sitecore Analysis Platform** is a comprehensive toolkit for analyzing and extracting data from Sitecore instances, providing both command-line tools and a modern web dashboard interface.

## 📂 Directory Structure

```
Project20/
│
├── 📊 cli/                              # Python Analysis & Extraction Engine
│   ├── smart_sitecore/                  # Core extraction modules
│   │   ├── analyzers/                   # Analysis modules
│   │   │   ├── architecture.py          # Architecture analysis
│   │   │   ├── data_architecture.py     # Data architecture analysis
│   │   │   └── security.py              # Security analysis
│   │   ├── enhanced_modules/            # Enhanced extraction modules
│   │   ├── enhanced_phase1_extractor.py # Main Sitecore extractor
│   │   ├── supabase_client_v2.py        # Database client v2
│   │   └── __init__.py                  # Module initialization
│   └── smart_sitecore_cli.egg-info/     # Package information
│
├── 🌐 web-platform/                     # Next.js Web Dashboard
│   ├── src/                             # Source code
│   │   ├── app/                         # Next.js 14 App Router
│   │   │   ├── api/sitecore/            # REST API endpoints
│   │   │   └── sitecore/                # Dashboard pages
│   │   ├── components/                  # React components
│   │   │   └── sitecore/                # Sitecore-specific components
│   │   ├── hooks/                       # Custom React hooks
│   │   ├── lib/                         # Utilities & services
│   │   │   ├── services/                # Database & API services
│   │   │   └── utils/                   # Helper utilities
│   │   └── types/                       # TypeScript definitions
│   ├── prisma/                          # Database ORM
│   │   └── schema.prisma                # Database schema
│   ├── docker/                          # Docker configurations
│   ├── scripts/                         # Build & deployment scripts
│   ├── package.json                     # Node dependencies
│   ├── next.config.js                   # Next.js configuration
│   └── tailwind.config.js              # Tailwind CSS configuration
│
├── 🗄️ database/                         # Database Management
│   ├── complete_v2_schema.sql           # Full v2.0 schema
│   ├── add_v1_compatibility_tables.sql  # v1.0 compatibility layer
│   ├── add_phase1_tracking.sql          # Phase 1 tracking tables
│   └── add_v2_enhancements.sql          # v2.0 enhancements
│
├── 🚀 launcher/                         # GUI Launcher (Experimental)
│   ├── core/                            # Core launcher modules
│   ├── gui/                             # GUI components
│   ├── test/                            # Test suites
│   └── build/                           # Build artifacts
│
├── 📊 backend/                          # Backend Services
│   └── src/                             # Source code
│
├── 📐 docs/                             # Documentation & Architecture
│   └── architecture/                    # Architecture diagrams
│       ├── images/                      # Generated PNG diagrams
│       │   ├── Smart Sitecore Analysis - C4 Context Diagram.png
│       │   ├── Smart Sitecore Analysis - C4 Container Diagram.png
│       │   └── [Additional architecture diagrams...]
│       ├── *.puml                       # PlantUML source files
│       └── C4*.puml                     # C4 model library files
│
├── 🔧 Scripts & Tools                  # Standalone Python Scripts
│   ├── launch.py                        # 🎯 Main unified launcher
│   ├── grab_sitecore_data.py            # Direct Sitecore extraction
│   ├── generate_extraction_report.py    # Report generation
│   ├── diagnose_database_connection.py  # Database diagnostics
│   ├── inspect_database_schema.py       # Schema inspection
│   ├── fix_v2_schema.py                # Schema migration tools
│   ├── create_enhanced_tables.py        # Table creation scripts
│   ├── audit_phase1_data.py            # Data auditing tools
│   └── web_api.py                      # Web API server
│
├── 📋 Configuration                    # Configuration Files
│   ├── config.json                     # Main configuration file
│   ├── requirements.txt                # Python dependencies
│   ├── Dockerfile.web-api              # Web API Docker configuration
│   └── nul                             # Null file (can be removed)
│
├── 📖 Documentation                     # Project Documentation
│   ├── README.md                       # Main project documentation
│   ├── QUICKSTART.md                   # Quick start guide
│   ├── DEVELOPMENT.md                  # Development guide
│   ├── PROJECT_STRUCTURE.md           # This file
│   ├── HANDOFF-NOTES.md               # Project handoff notes
│   ├── STATUS.md                      # Current project status
│   ├── DATABASE_CONNECTION_STATUS.md  # Database connection guide
│   ├── LAUNCHER.md                    # Launcher documentation
│   ├── LAUNCHER_README.md             # Launcher readme
│   └── supabase_kit.md                # Supabase integration guide
│
├── 🗂️ Data Storage                     # Local Data Storage
│   ├── local_database/                 # Local database files
│   ├── out/                           # Output files and reports
│   └── sitecore_venv/                 # Python virtual environment
│
└── 📦 Dependencies & Build             # Build Artifacts
    └── shared/                         # Shared resources
        └── config/                     # Shared configuration

```

## 🔧 Key Files

### Core Entry Points
- **`launch.py`** - Main unified launcher for all platform features
- **`grab_sitecore_data.py`** - Direct Sitecore data extraction
- **`web_api.py`** - RESTful API server

### Configuration
- **`config.json`** - Central configuration for all components
- **`requirements.txt`** - Python package dependencies
- **`web-platform/package.json`** - Node.js dependencies

### Database Schema
- **`database/complete_v2_schema.sql`** - Full v2.0 PostgreSQL schema
- **`web-platform/prisma/schema.prisma`** - Prisma ORM schema

## 🚀 Component Overview

### 1. **Python Extraction Engine** (`cli/`)
- GraphQL-based Sitecore data extraction
- Multi-site support with customer scoping
- Enhanced analysis modules for architecture, security, and performance

### 2. **Web Dashboard** (`web-platform/`)
- Next.js 14 with TypeScript
- Real-time data visualization
- RESTful API endpoints
- PostgreSQL integration via Prisma

### 3. **Database Layer** (`database/`)
- PostgreSQL with v2.0 multi-site schema
- Backward compatibility with v1.0
- Customer and site scoping

### 4. **Documentation** (`docs/`)
- PlantUML architecture diagrams
- C4 model diagrams
- Comprehensive system documentation

## 📊 Data Flow

```
1. Sitecore Instance (GraphQL API)
         ↓
2. Python Extraction Engine (cli/)
         ↓
3. PostgreSQL Database (Supabase/Local)
         ↓
4. Web Dashboard (web-platform/)
         ↓
5. User Interface (http://localhost:3000)
```

## 🔌 Integration Points

### Database Connection
- **Configuration**: `config.json`
- **Connection String**: PostgreSQL via `DATABASE_URL`
- **ORM**: Prisma for web platform, psycopg2 for Python

### API Endpoints
- **Base URL**: `http://localhost:3000/api/sitecore`
- **Extraction**: `/api/sitecore/extract`
- **Sites**: `/api/sitecore/sites`
- **Analysis**: `/api/sitecore/analysis`

### Authentication
- **Sitecore**: API Key authentication
- **Database**: Username/password or connection string
- **Web Platform**: Session-based (development)

## 🎯 Development Workflow

### Local Development
```bash
# Python extraction
python launch.py GrabSiteCoreData

# Web dashboard
cd web-platform && npm run dev

# Both together
python launch.py web-dev
```

### Docker Deployment
```bash
docker build -f Dockerfile.web-api -t sitecore-platform .
docker run -p 3000:3000 sitecore-platform
```

## 📦 Required Dependencies

### Python (3.8+)
- `psycopg2-binary` - PostgreSQL adapter
- `requests` - HTTP client
- `python-dotenv` - Environment management
- `flask` - Web API framework
- See `requirements.txt` for complete list

### Node.js (18+)
- `next` - React framework
- `react` - UI library
- `prisma` - Database ORM
- `tailwindcss` - CSS framework
- See `web-platform/package.json` for complete list

## 🔒 Security Considerations

- API keys stored in `config.json` (gitignored)
- Database credentials in environment variables
- Row-level security for multi-customer support
- HTTPS recommended for production deployment

## 📈 Monitoring & Logging

- Python extraction logs to console
- Web platform logs to `.next/` directory
- Database queries logged when verbose mode enabled
- Performance metrics tracked in database

---

**Last Updated**: January 2025
**Version**: 2.0
**Maintained By**: DelusionalSecurity Development Team