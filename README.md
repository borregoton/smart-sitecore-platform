# 🚀 Smart Sitecore Analysis Platform

[![Version](https://img.shields.io/badge/version-2.0-blue.svg)](https://github.com/bbleak-repo/smart-sitecore-platform)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/next.js-14-black.svg)](https://nextjs.org/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-13+-blue.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)

A comprehensive enterprise-grade toolkit for analyzing, extracting, and visualizing data from Sitecore instances. Features include GraphQL-based extraction, real-time web dashboard, multi-site support, and advanced architectural analysis.

![Dashboard Preview](docs/architecture/images/Smart%20Sitecore%20Analysis%20-%20C4%20Context%20Diagram.png)

## ✨ Features

### 🎯 Core Capabilities
- **GraphQL Data Extraction** - Direct integration with Sitecore GraphQL API
- **Multi-Site Support** - Analyze multiple Sitecore instances simultaneously
- **Real-Time Dashboard** - Modern Next.js web interface with live data
- **PostgreSQL Storage** - Enterprise-grade data persistence with Supabase
- **Architectural Analysis** - C4 model diagrams and system visualization
- **Security Scanning** - Built-in security assessment tools
- **Performance Metrics** - Site performance and optimization insights

### 🔧 Technical Stack
- **Backend**: Python 3.8+ with FastAPI/Flask
- **Frontend**: Next.js 14, React 18, TypeScript
- **Database**: PostgreSQL 13+ (Supabase compatible)
- **ORM**: Prisma (Web), psycopg2 (Python)
- **Styling**: Tailwind CSS
- **Documentation**: PlantUML, C4 Model

## 📚 Documentation

### Quick Links
- 📖 **[Project Structure](PROJECT_STRUCTURE.md)** - Complete repository organization
- 🚀 **[Quick Start Guide](QUICKSTART.md)** - Get up and running in 5 minutes
- 🔧 **[Development Guide](DEVELOPMENT.md)** - Detailed development setup
- 📊 **[Database Guide](DATABASE_CONNECTION_STATUS.md)** - Database configuration
- 📝 **[Handoff Notes](HANDOFF-NOTES.md)** - Project transfer documentation
- 🎮 **[Launcher Guide](LAUNCHER_README.md)** - GUI launcher documentation
- ⚡ **[Current Status](STATUS.md)** - Latest project status
- 🗄️ **[Supabase Integration](supabase_kit.md)** - Supabase setup guide

## 🚀 Quick Start

### Prerequisites
```bash
# Required software
- Python 3.8+
- Node.js 18+
- PostgreSQL 13+ (or Supabase account)
- Sitecore instance with GraphQL API enabled
```

### 1. Clone & Setup
```bash
# Clone the repository
git clone https://github.com/bbleak-repo/smart-sitecore-platform.git
cd smart-sitecore-platform/Project20

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
cd web-platform && npm install && cd ..
```

### 2. Configure
```bash
# Create configuration (interactive)
python launch.py --config-help

# Or create config with parameters
python launch.py GrabSiteCoreData \
  --sitecore-url "https://your-sitecore.com" \
  --sitecore-api-key "{YOUR-API-KEY}" \
  --db-host "your-database.com" \
  --db-user "your-username" \
  --customer-name "Your Organization"
```

### 3. Extract & Launch
```bash
# Extract Sitecore data
python launch.py GrabSiteCoreData

# Start web dashboard
python launch.py web-dev

# Access dashboard at http://localhost:3000
```

## 📊 Architecture Diagrams

The platform includes comprehensive architectural documentation with PlantUML diagrams:

### System Architecture
- **[C4 Context Diagram](docs/architecture/images/Smart%20Sitecore%20Analysis%20-%20C4%20Context%20Diagram.png)** - System boundaries and external dependencies
- **[C4 Container Diagram](docs/architecture/images/Smart%20Sitecore%20Analysis%20-%20C4%20Container%20Diagram.png)** - High-level technical components
- **[Data Flow Architecture](docs/architecture/images/Smart%20Sitecore%20Analysis%20-%20Data%20Flow%20Architecture.png)** - End-to-end data flow

### Component Details
- **[Web Platform Components](docs/architecture/images/Smart%20Sitecore%20Analysis%20-%20C4%20Component%20Diagram%20(Web%20Platform).png)** - Frontend architecture
- **[Extraction Engine Components](docs/architecture/images/Smart%20Sitecore%20Analysis%20-%20C4%20Component%20Diagram%20(Extraction%20Engine).png)** - Backend architecture

### Sequence Diagrams
- **[Extraction Sequence](docs/architecture/images/Smart%20Sitecore%20Analysis%20-%20Data%20Extraction%20Sequence.png)** - Data extraction workflow
- **[Dashboard Sequence](docs/architecture/images/Smart%20Sitecore%20Analysis%20-%20Web%20Dashboard%20Sequence.png)** - Dashboard data flow
- **[Web-Triggered Extraction](docs/architecture/images/Smart%20Sitecore%20Analysis%20-%20Web-Triggered%20Extraction%20Sequence.png)** - User-initiated extraction

## 🎯 Command Reference

### Data Operations
```bash
python launch.py GrabSiteCoreData       # Extract Sitecore data
python launch.py database_report        # Generate HTML report
python launch.py clear_database         # Reset database
python launch.py inspect_schema         # View database schema
```

### Web Platform
```bash
python launch.py web-dev               # Start development server
python launch.py web-build             # Build for production
python launch.py web-api               # Start API server only
```

### Database Management
```bash
python launch.py diagnose_database     # Test connectivity
python launch.py test_credentials      # Verify authentication
python launch.py fix_v2_schema         # Apply schema migrations
```

### Analysis & Reports
```bash
python launch.py generate_extraction_report  # Full extraction report
python launch.py audit_phase1_data          # Audit extracted data
python launch.py inspect_database_schema    # Schema inspection
```

## 🔧 Configuration

The platform uses a centralized `config.json` file:

```json
{
  "sitecore": {
    "url": "https://your-sitecore.com",
    "api_key": "{YOUR-API-KEY}",
    "timeout": 30
  },
  "database": {
    "host": "your-database.com",
    "port": 5432,
    "database": "postgres",
    "username": "your-username",
    "password": "your-password"
  },
  "web_server": {
    "host": "localhost",
    "port": 3000,
    "environment": "development"
  },
  "extraction": {
    "customer_name": "Your Organization",
    "verbose": true
  }
}
```

### Configuration Options
```bash
# View all configuration options
python launch.py --config-help

# Override configuration temporarily
python launch.py web-dev --port 8080 --no-save

# Update configuration permanently
python launch.py web-dev --port 8080 --save
```

## 🐳 Docker Deployment

### Local Docker
```bash
# Build and run with Docker
docker build -f Dockerfile.web-api -t sitecore-platform .
docker run -p 3000:3000 --env-file .env sitecore-platform
```

### Docker Compose
```bash
# Development environment
docker-compose -f docker/docker-compose.dev.yml up

# Production environment
docker-compose -f docker/docker-compose.prod.yml up -d
```

## 📈 What You'll See

### Web Dashboard Features
- **Site Portfolio View** - All discovered Sitecore sites
- **Real-Time Metrics** - Live extraction statistics
- **Analysis Results** - Security, architecture, and performance insights
- **Historical Data** - Track changes over time
- **Export Options** - Generate reports in multiple formats

### Sample Extracted Data
```
✅ Sites Discovered: 4
   • Home (/sitecore/content/Home)
   • nextjs-app-21 (/sitecore/content/nextjs-app-21)
   • react-app-21 (/sitecore/content/react-app-21)
   • TG Architects (/sitecore/content/TG Architects)

✅ Statistics:
   • Total Scans: 9
   • Successful: 2
   • Average Confidence: 92%
   • Templates Analyzed: 15
   • Fields Processed: 148
```

## 🛠️ Development

### Setting Up Development Environment
```bash
# Python virtual environment
python -m venv sitecore_venv
source sitecore_venv/bin/activate  # Linux/Mac
# or
sitecore_venv\Scripts\activate  # Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Start development servers
python launch.py web-dev
```

### Running Tests
```bash
# Python tests
pytest cli/tests/

# JavaScript/TypeScript tests
cd web-platform && npm test
```

### Building for Production
```bash
# Build web platform
cd web-platform && npm run build

# Create production Docker image
docker build -t sitecore-platform:latest .
```

## 🔒 Security

- **API Keys**: Stored in `config.json` (gitignored)
- **Database**: SSL/TLS connections recommended
- **Authentication**: Row-level security for multi-tenancy
- **Encryption**: Sensitive data encrypted at rest
- **Audit Logs**: All operations logged for compliance

## 📊 Performance

- **Extraction Speed**: ~1000 items/minute
- **Dashboard Load**: <2 seconds
- **Database Queries**: Optimized with indexes
- **Caching**: Redis support for production
- **Scalability**: Horizontal scaling supported

## 🤝 Contributing

We welcome contributions! Please see [DEVELOPMENT.md](DEVELOPMENT.md) for guidelines.

### Development Process
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **PlantUML** for architecture diagrams
- **C4 Model** for architectural patterns
- **Next.js** for the web framework
- **Sitecore** for the CMS platform
- **PostgreSQL** for database excellence

## 📞 Support

- **Documentation**: See `/docs` folder
- **Issues**: [GitHub Issues](https://github.com/bbleak-repo/smart-sitecore-platform/issues)
- **Discussions**: [GitHub Discussions](https://github.com/bbleak-repo/smart-sitecore-platform/discussions)

---

**Made with ❤️ by the DelusionalSecurity Development Team**

*Smart Sitecore Analysis Platform - Transforming Sitecore data into actionable insights*