# Smart Sitecore Analysis Platform v2.0 - Architecture Documentation

This directory contains comprehensive PlantUML diagrams documenting the complete architecture of the Smart Sitecore Analysis Platform v2.0, covering sequence diagrams, flow charts, C4 model diagrams, and deployment views.

## 📋 Documentation Index

### 🔄 Sequence Diagrams
These diagrams show the detailed interactions between components over time:

- **[01-sequence-extraction.puml](01-sequence-extraction.puml)** - Manual extraction process from launch.py through to PostgreSQL storage
- **[02-sequence-web-dashboard.puml](02-sequence-web-dashboard.puml)** - Web dashboard loading sequence and data fetching process
- **[03-sequence-web-extraction.puml](03-sequence-web-extraction.puml)** - Web-triggered extraction via API calls and child processes

### 🌊 Flow Diagrams
These diagrams illustrate data flow and user interaction patterns:

- **[04-flow-data-architecture.puml](04-flow-data-architecture.puml)** - Overall system data flow architecture showing all major components
- **[05-flow-user-interactions.puml](05-flow-user-interactions.puml)** - User interaction flows for both command line and web interface modes

### 🏗️ C4 Model Diagrams
The C4 model provides hierarchical views of the system architecture:

**Online Versions (require internet access):**
- **[06-c4-context.puml](06-c4-context.puml)** - System context showing users, platform, and external systems
- **[07-c4-container.puml](07-c4-container.puml)** - Container view showing major applications and databases
- **[08-c4-component-web.puml](08-c4-component-web.puml)** - Component view of the Next.js web platform
- **[09-c4-component-extraction.puml](09-c4-component-extraction.puml)** - Component view of the Python extraction engine

**Offline Versions (work without internet):**
- **[06-c4-context-offline.puml](06-c4-context-offline.puml)** - System context (offline compatible)
- **[07-c4-container-offline.puml](07-c4-container-offline.puml)** - Container view (offline compatible)
- **[08-c4-component-web-offline.puml](08-c4-component-web-offline.puml)** - Web platform components (offline)
- **[09-c4-component-extraction-offline.puml](09-c4-component-extraction-offline.puml)** - Extraction engine components (offline)

### 🚀 Deployment View
- **[10-deployment-view.puml](10-deployment-view.puml)** - Deployment architecture showing runtime environments and network connections (online)
- **[10-deployment-view-offline.puml](10-deployment-view-offline.puml)** - Deployment architecture (offline compatible)

## 🎯 Architecture Overview

### System Purpose
The Smart Sitecore Analysis Platform v2.0 is a comprehensive solution for:
- **Extracting** Sitecore GraphQL schema and content data
- **Analyzing** multi-site Sitecore implementations
- **Visualizing** data through interactive web dashboards
- **Generating** reports and insights for business users

### Key Components

#### 🖥️ Command Line Interface (Python)
- **Entry Point**: `launch.py` with multiple command options
- **Core Commands**: GrabSiteCoreData, web-dev, database_report, diagnose_database
- **Extraction Engine**: EnhancedPhase1Extractor for GraphQL processing
- **Database Client**: SupabaseClientV2 with PostgreSQL connectivity

#### 🌐 Web Platform (Next.js 14)
- **Frontend**: React 18 with TypeScript and interactive dashboards
- **API Layer**: Next.js API routes for data access and extraction triggers
- **Data Service**: SitecoreDataService with direct PostgreSQL connections
- **Real-time Updates**: Auto-refresh capabilities and status monitoring

#### 🗄️ Data Storage (PostgreSQL)
- **Database**: PostgreSQL 13+ with v2.0 multi-site schema
- **Tables**: 26+ tables including scans_v2, analysis_results, scan_modules
- **Authentication**: Tenant-based system (postgres.zyafowjs5i4ltxxq)
- **Storage**: JSON analysis results with metadata and statistics

