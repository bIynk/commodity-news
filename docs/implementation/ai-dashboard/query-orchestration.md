# Query Orchestration

## Overview
The query orchestration layer manages the flow of commodity data requests through the 3-tier caching system and coordinates API calls when fresh data is needed.

## Core Implementation

### Main File
`current/sql-dashboard/modules/ai_integration/commodity_queries.py`

### Key Functions

#### `get_commodity_data(commodity_name, timeframe, force_refresh)`
Primary entry point for commodity data retrieval.

**Flow:**
1. Check memory cache (session state)
2. Check database cache (SQLite)
3. Query Perplexity API if needed
4. Update all cache layers
5. Return processed data

#### `get_all_commodities(commodities_list, timeframe, force_refresh)`
Batch retrieval for multiple commodities.

**Optimization:**
- Parallel cache checks
- Batch API calls when possible
- Shared database connection
- Progress indication for UI

## Cache Key Generation

```python
def generate_cache_key(commodity: str, date: datetime) -> str:
    """Generate consistent cache key"""
    date_str = date.strftime("%Y-%m-%d")
    commodity_normalized = commodity.lower().replace(" ", "_")
    return f"{commodity_normalized}_{date_str}"
```

## Cache Check Logic

```python
def check_cache_validity(cached_data, current_date):
    """Determine if cached data is still valid"""
    if not cached_data:
        return False

    cache_date = cached_data.get('date')
    if cache_date != current_date:
        return False

    # Additional staleness checks
    if is_data_stale(cached_data):
        return False

    return True
```

## Force Refresh Modes

### 1. Normal Mode
- Full cache hierarchy check
- Returns cached data if valid
- Minimizes API calls

### 2. Force Refresh
- Skips all caches
- Direct API query
- Updates all cache layers

### 3. Clear Cache
- Removes all cached entries
- Resets memory state
- Triggers full refresh

## Database Operations

### Save Query Result
```python
def save_to_database(commodity, data, connection):
    """Persist API response to database"""
    query = """
        INSERT OR REPLACE INTO query_results
        (commodity, query_date, result_json, created_at)
        VALUES (?, ?, ?, ?)
    """
    connection.execute(query, [
        commodity,
        datetime.now().date(),
        json.dumps(data),
        datetime.now()
    ])
```

### Retrieve Cached Data
```python
def get_from_database(commodity, date, connection):
    """Fetch cached data from database"""
    query = """
        SELECT result_json
        FROM query_results
        WHERE commodity = ? AND query_date = ?
        ORDER BY created_at DESC
        LIMIT 1
    """
    result = connection.execute(query, [commodity, date]).fetchone()
    return json.loads(result[0]) if result else None
```

## Error Handling

### API Failure Fallback
```python
def handle_api_failure(commodity, error):
    """Graceful degradation on API failure"""
    # Try to return stale cached data
    stale_data = get_stale_cache(commodity)
    if stale_data:
        stale_data['warning'] = 'Using cached data due to API error'
        return stale_data

    # Return error response
    return create_error_response(commodity, error)
```

### Partial Success Handling
When fetching multiple commodities:
- Continue processing on individual failures
- Mark failed commodities
- Return partial results
- Log errors for debugging

## Performance Metrics

### Cache Hit Rates
```python
cache_metrics = {
    'memory_hits': 0,
    'database_hits': 0,
    'api_calls': 0,
    'cache_hit_rate': 0.0
}

def update_metrics(cache_level):
    """Track cache performance"""
    cache_metrics[cache_level] += 1
    calculate_hit_rate()
```

### Response Times
- Memory cache: < 1ms
- Database cache: 10-50ms
- API call: 2-5s per commodity

## Batch Processing

### Parallel Execution
```python
def batch_query_commodities(commodity_list):
    """Query multiple commodities efficiently"""
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(get_commodity_data, c): c
            for c in commodity_list
        }

        results = {}
        for future in as_completed(futures):
            commodity = futures[future]
            try:
                results[commodity] = future.result()
            except Exception as e:
                results[commodity] = handle_error(e)

        return results
```

