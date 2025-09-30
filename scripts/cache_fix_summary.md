# Cache Fix: Preventing Redundant API Queries

## Problem
The system was using `datetime.now().date()` as the cache key, causing redundant API queries when:
- Data last updated: Sept 19
- Current date: Sept 22
- Cache lookup searched for Sept 22 entries but data was from Sept 19
- Result: Cache miss → unnecessary API query

## Solution
Modified the caching logic to use the **data's last updated date** instead of the current date.

### Files Modified

1. **commodity_queries.py**
   - Added `data_last_updated` parameter to `query_all_commodities()`
   - Uses data date for cache key instead of current date
   - Updates cache lookups to use `get_cached_result_by_date()`

2. **ai_database.py**
   - Added `query_date` parameter to `save_query_results()`
   - Created new `get_cached_result_by_date()` method
   - Cache entries now keyed by data date, not query date

3. **main.py**
   - Extracts `data_last_updated` from the latest_date in commodity data
   - Passes this date to the AI orchestrator

## Benefits
- **No redundant queries**: If data hasn't updated since Sept 19, queries on Sept 22 will find and use the Sept 19 cache
- **Cost savings**: Prevents unnecessary Perplexity API calls when data is stale
- **Better alignment**: Cache lifecycle matches data lifecycle

## How It Works

### Before (Problem)
```python
# Sept 22: Checking cache
query_date = datetime.now().date()  # Sept 22
# Searches for: commodity='X', query_date='Sept 22'
# Cache has: commodity='X', query_date='Sept 19'
# Result: MISS → API Query
```

### After (Fixed)
```python
# Sept 22: Checking cache
query_date = data_last_updated.date()  # Sept 19 (from data)
# Searches for: commodity='X', query_date='Sept 19'
# Cache has: commodity='X', query_date='Sept 19'
# Result: HIT → No API Query
```

## Testing
Run `python scripts/test_cache_fix.py` to verify the fix behavior.