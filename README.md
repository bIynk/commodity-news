## 1. Introduction
The Vietnamese steel market is highly influenced by movements in global and regional commodity prices and demand trends. Staying ahead requires continuous monitoring of market-moving news across key commodities and macroeconomic drivers.

This project provides a **unified commodity dashboard** that combines real-time SQL Server market data with AI-powered intelligence. The dashboard enriches market data with **structured summaries** (commodity movements and drivers) and **recent news snippets** (short articles with sources) powered by Perplexity AI.

The system leverages **MS SQL Server** for real-time price data and optionally uses Perplexity AI to retrieve, summarize, and present market insights with an intelligent **daily caching system** to minimize API costs.

### Quick Start
```bash
# Install dependencies
cd app
pip install -r requirements.txt

# Set up required environment variables
export DC_DB_STRING="your_mssql_connection_string"
export PERPLEXITY_API_KEY="your_api_key"

# Run the dashboard
streamlit run main.py

# Optional: Enable write access for new AI queries
export DC_DB_STRING_MASTER="connection_string_with_write_permissions"
```

> ⚠️ **SSL Certificate Warning**: The current code has SSL verification temporarily disabled for testing. See [Technical Debt Documentation](docs/architecture/ssl-workaround.md) for details on removing this before production deployment.

### Documentation
📚 **Full developer documentation is organized in `docs/`**

- **[Developer Documentation Hub](docs/README.md)** - Complete navigation guide
- **[Architecture](docs/architecture/)** - System design and architecture
- **[Development](docs/development/)** - Setup, coding standards, debugging
- **[Quick Start Guide](docs/setup/installation.md)** - Installation and usage  

---

## 2. Objectives
- Provide **daily, AI-curated structured summaries** of key commodities across all sectors.
- Present **short recent news articles with cited sources** for deeper context.
- Ensure all sources are **freely accessible** for AI retrieval.
- Cover **100+ commodities** across Agricultural, Chemicals, Energy, Fertilizer, Metals, Shipping, and Steel sectors.
- Map **sector-specific authoritative sources** to guide AI intelligence gathering.  

---

## 3. System Architecture

### Core Components
1. **SQL Dashboard Base** – Real-time commodity prices and z-score analysis from MS SQL Server
2. **AI Intelligence Layer** – Integrated Perplexity AI for market insights (now default)
3. **Smart Caching** – Three-tier cache system (Memory → Database → API) for AI queries
4. **Unified Display**
   - **Market Data**: Real-time prices, changes, and technical indicators from SQL
   - **AI Intelligence**: Structured summaries with drivers and trends
   - **News Cards**: Recent developments with source citations

### Component Interaction
```
┌──────────────────────────────────────────────────────┐
│              Unified Streamlit Dashboard              │
└──────────────────────────────────────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
    ┌───────▼────────┐          ┌────────▼────────┐
    │  SQL Data      │          │  AI Features    │
    │  (Always On)   │          │  (Optional)     │
    └───────┬────────┘          └────────┬────────┘
            │                             │
    ┌───────▼────────┐          ┌────────▼────────┐
    │   MS SQL       │          │   Perplexity    │
    │   Server       │          │   API + Cache   │
    └────────────────┘          └─────────────────┘
```

### Key Files
- `app/main.py` - Unified Streamlit dashboard
- `app/modules/` - Core SQL dashboard modules
- `app/modules/ai_integration/` - AI feature modules
  - `perplexity_client.py` - API communication with JSON parsing
  - `commodity_queries.py` - Query orchestration with 3-tier caching
  - `data_processor.py` - Formats AI data for display
  - `ai_database.py` - AI data persistence in MSSQL  

---

## 4. Workflow

### Base Dashboard (Always Available)
1. **Load Market Data** - Real-time commodity prices from MS SQL Server
2. **Calculate Indicators** - Z-scores, price changes, technical indicators
3. **Display Analytics** - Charts, tables, and market metrics