## Configuration

### Timeouts and Retries
```yaml
query_settings:
  cache_timeout_hours: 24
  api_timeout_seconds: 30
  max_retries: 3
  retry_delay_seconds: 1
```

### Commodity List
```yaml
commodities:
  - name: "iron ore"
    query_keywords: ["iron ore 62% Fe", "Chinese ports"]
  - name: "coking coal"
    query_keywords: ["metallurgical coal", "Australia FOB"]
```

## Monitoring and Logging

### Query Logging
```python
logger.info(f"Query initiated: {commodity} - {timeframe}")
logger.debug(f"Cache key: {cache_key}")
logger.info(f"Cache hit: {cache_level}")
logger.warning(f"API error for {commodity}: {error}")
```

### Performance Tracking
- Query count per commodity
- Average response times
- Cache hit/miss ratios
- Error frequency

## Z-Score Filtering and Display Logic (January 2025 Update)

### Overview
The system uses z-scores to determine which commodities warrant fresh AI API queries, while ALWAYS displaying ALL available cached data from the past 7 days regardless of current z-scores.

### Z-Score Calculation
```python
# Uses compute_frequency_aware_zscore for accurate volatility measurement
zscore_df = compute_frequency_aware_zscore(
    price_series,
    lookback=90,  # 90 days for frequency detection
    window=30     # 30 periods for rolling statistics
)
```

### Commodity Display Logic (Updated January 22, 2025)

#### ALL Commodities ARE Displayed When:
1. **Any Cached Data Exists** (past 7 days) - regardless of current z-score
   - Includes full query cache from `AI_Query_Cache` table
   - Includes historical market intelligence from `AI_Market_Intelligence` table
   - Includes news items from `AI_News_Items` table
2. **High Volatility Today**: |z-score| > threshold (default 2.0) - triggers fresh AI query

#### API Queries Only Happen When:
1. **High z-score** (|z-score| > 2.0) AND
2. **No recent cache available** (nothing in past 7 days)

### Implementation Details

#### New Data Flow in `query_all_commodities()`:
```python
# Step 1: Check memory cache (if same day and not force_refresh)

# Step 2: ALWAYS get ALL cached data from the past 7 days
for commodity in commodities_to_process:
    # Check for recent full cache (AI_Query_Cache)
    cached_result = self.database.get_today_results(commodity.name, timeframe)

    if cached_result:
        # Use complete cached data
        results.append(cached_result)
    else:
        # No recent cache - check for historical intelligence and news
        weekly_news = self.database.get_weekly_news(commodity.name, days=7)
        historical_intelligence = self.database.get_historical_market_intelligence(commodity.name, days=7)

        if weekly_news or historical_intelligence:
            # Create result from historical data with REAL values (not placeholders)
            results.append({
                'data': {
                    'trend': historical_intelligence.get('trend', 'unknown'),  # Real trend
                    'key_drivers': historical_intelligence.get('key_drivers', []),  # Real drivers
                    'current_price': historical_intelligence.get('current_price', 'N/A'),
                    'market_news': news_items,
                    # ... other fields
                }
            })

# Step 3: Only query API for high z-score items WITHOUT cache
if commodity_zscores and abs(zscore) <= threshold:
    # Low z-score - do NOT query API (but still displayed if cache exists)
    continue
```

#### New Method in `ai_database.py`:
```python
def get_historical_market_intelligence(self, commodity: str, days: int = 7) -> Optional[Dict]:
    """
    Get the most recent market intelligence data from the past week.
    Returns trend, key_drivers, price data from AI_Market_Intelligence table.
    """
    query = """
    SELECT TOP 1
        Current_Price,
        Price_Change_Pct,
        Trend,
        Key_Drivers,
        Price_Outlook,
        Analysis_Date
    FROM AI_Market_Intelligence
    WHERE Commodity = :commodity
      AND Analysis_Date >= :cutoff_date
    ORDER BY Analysis_Date DESC
    """
```

### Key Changes from Previous Version

