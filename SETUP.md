# Commodity AI Dashboard - Setup Guide

## 📋 Prerequisites

- Python 3.8 or higher
- Perplexity AI API key (get from [Perplexity Settings](https://www.perplexity.ai/settings/api))

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

### 4. Configure API Key

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your Perplexity API key:

```
PERPLEXITY_API_KEY=your_actual_api_key_here
```

### 5. Run the Dashboard

```bash
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8501`

## 📁 Project Structure

```
2025 - Commodity AI/
├── app.py                    # Main Streamlit dashboard
├── config.yaml              # Configuration file
├── requirements.txt         # Python dependencies
├── .env                     # API keys (create from .env.example)
├── .env.example            # Template for environment variables
├── README.md               # Project overview and objectives
├── SETUP.md                # Installation and setup guide
├── CLAUDE.md               # Technical documentation
├── src/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── perplexity_client.py    # Perplexity AI API wrapper
│   │   └── commodity_queries.py     # Query orchestration with caching
│   ├── processing/
│   │   ├── __init__.py
│   │   └── data_processor.py        # Data formatting and processing
│   └── storage/
│       ├── __init__.py
│       └── database.py              # SQLite database with daily caching
├── data/                    # Data storage (auto-created)
│   └── commodity_data.db   # SQLite database file
└── logs/                    # Log files (auto-created)
```

## 🎯 Features

### Timeframe Selection
- **1 week**: Short-term price movements and immediate catalysts
- **1 month**: Medium-term trends and structural changes

### Steel Sector Commodity Coverage
- **Steel Raw Materials**: Iron ore, coking coal, scrap steel
- **Steel Products**: Rebar, Hot Rolled Coil (HRC)

### JSON-Structured Queries
The system uses structured JSON queries to Perplexity AI for consistent data:
```json
{
    "commodity": "iron ore",
    "current_price": "USD 116/ton",
    "price_change": "+1.8%",
    "trend": "bullish",
    "key_drivers": ["China demand", "Supply issues"],
    "recent_news": ["Jan 4: Market update..."],
    "source_urls": [
        "https://www.reuters.com/markets/commodities/specific-article",
        "https://tradingeconomics.com/commodity/iron-ore/news-article"
    ]
}
```

**Key Feature**: Full clickable URLs are provided for each source, allowing users to follow up on specific news articles.

### Dashboard Sections
1. **Metrics Overview**: Quick stats on market trends
2. **Summary Table**: Comprehensive view with prices, changes, drivers
3. **News Cards**: Recent developments with clickable source links
   - Each source is a clickable link to the original article
   - Links open in new tabs for easy reference
   - Domain names displayed for clean interface
4. **Export Options**: JSON, CSV, or Markdown format

## 🔧 Configuration Options

Edit `config.yaml` to customize:

- Commodity list and keywords
- Query refresh intervals
- Dashboard appearance
- Cache duration
- Database retention period

## 📊 Using the Dashboard

1. **Select Timeframe**: Choose between 1 week or 1 month analysis
2. **Data Refresh Options**:
   - **Get Today's Data**: Uses cached data if available (recommended)
   - **Force Refresh**: Forces new query to Perplexity AI
   - **Clear Cache**: Clears all memory and session caches
3. **Filter by Category**: Use the sidebar to filter commodities
4. **Export Data**: Download results in JSON, CSV, or Markdown format
5. **Auto-refresh**: Enable to automatically update every 30 minutes

### Data Source Indicators
- ✅ **"Using today's cached data from database"** - Data from SQLite cache
- ✅ **"Fresh data retrieved from Perplexity AI"** - New API query made

## 🔍 Troubleshooting

### API Key Issues
- Ensure your Perplexity API key is valid
- Check that `.env` file is in the project root
- Verify the key has proper permissions

### Connection Errors
- Check internet connectivity
- Verify Perplexity API is accessible
- Review logs in `logs/` directory

### No Data Displayed
- Click "Refresh Data" to fetch initial data
- Check commodity queries in logs
- Ensure timeframe is selected

## 📈 Data Sources

The dashboard uses Perplexity AI to aggregate data from:
- Reuters Commodities
- Trading Economics
- Mining.com
- SteelOrbis
- Bloomberg
- Investing.com
- And other freely accessible sources

## 🔐 Security Notes

- Never commit `.env` file to version control
- Keep your API key confidential
- Regularly rotate API keys
- Monitor API usage to avoid exceeding limits

## 📝 Advanced Usage

### Custom Commodities

Add new commodities in `config.yaml`:

```yaml
commodities:
  - name: "lithium"
    display_name: "Lithium"
    category: "Battery Metals"
    unit: "USD/ton"
    vietnam_specific: false
    query_keywords:
      - "lithium carbonate"
      - "battery grade"
      - "EV demand"
```

### Database Queries

Access historical data:

```python
from src.storage.database import CommodityDatabase

db = CommodityDatabase()
history = db.get_price_history("iron ore", days=30)
```

### Scheduling Updates

For automated updates, use a task scheduler:

**Windows (Task Scheduler)**:
Create a batch file `run_dashboard.bat`:
```batch
cd /d "C:\path\to\project"
call venv\Scripts\activate
python -m streamlit run app.py
```

**Linux/Mac (cron)**:
```bash
# Add to crontab
0 9 * * * cd /path/to/project && source venv/bin/activate && streamlit run app.py
```

## 🤝 Support

For issues or questions:
1. Check the logs in `logs/` directory
2. Review configuration in `config.yaml`
3. Ensure all dependencies are installed
4. Verify Perplexity API status

## 📄 License

This project is designed for internal use at Dragon Capital for monitoring commodity markets relevant to Vietnamese steel sector.