### Unified Workflow
1. **Load Market Data** - Real-time commodity prices from MS SQL Server
2. **Check AI Cache** - Memory → Database → API hierarchy
3. **Query Perplexity** (if needed) - Structured JSON requests for market intelligence
4. **Merge Intelligence** - Combine AI insights with SQL data
5. **Display Dashboard**
   - **Market Data**: Real-time prices and indicators (from SQL)
   - **AI Summary**: Trends, drivers, and confidence scores (from Perplexity)
   - **News Cards**: Recent developments with sources (from Perplexity)  

---

## 5. Environment Variables

### Required
```bash
# MS SQL Server connection string
DC_DB_STRING="DRIVER={ODBC Driver 17 for SQL Server};SERVER=your_server;DATABASE=your_db;UID=user;PWD=password"
```

### Required for AI Features
```bash
# Perplexity API key (required)
PERPLEXITY_API_KEY="your_perplexity_api_key"

# Database write access (optional - for new AI queries)
DC_DB_STRING_MASTER="connection_string_with_write_permissions"
```

### Optional Configuration
```bash
# AI Z-score threshold for querying (default: 2.0)
# Only commodities with |z-score| > threshold trigger new API calls
AI_ZSCORE_THRESHOLD="2.0"

# Cache duration in hours (default: 24)
AI_CACHE_HOURS="24"

# Max news items to display per commodity (default: 6)
MAX_NEWS_ITEMS="6"
```

---

## 6. Dashboard Layout

### **Top Section: Structured Market Summary (Table Format)**  

The structured summary will be displayed as a **table** with the following columns:  

| Commodity | Price/Change | Key Drivers (Catalysts) | Sources |  
|-----------|--------------|--------------------------|---------|  

**Example Table Output (Steel Sector Focus):**  

| Commodity     | Price/Change        | Key Drivers (Catalysts)                      | Sources*                      |  
|---------------|--------------------|-----------------------------------------------|-------------------------------|  
| Iron Ore      | +1.8% → USD 116/t  | China stimulus optimism, firm mill demand     | Reuters, Trading Economics    |  
| Coking Coal   | Stable → USD 280/t | Weather disruptions, steady Indian imports    | Mining, Hellenic             |  
| Scrap Steel   | +USD 5/t           | Seasonal demand recovery, higher freight costs| Scrapmonster, SteelOrbis     |  
| Steel Rebar   | +2.5%              | Vietnam construction boom, China exports      | Tradingeconomics, SteelOrbis |  
| Steel (HRC)   | +2%                | Policy support, auto sector demand            | Tradingeconomics, SteelOrbis |  

*Sources shown as domain names in table; full clickable URLs available in news cards  

---

### **Bottom Section: Recent Developments (News Cards Example - Steel Focus)**  

**🪨 Iron Ore**  
📌 *Jan 4: Iron ore rises on China demand hopes*  
📌 *Jan 3: Chinese mills ramp up restocking ahead of construction season*  
📌 *Jan 2: Prices lift to $116/ton on supply concerns*  
📰 Sources: [Reuters](actual-article-url) | [Trading Economics](actual-article-url) | [Mining.com](actual-article-url)

**🔥 Coking Coal**  
📌 *Jan 4: Cyclone threat keeps Australian coal buyers cautious*  
📌 *Jan 3: Market remains steady despite weather disruptions in Queensland*  
📰 Sources: [Mining.com](actual-article-url) | [Hellenic Shipping](actual-article-url)

**♻️ Scrap Steel**  
📌 *Jan 4: Turkish mills lift bids for import scrap*  
📌 *Jan 3: Seasonal restocking boosts import demand by $5/ton*  
📰 Sources: [Scrap Monster](actual-article-url) | [SteelOrbis](actual-article-url)

**Note**: In the actual dashboard, source links are fully clickable URLs to specific articles, not homepage links  

