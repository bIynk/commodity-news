# Caching Architecture

## Overview
The system implements a three-tier caching strategy combined with z-score threshold filtering to minimize API costs while maintaining data freshness. This architecture reduces API calls by approximately 80-90% through intelligent daily caching and volatility-based filtering.

## Three-Tier Cache Hierarchy

### Tier 1: Memory Cache (~1ms)
- **Location**: Python session state (Streamlit)
- **Scope**: Per-session, per-browser
- **Duration**: Until app restart or date change
- **Use Case**: Same-day, same-session repeated requests

### Tier 2: Database Cache (~10-50ms)
- **Location**: MS SQL Server (shared with SQL dashboard)
- **Scope**: Application-wide, persistent
- **Duration**: 7-day lookback for news, 90 days retention
- **Use Case**: Recent requests across sessions/restarts

### Tier 3: Perplexity API (~2-5s per commodity)
- **Location**: External API
- **Scope**: Fresh data source
- **Duration**: N/A (source of truth)
- **Use Case**: First query of the day per commodity

## Detailed Data Flow

```
USER ACTION (Get Today's Data / Force Refresh)
            ↓
1. CALCULATE Z-SCORES
   → Extract weekly % changes from SQL data
   → Compute z-scores for volatility assessment
            ↓
2. CHECK MEMORY CACHE (~1ms)
   → If found & valid: Return immediately
            ↓
3. CHECK DATABASE CACHE (~10-50ms)
   → Look back up to 7 days for cached results
   → If found: Load & update memory cache
            ↓
4. APPLY Z-SCORE FILTER
   → If |z-score| ≤ threshold (default: 2.0): Skip API query
   → Use cached news from past week if available
            ↓
5. QUERY PERPLEXITY AI (~2-5s per commodity)
   → Only for commodities with |z-score| > threshold
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

## Performance Characteristics

| Cache Level | Response Time | Use Case |
|------------|---------------|----------|
| Memory Cache | ~1ms | Same day, same session |
| Database Cache | 10-50ms | Within 7 days, any session |
| Z-Score Filter | ~0ms | Skip API for stable commodities |
| Perplexity API | 2-5s/commodity | High volatility (|z-score| > 2) |

## Cache Management

### Cache Invalidation
- **Memory Cache**: Cleared on app restart or date change
- **Session State**: Browser-specific, cleared on refresh
- **Database**: Persists 90 days (configurable in config.yaml)
- **Force Refresh**: Bypasses all caches for immediate updates

### Intelligent Caching Strategy
- **Z-score filtering**: Only query commodities with significant price movements
- **Weekly lookback**: Database cache checks past 7 days
- **Three-tier cache**: Memory → Database → Perplexity AI
- **80-90% cost reduction**: Z-score filter + daily caching
- **Weekly news aggregation**: All commodities show news from past week
- **Force refresh option**: Available when immediate updates needed

## Implementation Details

### Cache Key Structure
```python
cache_key = f"{commodity_name}_{date_string}"
```

### Database Schema (MS SQL Server)
```sql
CREATE TABLE AI_Query_Cache (
    Cache_ID INT PRIMARY KEY IDENTITY(1,1),
    Commodity NVARCHAR(100),
    Query_Date DATE,
    Timeframe NVARCHAR(20),
    Query_Response NVARCHAR(MAX),
    Created_At DATETIME DEFAULT GETDATE(),
    Expires_At DATETIME,
    Cache_Hit_Count INT DEFAULT 0
);

CREATE INDEX idx_commodity_date ON AI_Query_Cache(Commodity, Query_Date);
CREATE INDEX idx_expires ON AI_Query_Cache(Expires_At);
```

### Memory Cache Implementation
```python
# Streamlit session state
if 'cache' not in st.session_state:
    st.session_state.cache = {}

# Cache check
if cache_key in st.session_state.cache:
    return st.session_state.cache[cache_key]
```

## Cache Configuration

From `config.yaml` and environment:
```yaml
# config.yaml
api:
  zscore_threshold: 2.0  # Only query if |z-score| > threshold

dashboard:
  cache_duration_minutes: 60
  auto_refresh_minutes: 30
  enable_zscore_filtering: true

database:
  cleanup_days: 90  # Days of data to retain
  news_lookback_days: 7  # Days to look back for cached news
```

```bash
# Environment variables
AI_ZSCORE_THRESHOLD=2.0  # Override config value
```

## Cache Modes

1. **Normal Mode**: Full 3-tier cache check
2. **Force Refresh**: Skip all caches, query API directly
3. **Clear Cache**: Remove all cached data and refresh

## Benefits

- **80-90% API Cost Reduction**: Z-score filtering + intelligent caching
- **Smart Resource Usage**: API calls only for volatile commodities
- **Complete Coverage**: All commodities show news (from cache if stable)
- **Sub-second Response**: Memory cache provides instant results
- **Resilience**: Database cache survives restarts with 7-day lookback
- **Flexibility**: Force refresh for critical updates
- **Scalability**: Strategy scales to 100+ commodities

## Multi-Day Query Scenarios

### Scenario 1: High Volatility Monday, Low Tuesday
**Monday:**
- Iron Ore: +8% weekly change, z-score = 4.0
- Action: Query Perplexity API, cache result
- Display: Fresh news with "2025-01-20" dates

**Tuesday:**
- Iron Ore: +0.5% change from Monday, z-score = 0.25
- Action: Skip API (below threshold), use Monday's cache
- Display: Monday's news with "2025-01-20" dates

### Scenario 2: No Query for a Week, Then Spike
**Previous Week:**
- Steel HRC: Stable, no queries made
- Cache: Empty

**Today:**
- Steel HRC: +10% weekly change, z-score = 5.0
- Action: Query Perplexity API
- Display: Fresh news with current dates

### Scenario 3: Mixed Cache Ages
**Result:**
- Iron Ore: Cached 3 days ago (below threshold today)
- Coking Coal: Fresh query today (above threshold)
- Scrap Steel: Cached yesterday (below threshold)
- Display: All show news with appropriate dates in YYYY-MM-DD format

### Scenario 4: Force Refresh Override
**Normal:**
- Commodity below threshold → Use cache

**Force Refresh:**
- User clicks "Refresh AI" button
- Action: Query ALL commodities regardless of z-score
- Use Case: Breaking news event, manual override needed

## Z-Score Calculation Example

```python
# Weekly price change to z-score
weekly_change_pct = 0.04  # 4% change
typical_weekly_volatility = 0.02  # 2% typical volatility

z_score = weekly_change_pct / typical_weekly_volatility
# z_score = 2.0 (exactly at threshold)

if abs(z_score) > threshold:  # threshold = 2.0
    # Query API
else:
    # Use cache
```

## Related Documentation

- [System Overview](./system-overview.md)
- [Database Design](./database-design.md)
- [API Integration](../api-reference/perplexity-api.md)
- [Z-Score Implementation](../implementation/zscore-threshold-expansion-plan.md)