#### Before (Problem):
- Low z-score commodities with no TODAY's cache were skipped entirely
- Displayed "❓ Historical" and "Historical data only" placeholders
- Lost visibility of valuable cached data from past week

#### After (Fixed):
- ALL commodities with ANY cached data (7 days) are displayed
- Shows REAL cached trends and drivers, not placeholders
- Z-score only gates NEW API calls, not display

### Rationale
- **Complete Visibility**: Users see ALL available market intelligence from the past week
- **Cost Efficiency**: Still reduces API calls by ~80% through z-score filtering
- **Data Integrity**: Displays actual cached values instead of misleading placeholders
- **Better UX**: No missing commodities that have recent historical data

### Configuration
```python
# Environment Variables
AI_ZSCORE_THRESHOLD = 2.0  # Minimum |z-score| for NEW API queries only

# Cache lookback period
CACHE_LOOKBACK_DAYS = 7  # Display any data from past 7 days
```

## Query Date Tracking and Display (January 2025 Update)

### Overview
The system now tracks and displays the actual date when each commodity's Perplexity AI query was performed, providing transparency about data freshness.

### Implementation Components

#### Database Schema
The `Query_Date` field in `AI_Query_Cache` table stores when each query was executed:
- Populated when saving new Perplexity API responses
- Retrieved with all cached queries for display
- Used to show data age to users

#### Data Flow for Query_Date

1. **Fresh Queries** (from Perplexity API):
   ```python
   # In commodity_queries.py - _query_commodity_with_context()
   result["cache_date"] = datetime.now().date().isoformat()
   ```

2. **Cached Results** (from database):
   ```python
   # In ai_database.py - get_today_results()
   SELECT Query_Response, Created_At, Query_Date FROM AI_Query_Cache
   # Returns with:
   "cache_date": row['Query_Date'].isoformat()
   ```

3. **Historical Data** (from AI_Market_Intelligence):
   ```python
   # Uses Analysis_Date from historical intelligence
   "cache_date": historical_intelligence.get('analysis_date')
   ```

### Display Integration

#### AI Table - "Date Flagged" Column
Shows when the AI analysis was performed:
```python
# In data_processor.py - _format_table_row()
query_date = result.get("cache_date") or result.get("query_date") or ""
# Formats as YYYY-MM-DD for display
return {
    "Date flagged": query_date  # New column
}
```

Column configuration in `ai_section.py`:
```python
display_columns = ['Commodity', 'Trend', 'Price change', 'Key Drivers', 'Date flagged']
```

#### News Cards - "Updated" Date
Displays the query date instead of today's date:
```python
# In data_processor.py - _format_news_card()
timestamp = result.get("cache_date") or result.get("timestamp", datetime.utcnow().isoformat())
```

### Key Benefits
- **Transparency**: Users see exactly when each analysis was performed
- **Trust**: No misleading "updated today" for older cached data
- **Monitoring**: Easy to identify stale data that needs refresh

### Data Preservation Through Pipeline
The `cache_date` field is preserved through all processing steps:
1. Database queries include `Query_Date` in SELECT statements
2. `aggregate_weekly_news()` preserves all top-level fields including `cache_date`
3. All code paths (cached, fresh, historical) populate `cache_date`

### Configuration
No additional configuration needed - Query_Date tracking is automatic for all AI queries.

## Testing

### Mock Orchestration
```python
@pytest.fixture
def mock_orchestrator():
    """Test orchestrator with mock data"""
    orchestrator = QueryOrchestrator()
    orchestrator.api_client = MockPerplexityClient()
    orchestrator.database = MockDatabase()
    return orchestrator
```

### Test Scenarios
1. Cache hit flow
2. Cache miss → API call
3. Force refresh behavior
4. Error handling
5. Batch processing
6. Z-score filtering behavior
7. Skipped commodity handling
8. Query date preservation through cache layers

## Related Documentation

- [Perplexity Integration](./perplexity-integration.md)
- [Caching Architecture](../../architecture/caching-architecture.md)
- [Database Operations](../../architecture/database-design.md)
- [Z-Score Calculation](../sql-dashboard/zscore-calculation.md)