---

## 7. Data Sources (Freely Available & AI-Accessible) - Steel Sector Focus

### 🔹 Iron Ore
- [Reuters Commodities](https://www.reuters.com/business/commodities/)  
- [Trading Economics – Iron Ore](https://tradingeconomics.com/commodity/iron-ore)  
- [Mining.com – Iron Ore News](https://www.mining.com/commodity/iron-ore/)  

### 🔹 Coking Coal
- [Mining.com – Coal News](https://www.mining.com/commodity/coal/)  
- [Hellenic Shipping News](https://www.hellenicshippingnews.com/category/commodities/coal/)  

### 🔹 Scrap Steel
- [Scrap Monster](https://www.scrapmonster.com/)  
- [SteelOrbis](https://www.steelorbis.com/)  

### 🔹 Steel Products (Rebar, HRC)
- [Trading Economics – Steel](https://tradingeconomics.com/commodity/steel)  
- [SteelOrbis - Market Reports](https://www.steelorbis.com/)  

### 🔹 General Market Coverage
- [Investing.com – Commodities](https://www.investing.com/commodities/)  
- [XE Currency News](https://www.xe.com/news/)  

---

## 8. Technical Implementation

### Core Components
- **Base Platform**: SQL Dashboard with real-time MS SQL Server data
- **AI Integration**: Optional Perplexity AI layer for market intelligence
- **Z-Score Filtering**: Smart API optimization based on price volatility
- **Backend**: Python with modular architecture supporting feature flags
- **Frontend**: Unified Streamlit dashboard with progressive enhancement
- **Storage**: Shared MSSQL database for all data (prices, cache, AI results)

### JSON Query Structure
```json
{
    "commodity": "iron ore",
    "current_price": "USD 116/ton",
    "price_change": "+1.8%",
    "trend": "bullish",
    "key_drivers": ["China demand", "Supply disruption", "Vietnam growth"],
    "recent_news": ["Jan 4: Price rises on...", "Jan 3: Australia faces..."],
    "source_urls": [
        "https://www.reuters.com/markets/commodities/article-link",
        "https://tradingeconomics.com/commodity/iron-ore/news",
        "https://www.mining.com/specific-article-url"
    ]
}
```

**Key Feature**: Full URLs are provided for each source, allowing users to click through to the original articles for detailed follow-up.

### Unified Architecture
- **Integrated System**: AI features now default part of dashboard
- **Access Levels**: Read-only for cache, write access for new queries
- **Shared Infrastructure**: Single codebase, database, and UI framework
- **Intelligent Caching**: Three-tier cache (Memory → Database → API) for AI queries
- **Z-Score Threshold**: Only query commodities with significant price movements (|z-score| > 2)
- **Weekly News Aggregation**: Shows news from past 7 days for all commodities
- **Cost Optimization**: 80-90% API cost reduction through smart caching and z-score filtering

### Unified Data Flow

```
USER OPENS DASHBOARD
            ↓
1. LOAD SQL DATA (Always)
   → Fetch real-time prices from MSSQL
   → Calculate z-scores and indicators
   → Prepare base visualizations
            ↓
2. CHECK AI FEATURES (If ENABLE_AI_FEATURES=true)
   → Verify Perplexity API key exists
   → Initialize AI modules
   → Check cache status
            ↓
3. FETCH AI INTELLIGENCE (If enabled)
   → Calculate z-scores from weekly price changes
   → Memory cache check (~1ms)
   → Database cache check (including 7-day lookback)
   → Filter: Only query if |z-score| > threshold
   → Perplexity API call if needed (~2-5s per commodity)
   → Aggregate weekly news for all commodities
   → Store results in AI tables
            ↓
4. MERGE & DISPLAY
   → Combine SQL data with AI insights
   → Show enhanced metrics and trends
   → Display news cards with sources
   → Maintain responsive UI throughout
```

### Performance Characteristics

| Cache Level | Response Time | Use Case |
|------------|---------------|----------|
| Memory Cache | ~1ms | Same day, same session |
| Database Cache | 10-50ms | Within 7 days, any session |
| Perplexity API | 2-5s/commodity | High volatility (|z-score| > 2) |

### Z-Score Threshold Filtering

**How it works:**
1. Calculate z-scores from weekly price percentage changes
2. Only query Perplexity API for commodities with |z-score| > threshold (default: 2.0)
3. Show cached news (up to 7 days old) for stable commodities
4. Result: 80-90% reduction in API calls during normal market conditions

**Example Scenarios:**
- **Iron Ore**: +8% weekly change, z-score = 4.0 → **New API query**
- **Steel HRC**: +0.5% weekly change, z-score = 0.25 → **Use cached news**
- **Coking Coal**: -7% weekly change, z-score = -3.5 → **New API query**

**Benefits:**
- Focuses API usage on significant market movements
- All commodities still display news (from cache)
- Reduces costs while maintaining comprehensive coverage

### Cache Management

- **Memory Cache**: Cleared on app restart or date change
- **Session State**: Browser-specific, cleared on refresh
- **Database**: Persists 90 days (configurable in config.yaml)
- **Force Refresh**: Bypasses all caches for immediate updates

---

## 9. Expected Benefits
- **Unified Experience**: Single dashboard for all commodity intelligence needs
- **Cost Effective**: 80-90% API cost reduction through z-score filtering and intelligent caching
- **Smart Resource Usage**: API calls only for commodities with significant price movements
- **Weekly News Coverage**: All commodities show news from past 7 days regardless of volatility
- **Expanded Coverage**: Scaling from 5 steel commodities to 100+ across all sectors (in progress)
- **Vietnam-Focused**: Tailored insights for Vietnamese market dynamics
- **Source Transparency**: All AI insights come with cited sources for verification
- **Performance**: Sub-2s load times with intelligent caching
- **Sector Intelligence**: Specialized news sources for each commodity sector

---

## 10. Project Status

### Completed ✅
- **Unified Dashboard**: AI and SQL dashboards fully integrated
- **MSSQL Migration**: Shared database with AI tables (AI_Query_Cache, AI_Market_Intelligence, AI_News_Items)
- **Module Integration**: AI features integrated into `modules/ai_integration/`
- **3-Tier Caching**: Memory → Database → API cache system operational
- **UI Integration**: AI intelligence displayed alongside SQL data
- **Testing & Validation**: Core unified dashboard tested and operational

### Current Phase 🟡 (Sector Expansion - Increasing AI Capacity)
**Goal**: Expand from 5 steel commodities to 100+ commodities across all database sectors

#### In Progress:
- **Configuration Structure**: Creating `config/commodities.yaml` with sector mappings
- **Data Model Updates**: Extending commodity dataclass for natural language queries
- **Source Guidance System**: Mapping sectors to authoritative news sources
- **Dynamic Loading**: Replacing hardcoded commodities with configuration-driven approach

#### Key Tasks:
- Map Bloomberg tickers to natural language names for Perplexity queries
- Add sector-specific news sources (USDA for agriculture, EIA for energy, etc.)
- Implement query budget controls for API cost management
- Update UI for multi-sector commodity selection

---

## 11. Development

### Running the Unified Dashboard
```bash
# Development mode with auto-reload
streamlit run current/sql-dashboard/main.py --server.runOnSave=true

# With debug logging
LOG_LEVEL=DEBUG streamlit run current/sql-dashboard/main.py

# Test AI features without API calls
ENABLE_AI_FEATURES=true MOCK_API=true streamlit run current/sql-dashboard/main.py
```

### Testing
```bash
# Run test suite
pytest tests/

# Test AI integration specifically
pytest tests/test_ai_integration.py

# Test with coverage
pytest --cov=modules tests/
```

---
