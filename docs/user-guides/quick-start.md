# Commodity Dashboard - Quick Start Guide

## 📋 Prerequisites

- Python 3.8 or higher
- MS SQL Server connection (required)
- Perplexity AI API key (optional, for AI features)

## 🚀 Quick Start

### 1. Clone or Download the Project

```bash
cd "2025 - Commodity AI"
```

### 2. Create Virtual Environment (Recommended)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Database Connection

Set your MS SQL Server connection string:

```bash
# Windows (PowerShell)
$env:DC_DB_STRING="DRIVER={ODBC Driver 17 for SQL Server};SERVER=your_server;DATABASE=your_db;UID=user;PWD=password"

# Linux/Mac
export DC_DB_STRING="DRIVER={ODBC Driver 17 for SQL Server};SERVER=your_server;DATABASE=your_db;UID=user;PWD=password"
```

### 5. Run the Unified Dashboard

#### Basic Mode (SQL Data Only)
```bash
streamlit run current/sql-dashboard/main.py
```

#### With AI Features (Optional)
```bash
# Set environment variables
export ENABLE_AI_FEATURES=true
export PERPLEXITY_API_KEY="your_perplexity_api_key"

# Run dashboard with AI intelligence
streamlit run current/sql-dashboard/main.py
```

The dashboard will open in your browser at `http://localhost:8501`

## 📁 Project Structure

```
2025 - Commodity AI/
├── current/
│   └── sql-dashboard/              # Unified dashboard
│       ├── main.py                 # Entry point
│       ├── modules/                # Core modules
│       │   ├── db_connection.py    # MSSQL connection
│       │   ├── data_loader.py      # Data fetching
│       │   ├── calculations.py     # Analytics
│       │   └── ai_integration/     # AI features (optional)
│       │       ├── perplexity_client.py
│       │       ├── commodity_queries.py
│       │       └── data_processor.py
│       └── pages/                  # Additional pages
├── config.yaml                     # Configuration
├── requirements.txt                # Dependencies
└── .docs/                         # Documentation
```

## 🎯 Features

### Base Dashboard (Always Available)
- **Real-time Prices**: Live commodity data from MS SQL Server
- **Z-Score Analysis**: Frequency-aware statistical analysis
- **Technical Indicators**: Price changes, trends, volatility
- **Interactive Charts**: Plotly-based visualizations
- **Stock Integration**: Related equities tracking

### AI Features (When Enabled)
- **Market Intelligence**: AI-powered insights from Perplexity
- **News Aggregation**: Recent developments with sources
- **Trend Analysis**: Bullish/bearish sentiment detection
- **Key Drivers**: Market catalysts and influences
- **Smart Caching**: 3-tier cache system for cost optimization

## 🔧 Environment Variables

### Required
```bash
DC_DB_STRING="your_mssql_connection_string"
```

### Optional (for AI Features)
```bash
ENABLE_AI_FEATURES=true              # Enable AI intelligence
PERPLEXITY_API_KEY="your_api_key"    # Perplexity API access
DC_DB_STRING_MASTER="write_access"   # Optional write permissions for caching
```

### Development Options
```bash
LOG_LEVEL=DEBUG                      # Detailed logging
MOCK_API=true                        # Use mock data for testing
CACHE_ENABLED=false                  # Disable caching for development
```

## 📊 Using the Dashboard

### 1. Dashboard Sections

#### Without AI Features
- **Market Metrics**: Overview of market conditions
- **Price Table**: Detailed commodity prices and changes
- **Charts**: Technical analysis and trends
- **Stock Correlations**: Related equity movements

#### With AI Features Enabled
All of the above plus:
- **AI Intelligence Summary**: Market trends and drivers
- **News Cards**: Recent market developments
- **Confidence Scores**: AI certainty indicators
- **Source Citations**: Clickable links to original sources

### 2. Navigation

#### Sidebar Controls
- **Filters**: Sector, Nation, Change Type, Commodity
- **Chart Options**: Customize visualizations
- **AI Controls** (if enabled):
  - Timeframe selection (1 week / 1 month)
  - Refresh AI data
  - Clear cache

### 3. Data Refresh

#### SQL Data
- Automatically loads on page refresh
- Real-time connection to database

#### AI Data (if enabled)
- **Cached by default**: Uses daily cache to minimize API costs
- **Force Refresh**: Override cache for immediate updates
- **Auto-refresh**: Optional 30-minute updates

## 🔍 Troubleshooting

### Database Connection Issues
```bash
# Test your connection string
python -c "import pyodbc; pyodbc.connect('$DC_DB_STRING')"
```

### AI Features Not Showing
1. Verify `ENABLE_AI_FEATURES=true`
2. Check `PERPLEXITY_API_KEY` is set
3. Review logs for initialization errors

### Performance Issues
- Enable caching: `CACHE_ENABLED=true`
- Check database query performance
- Monitor API response times in logs

## 📈 Data Sources

### SQL Database
- Real-time commodity prices
- Historical price data
- Market indicators

### AI Intelligence (Optional)
Aggregated from:
- Reuters Commodities
- Trading Economics
- Mining.com
- SteelOrbis
- Bloomberg
- Other freely accessible sources

## 🚀 Advanced Usage

### Development Mode
```bash
# Auto-reload on code changes
streamlit run current/sql-dashboard/main.py --server.runOnSave=true

# Debug mode with detailed logging
LOG_LEVEL=DEBUG streamlit run current/sql-dashboard/main.py
```

### Testing
```bash
# Run test suite
pytest tests/

# Test AI integration
pytest tests/test_ai_integration.py
```

### Custom Configuration
Edit `config.yaml` to customize:
- Commodity definitions
- API settings
- Cache duration
- Dashboard appearance

## 🔐 Security Notes

- Never commit API keys to version control
- Use environment variables for sensitive data
- Implement proper access controls for database
- Monitor API usage to avoid quota issues

## 📊 Migration Status

### Current Phase
The project is actively migrating to a unified dashboard:
- ✅ Database migration complete
- 🟡 Unified dashboard implementation in progress
- 🔵 Sector expansion planned next

### Legacy Dashboards
While the unified dashboard is being implemented, legacy dashboards remain available:
```bash
# Legacy AI Dashboard (deprecated)
streamlit run current/ai-dashboard/main.py

# Current SQL Dashboard (being enhanced)
streamlit run current/sql-dashboard/main.py
```

## 🤝 Support

For issues or questions:
1. Check logs in development mode: `LOG_LEVEL=DEBUG`
2. Review configuration in `config.yaml`
3. Consult documentation in `.docs/`
4. Verify database connectivity
5. Check API status (if using AI features)

## 📄 License

This project is designed for internal use at Dragon Capital for monitoring commodity markets relevant to Vietnamese steel sector.