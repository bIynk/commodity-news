# Commodity Market Intelligence Dashboard

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/streamlit-1.29-FF4B4B.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Multi-commodity market intelligence platform** combining real-time SQL Server data with AI-powered insights for the Vietnamese market.

## Overview

A unified Streamlit dashboard that monitors **95+ commodities** across 11 sectors, providing:
- 📊 Real-time price data from MS SQL Server
- 🤖 AI-powered market intelligence via Perplexity AI
- 📈 Advanced analytics with z-score volatility detection
- 📰 Curated news with source citations
- 💾 Smart 3-tier caching (Memory → Database → API)

**Target Market**: Vietnamese steel sector and related commodity analysis

---

## Quick Start

### Prerequisites
- Python 3.11+
- MS SQL Server access
- Perplexity API key ([Get one here](https://www.perplexity.ai/))
- **Database Driver** (automatically selected):
  - `pymssql` - For Streamlit Cloud (no system dependencies)
  - `pyodbc` - For local development (requires ODBC Driver 17)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd commodity-dashboard

# Install dependencies
cd app
pip install -r requirements.txt

# Copy environment template
cp ../.env.example ../.env
# Edit .env with your credentials
```

### Configuration

Set up your environment variables in `.env`:

```bash
# Required: Database connection
DC_DB_STRING="DRIVER={ODBC Driver 17 for SQL Server};SERVER=your_server;DATABASE=CommodityDB;UID=user;PWD=password"

# Required: AI features
PERPLEXITY_API_KEY="your_perplexity_api_key"

# Optional: Write access for new AI queries
DC_DB_STRING_MASTER="connection_string_with_write_permissions"

# Optional: Configuration
AI_ZSCORE_THRESHOLD="2.0"
AI_CACHE_HOURS="24"
MAX_NEWS_ITEMS="6"
LOG_LEVEL="INFO"
```

### Running the Dashboard

```bash
# From app/ directory
streamlit run main.py

# With auto-reload (development)
streamlit run main.py --server.runOnSave=true

# With debug logging
LOG_LEVEL=DEBUG streamlit run main.py
```

Access the dashboard at: `http://localhost:8501`

---

## Features

### 📊 Real-Time Market Data
- **95+ commodities** across 11 sectors
- Live price updates from MS SQL Server
- Multi-period price changes (1D, 1W, 1M, 3M, 6M, 1Y)
- Frequency-aware z-score calculations
- Interactive charts and tables

### 🤖 AI Market Intelligence
- Automated market analysis via Perplexity AI
- Trend detection (bullish/bearish/stable)
- Key market drivers identification
- Recent news aggregation with sources
- Vietnam-specific market insights

### 💾 Smart Caching System
- **3-tier cache hierarchy**:
  1. Memory cache (~1ms) - Session state
  2. Database cache (10-50ms) - 7-day lookback
  3. Perplexity API (2-5s) - Fresh data
- **Z-score filtering**: Only queries high-volatility commodities (|z-score| > 2.0)
- **Cost optimization**: 80-90% reduction in API calls

### 📈 Advanced Analytics
- Frequency-aware z-score calculations
- Automatic data frequency detection (daily/weekly)
- Staleness filtering (7-day/14-day)
- Stock impact analysis
- Multi-commodity correlation tracking

### 🎯 Sector Coverage
- Agricultural (Corn, Soybeans, Wheat, etc.)
- Chemicals (Urea, Ammonia, Methanol, etc.)
- Energy (Crude Oil, Natural Gas, Coal, etc.)
- Fertilizer (DAP, Potash, etc.)
- Metals (Aluminum, Copper, Zinc, etc.)
- Precious Metals (Gold, Silver, Platinum, etc.)
- Shipping (Baltic Dry Index, routes)
- Steel Raw Materials (Iron Ore, Coking Coal, Scrap)
- Steel Products (Rebar, HRC, CRC, Wire Rod)
- Soft Commodities (Cocoa, Orange Juice, Lumber)
- Other (FX rates, indices)

---

## Architecture

### System Components

```
┌────────────────────────────────────────┐
│      Streamlit Dashboard (app/)         │
└────────────────────────────────────────┘
              │
      ┌───────┴───────┐
      │               │
┌─────▼─────┐   ┌────▼────────┐
│  SQL Data │   │ AI Features │
│  (Always) │   │  (Optional) │
└─────┬─────┘   └────┬────────┘
      │               │
┌─────▼─────┐   ┌────▼────────┐
│  MS SQL   │   │ Perplexity  │
│  Server   │   │ API + Cache │
└───────────┘   └─────────────┘
```

### Project Structure

```
commodity-dashboard/
├── app/                        # Production application
│   ├── main.py                 # Entry point
│   ├── config/                 # Configuration files
│   │   └── news_sources.yaml  # Sector-specific sources
│   ├── modules/                # Core modules
│   │   ├── ai_integration/     # AI features
│   │   │   ├── perplexity_client.py
│   │   │   ├── commodity_queries.py
│   │   │   ├── data_processor.py
│   │   │   ├── ai_database.py
│   │   │   └── sector_config.py
│   │   ├── calculations.py     # Analytics engine
│   │   ├── data_loader.py      # Data fetching
│   │   ├── db_connection.py    # Database management
│   │   └── styling.py          # UI components
│   ├── pages/                  # Additional pages
│   │   └── Chart_Analysis.py
│   └── requirements.txt
│
├── tests/                      # Test suite
│   ├── conftest.py
│   └── test_*.py
│
├── docs/                       # Documentation
│   ├── architecture/           # System design
│   ├── development/            # Dev guides
│   ├── setup/                  # Installation guides
│   └── README.md
│
├── scripts/                    # Utility scripts
│   └── migrate_to_mssql.py
│
├── archive/                    # Archived legacy code
│
├── .streamlit/                 # Streamlit config
│   └── config.toml
│
└── README.md                   # This file
```

### Data Flow

1. **Load SQL Data** → Fetch real-time prices from MSSQL
2. **Calculate Analytics** → Z-scores, indicators, frequency detection
3. **Check AI Cache** → Memory → Database → Historical intelligence
4. **Query AI** (if needed) → Perplexity API for high-volatility commodities
5. **Merge & Display** → Unified dashboard with all insights

---

## Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/

# With coverage
pytest --cov=app tests/

# Specific test file
pytest tests/test_ai_integration.py -v
```

### Code Quality

```bash
# Format code
black app/ tests/

# Lint
flake8 app/ tests/

# Type checking
mypy app/
```

### Development Mode

```bash
# Run with auto-reload
cd app
streamlit run main.py --server.runOnSave=true

# Debug mode with detailed logging
LOG_LEVEL=DEBUG streamlit run main.py

# Mock API for testing (no API calls)
MOCK_API=true streamlit run main.py
```

---

## Database Schema

### Core Tables
- `Ticker_Reference` - Commodity metadata (95+ commodities)
- `Price_Data` - Historical price data
- `AI_Query_Cache` - Cached API responses (24h TTL)
- `AI_Market_Intelligence` - Processed AI analysis with Query_Date
- `AI_News_Items` - News articles with sources

See [Database Documentation](docs/architecture/database-schema.md) for details.

---

## Performance

### Benchmarks
- **Page Load**: <2s with cache
- **Memory Cache**: ~1ms response
- **Database Cache**: 10-50ms response
- **API Query**: 2-5s per commodity
- **Cache Hit Rate**: 80-90% after warmup

### Optimization Features
- Z-score filtering reduces API calls by 80-90%
- 3-tier caching minimizes database queries
- Frequency-aware calculations adapt to data patterns
- Async loading for AI section (Streamlit fragments)
- Smart staleness detection

---

## Documentation

📚 **Comprehensive documentation available in [`docs/`](docs/)**

### Quick Links
- [Installation Guide](docs/setup/installation.md)
- [System Architecture](docs/architecture/system-overview.md)
- [Database Design](docs/architecture/database-schema.md)
- [API Integration](docs/implementation/ai-dashboard/perplexity-integration.md)
- [Debugging Guide](docs/development/debugging-guide.md)
- [Coding Standards](docs/development/coding-standards.md)

### Key Concepts
- [Z-Score Calculation](docs/implementation/sql-dashboard/zscore-calculation.md)
- [Caching Strategy](docs/architecture/caching-architecture.md)
- [Query Orchestration](docs/implementation/ai-dashboard/query-orchestration.md)

---

## Deployment

### Database Driver Support

The application **automatically detects** and uses the appropriate SQL Server driver:

- **pymssql** (Streamlit Cloud) - Pure Python, no system dependencies
- **pyodbc** (Local Development) - Requires ODBC Driver 17 for SQL Server

No code changes needed - just install the appropriate driver for your environment.

### Environment Setup

1. **Streamlit Cloud Deployment**
   ```toml
   # Add to .streamlit/secrets.toml
   DC_DB_STRING = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=host;DATABASE=db;UID=user;PWD=pass"
   PERPLEXITY_API_KEY = "your_api_key"
   ```
   See [Deployment Guide](docs/setup/deployment.md) for detailed instructions.

2. **Local Development**
   ```bash
   # Add to .env file
   DC_DB_STRING="DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=CommodityDB;UID=user;PWD=pass"
   PERPLEXITY_API_KEY="your_api_key"
   ```

3. **Database Configuration**
   - Ensure MS SQL Server is accessible
   - Grant appropriate permissions (read-only for basic features)
   - Optional: Write access for new AI query caching

4. **API Keys**
   - Obtain Perplexity API key
   - Monitor usage and set budget alerts
   - Configure rate limiting if needed

### Docker Deployment

```dockerfile
# TODO: Add Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY app/ ./
RUN pip install -r requirements.txt
CMD ["streamlit", "run", "main.py", "--server.port=8501"]
```

---

## Project Status

### ✅ Completed
- Unified dashboard with AI integration
- MSSQL migration with AI tables
- 3-tier caching system
- Dynamic commodity loading (95+ commodities)
- Sector-specific news source guidance
- Z-score filtering and cost optimization
- Query date tracking for AI analysis
- Comprehensive documentation

### 🚧 In Progress
- Query budget controls and cost tracking
- Enhanced error handling and retry logic
- Additional test coverage

### 📋 Roadmap
- Remove SSL workaround for production
- REST API for external integrations
- User authentication and preferences
- Real-time WebSocket updates
- Mobile-responsive UI improvements
- Export functionality (PDF/Excel reports)

---

## Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow coding standards ([docs/development/coding-standards.md](docs/development/coding-standards.md))
4. Write tests for new features
5. Ensure all tests pass (`pytest tests/`)
6. Format code (`black app/ tests/`)
7. Commit changes (`git commit -m 'Add amazing feature'`)
8. Push to branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

### Code Standards
- Python 3.11+ with type hints
- Black formatting (line length 100)
- Comprehensive docstrings
- Unit tests for new features
- Follow existing patterns

---

## Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Check connection string format
# Verify ODBC Driver 17 is installed
# Test network connectivity to SQL Server
```

**API Rate Limiting**
```bash
# Adjust AI_ZSCORE_THRESHOLD to reduce API calls
# Increase AI_CACHE_HOURS for longer cache duration
# Use MOCK_API=true for testing without API calls
```

**SSL Certificate Warnings**
```bash
# This is a known issue - SSL verification temporarily disabled
# See docs/architecture/ssl-workaround.md for details
# Will be resolved before production deployment
```

See [Debugging Guide](docs/development/debugging-guide.md) for detailed troubleshooting.

---

## License

MIT License - see [LICENSE](LICENSE) file for details

---

## Acknowledgments

- **Perplexity AI** - Market intelligence API
- **Streamlit** - Dashboard framework
- **Microsoft SQL Server** - Database platform
- **Dragon Capital Research Team** - Domain expertise

---

## Contact

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/commodity-dashboard/issues)
- **Email**: research@dragon-capital.com

---

**Version**: 2.0.0
**Last Updated**: 2025-09-30
**Status**: Production-ready (pending SSL fix)