#### 🔗 External Integrations
- **Sitecore CMS**: cm-qa-sc103.kajoo.ca GraphQL API endpoint
- **Authentication**: API key-based access (sc_apikey header)
- **Data Volume**: 1.1MB+ GraphQL schema, 216 types, 2968 fields

### Current System Status

#### ✅ Operational Metrics
- **Sites Discovered**: 4 active Sitecore sites
- **Schema Coverage**: 216 GraphQL types, 2968 fields
- **Extraction Performance**: ~1.33 seconds average duration
- **Database Records**: 9 total scans, 2 successful extractions
- **Web Platform**: Running on localhost:3000

#### 📊 Discovered Sites
1. **Home** - Sample Item template, 0 children
2. **nextjs-app-21** - App template, 4 children
3. **react-app-21** - App template, 4 children
4. **TG Architects** - Folder template, 1 child

### Data Flow Architecture

```
Sitecore CMS → Python Extraction → PostgreSQL → Web API → React Dashboard
     ↑              ↓                    ↑          ↓          ↓
GraphQL API    JSON Storage         Direct SQL   REST API   User Interface
```

### User Personas & Access Patterns

#### 👨‍💻 Developer/Admin
- **Access Method**: Command line interface
- **Primary Tasks**: Bulk extractions, database diagnostics, system maintenance
- **Tools**: launch.py commands, database reports, schema inspection

#### 👩‍💼 Business User
- **Access Method**: Web browser interface
- **Primary Tasks**: Data visualization, site exploration, extraction triggers
- **Tools**: Interactive dashboard, statistics cards, site grid

#### 📊 Data Consumer
- **Access Method**: Web dashboard viewing
- **Primary Tasks**: Monitoring metrics, performance analysis, report consumption
- **Tools**: Real-time statistics, historical data, export capabilities

### Security & Authentication

#### 🔐 Sitecore API Access
- **Method**: API key authentication
- **Key**: {34B8FFF8-8F50-4C41-95A8-D2A9304EBD52}
- **Endpoint**: /sitecore/api/graph/edge
- **Protocol**: HTTPS

#### 🗄️ Database Access
- **Method**: Tenant-based PostgreSQL authentication
- **Username**: postgres.zyafowjs5i4ltxxq
- **Host**: 10.0.0.196:5432
- **Connection**: Pool-based with retry logic

### Performance Characteristics

#### ⚡ Extraction Performance
- **GraphQL Schema**: 1.1MB+ response size
- **Processing Time**: 1.33 seconds average
- **Confidence Scoring**: 90%+ confidence rates
- **Error Handling**: Comprehensive retry and rollback

#### 🚀 Web Performance
- **Development Server**: Hot reload on port 3000
- **Database Queries**: Optimized with connection pooling
- **Real-time Updates**: 2-second refresh delays
- **Response Time**: Sub-second API responses

## 🛠️ Development Guidelines

### Running the System
```bash
# Extract fresh Sitecore data
python launch.py GrabSiteCoreData

# Start web platform
python launch.py web-dev
# OR
cd web-platform && npm run dev

# Generate database report
python launch.py database_report

# Diagnose connectivity
python launch.py diagnose_database
```

### Architecture Principles
1. **Separation of Concerns**: Clear boundaries between CLI, web, and data layers
2. **Single Responsibility**: Each component has a focused purpose
3. **Defensive Programming**: Comprehensive error handling throughout
4. **Real-time Capabilities**: Live data updates and status monitoring
5. **Extensibility**: Modular design for future enhancements

### Quality Assurance
- **Type Safety**: Full TypeScript coverage in web platform
- **Error Handling**: Result patterns and graceful degradation
- **Testing**: Comprehensive test coverage for critical paths
- **Monitoring**: Real-time connection and extraction status

This architectural documentation provides a complete view of the Smart Sitecore Analysis Platform v2.0, enabling developers, administrators, and stakeholders to understand the system's design, capabilities, and operational characteristics.