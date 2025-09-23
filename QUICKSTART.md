# Smart Sitecore Analysis Platform v2.0 - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Prerequisites
- Python 3.8+
- Node.js 18+
- PostgreSQL database access
- Sitecore instance with GraphQL API

### 1. Configuration Setup (30 seconds)
```bash
# First-time configuration (creates config.json automatically)
python launch.py --config-help  # See all available options

# Quick setup with your credentials
python launch.py inspect_schema \
  --sitecore-url "https://your-sitecore.com" \
  --sitecore-api-key "{YOUR-API-KEY}" \
  --db-host "your-database.com" \
  --db-user "your-username"
```
**Expected**: Shows 26+ tables including `scans_v2`, `analysis_results`

### 2. Extract Sitecore Data (60 seconds)
```bash
# With config.json created, simply run:
python launch.py GrabSiteCoreData

# OR set parameters inline if needed:
python launch.py GrabSiteCoreData \
  --customer-name "Your Company" \
  --site-name "Production Site"
```
**Expected**: Extracts sites from your configured Sitecore instance

### 3. Start Web Platform (30 seconds)
```bash
# Easy way (uses config.json settings):
python launch.py web-dev

# OR manually:
cd web-platform && npm install && npm run dev
```
**Access**: http://localhost:3000 (or configured port)

### 4. View Results (Instantly)
- **"Extracted Sitecore Data" tab**: See your discovered sites
- **Real-time statistics**: Scan history and success rates
- **Site details**: Templates, child counts, content structure

## 🎯 What You'll See

### Discovered Sitecore Sites
The dashboard will display all sites found in your Sitecore instance:
- **Site names and paths** (e.g., `/sitecore/content/YourSite`)
- **Template types** (e.g., App, Sample Item, Folder)
- **Content metrics** (child counts, field samples)
- **Extraction timestamps** and confidence scores

### Live Statistics
- **Database**: Connection status indicator
- **Total scans** with success/failure counts
- **Last scan timestamp** from your extractions
- **Confidence scores**: Based on extraction quality

## 🔧 Quick Commands

### Data Operations
```bash
python launch.py GrabSiteCoreData     # Extract fresh Sitecore data
python launch.py database_report      # Generate HTML report
python launch.py clear_database       # Reset for fresh extraction
```

### Web Platform
```bash
python launch.py web-dev             # Start web development server
# OR manually:
cd web-platform && npm run dev      # Manual start (more reliable)
```

### Troubleshooting
```bash
python launch.py diagnose_database   # Test database connectivity
python launch.py test_credentials    # Verify authentication
```

## ⚡ Key Features Working

✅ **Real-time Sitecore data visualization**
✅ **Interactive site browser with content details**
✅ **Web-based extraction triggers**
✅ **Database connectivity monitoring**
✅ **Complete v2.0 multi-site architecture**

## 🐛 Common Issues

**Port in use**: Web server automatically finds available port
**Database connection error**: Check credentials with `python launch.py diagnose_database`
**Missing config.json**: Run with configuration parameters to create automatically
**Chunk loading error**: Clear cache with `rm -rf .next && npm run dev`
**No sites found**: Verify Sitecore URL and API key in config.json

## 📈 Next Steps

1. **Configuration tuning**: Use `python launch.py --config-help` for all options
2. **Add multiple sites**: Update Sitecore endpoints in config.json
3. **Schedule extractions**: Set up automated data collection
4. **Custom dashboards**: Build site-specific analysis views
5. **Export capabilities**: Generate reports and data exports

**🎉 You now have a fully functional Smart Sitecore Analysis Platform displaying real extracted data!**