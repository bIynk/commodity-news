## 1. Introduction
The Vietnamese steel market is highly influenced by movements in global and regional commodity prices and demand trends. Staying ahead requires continuous monitoring of market-moving news across key commodities and macroeconomic drivers.  

This project builds an **AI-powered dashboard** that combines a **structured summary** (top-level view of commodity movements and drivers) with **recent news snippets** (short articles with sources), modeled after tools like Perplexity AI.  

The system leverages **freely available web data sources** and uses Perplexity AI to retrieve, summarize, and present relevant insights with an intelligent **daily caching system** to minimize API costs.

### Quick Start
```bash
# Install dependencies
pip install -r requirements.txt

# Set up API key
cp .env.example .env
# Edit .env and add your Perplexity API key

# Run dashboard
streamlit run app.py
```

> ⚠️ **SSL Certificate Warning**: The current code has SSL verification temporarily disabled for testing. See [CLAUDE.md](CLAUDE.md#-ssl-certificate-hotfix-remove-for-production) for details on removing this before production deployment.

### Documentation
- **Setup Guide**: See [SETUP.md](SETUP.md) for detailed installation
- **Technical Docs**: See [CLAUDE.md](CLAUDE.md) for architecture details  

---

## 2. Objectives
- Provide a **daily, AI-curated structured summary** of key steel-related commodities.  
- Present **short recent news articles with cited sources** for deeper context.  
- Ensure all sources are **freely accessible** for AI retrieval.  
- Focus specifically on commodities most relevant to the **Vietnamese steel sector**.  

---

## 3. System Architecture

### Core Components
1. **Commodity Selection** – Track 5 key steel sector commodities (iron ore, coking coal, scrap steel, rebar, HRC)  
2. **AI Query with JSON** – Send structured query to Perplexity AI requesting JSON response  
3. **Smart Caching** – Daily cache system (Memory → Database → API)  
4. **Dashboard Display**  
   - **Structured Summary**: Table with prices, changes, drivers, trends  
   - **Recent Developments**: News cards with dated events and sources

### Component Interaction
```
┌─────────────┐       ┌──────────────┐       ┌──────────────┐
│  Streamlit  │ ───── │ Orchestrator │ ───── │ Perplexity   │
│  Dashboard  │       │   (Caching)  │       │     API      │
└─────────────┘       └──────────────┘       └──────────────┘
       │                     │                       ↑
       │                     ↓                       │
┌─────────────┐       ┌──────────────┐              │
│    Data     │       │   SQLite     │ ─────────────┘
│  Processor  │ ───── │   Database   │  (Only if no cache)
└─────────────┘       └──────────────┘
```

### Key Files
- `app.py` - Streamlit dashboard interface
- `src/api/perplexity_client.py` - API communication with JSON parsing
- `src/api/commodity_queries.py` - Query orchestration with 3-tier caching
- `src/processing/data_processor.py` - Formats JSON data for display
- `src/storage/database.py` - SQLite persistence layer  

---

## 4. Workflow
1. **Define Commodity Watchlist**  
   - Steel focus: Iron ore, coking coal, scrap steel, steel rebar, HRC  
2. **Daily JSON Query to Perplexity AI**  
   - Request: Price, change, drivers, news, sources in structured JSON  
   - Example: *"Summarize iron ore market from last week with price changes and key drivers"*  
3. **Intelligent Caching**  
   - Check daily cache before making API calls  
   - Store results in SQLite for persistence  
4. **Dashboard Rendering**  
   - **Top section:** Summary table with all commodities  
   - **Bottom section:** News cards with recent developments  

---

## 5. Dashboard Layout

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

## 6. Data Sources (Freely Available & AI-Accessible) - Steel Sector Focus

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

## 7. Technical Implementation

### Core Components
- **AI Agent**: Perplexity AI with JSON-structured responses
- **Query Format**: Single comprehensive query for price, news, and drivers
- **Backend**: Python with daily caching system to minimize API calls
- **Frontend**: Streamlit dashboard with table and news cards
- **Storage**: SQLite database for persistent daily cache

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

### Daily Caching Strategy
- **Once-per-day queries**: Each commodity queried maximum once daily
- **Three-tier cache**: Memory → Database → Perplexity AI
- **90% cost reduction**: Single JSON query + daily caching
- **Force refresh option**: Available when immediate updates needed

### Detailed Data Flow

```
USER ACTION (Get Today's Data / Force Refresh)
            ↓
1. CHECK MEMORY CACHE (~1ms)
   → If found & valid: Return immediately
            ↓
2. CHECK DATABASE CACHE (~10-50ms)
   → If today's data exists: Load & update memory cache
            ↓
3. QUERY PERPLEXITY AI (~2-5s per commodity)
   → Build JSON query with timeframe & commodity context
   → Send comprehensive request for price + news + drivers
   → Parse JSON response (with fallback to text parsing)
            ↓
4. SAVE TO DATABASE
   → Store in query_results table
   → Update price_history for trends
   → Cache for future requests
            ↓
5. PROCESS & FORMAT DATA
   → Format table rows: Price/Change, Drivers, Trend
   → Extract domain names from URLs for table display
   → Create news cards with dated events
   → Apply visual indicators (↑↓ 📈📉)
            ↓
6. RENDER DASHBOARD
   → Display metrics (bullish/bearish counts)
   → Show summary table with clean source names
   → Present news cards with clickable source links
   → Links open in new tabs for article follow-up
```

### Performance Characteristics

| Cache Level | Response Time | Use Case |
|------------|---------------|----------|
| Memory Cache | ~1ms | Same day, same session |
| Database Cache | 10-50ms | Same day, new session/restart |
| Perplexity API | 2-5s/commodity | First query of the day |

### Cache Management

- **Memory Cache**: Cleared on app restart or date change
- **Session State**: Browser-specific, cleared on refresh
- **Database**: Persists 90 days (configurable in config.yaml)
- **Force Refresh**: Bypasses all caches for immediate updates

---

## 8. Expected Benefits
- Daily, **up-to-date market intelligence** without relying on expensive subscriptions.  
- **Steel-focused, commodity-linked view** tailored to Vietnam’s market dynamics.  
- Efficient **information triage** (structured summary + expandable news).  
- Fully **source-cited** to ensure reliability.  


