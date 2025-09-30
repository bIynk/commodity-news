# Debugging Guide

## Common Issues and Solutions

### 1. Perplexity API Issues

#### Authentication Failures
```python
# Check API key is loaded
import os
print(f"API Key present: {bool(os.getenv('PERPLEXITY_API_KEY'))}")
print(f"Key length: {len(os.getenv('PERPLEXITY_API_KEY', ''))}")

# Test API connection
from current.ai_dashboard.src.api.perplexity_client import PerplexityClient
client = PerplexityClient()
response = client.test_connection()
```

#### Rate Limiting (429 Errors)
```python
# Check rate limit status
from current.ai_dashboard.src.utils.rate_limiter import get_perplexity_rate_limiter
limiter = get_perplexity_rate_limiter()
print(f"Remaining tokens: {limiter.tokens}")
print(f"Reset time: {limiter.next_reset}")
```

#### JSON Parsing Errors
```python
# Enable debug logging for API responses
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('perplexity_client')

# Log raw responses
def debug_response(response_text):
    print("Raw response:")
    print(response_text[:500])  # First 500 chars
    try:
        import json
        parsed = json.loads(response_text)
        print("Successfully parsed JSON")
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
```

### 2. Database Connection Issues

#### SQL Server Connection Failures
```bash
# Test ODBC driver installation
odbcinst -q -d

# Test connection string
python -c "
import pyodbc
import os
conn_str = os.getenv('DC_DB_STRING')
print(f'Testing: {conn_str[:50]}...')
try:
    conn = pyodbc.connect(conn_str)
    print('Success!')
except Exception as e:
    print(f'Failed: {e}')
"
```

#### SQLite Lock Issues
```python
# Check for locks
import sqlite3
import time

def check_sqlite_locks():
    conn = sqlite3.connect('data/commodity_data.db')
    cursor = conn.cursor()

    # Check pragma
    cursor.execute("PRAGMA journal_mode")
    print(f"Journal mode: {cursor.fetchone()}")

    # Try exclusive lock
    try:
        cursor.execute("BEGIN EXCLUSIVE")
        print("Got exclusive lock")
        cursor.execute("COMMIT")
    except sqlite3.OperationalError as e:
        print(f"Database locked: {e}")
```

### 3. Streamlit Issues

#### Session State Debugging
```python
# Add to dashboard for debugging
import streamlit as st

if st.checkbox("Show Debug Info"):
    st.write("Session State:")
    st.json(dict(st.session_state))

    st.write("Cache Status:")
    if 'cache' in st.session_state:
        st.write(f"Cached items: {len(st.session_state.cache)}")
        st.write(f"Cache keys: {list(st.session_state.cache.keys())}")
```

#### Memory Issues
```bash
# Clear Streamlit cache
streamlit cache clear

# Monitor memory usage
python -c "
import psutil
import os
process = psutil.Process(os.getpid())
print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB')
"
```

### 4. Cache Debugging

#### Inspect Cache Contents
```python
def debug_cache():
    """Inspect all cache levels"""

    # Memory cache
    import streamlit as st
    if 'cache' in st.session_state:
        print(f"Memory cache entries: {list(st.session_state.cache.keys())}")

    # Database cache
    import sqlite3
    conn = sqlite3.connect('data/commodity_data.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT commodity, query_date, created_at
        FROM query_results
        ORDER BY created_at DESC
        LIMIT 10
    """)

    print("Recent cache entries:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} (created {row[2]})")
```

#### Force Cache Clear
```python
def clear_all_caches():
    """Clear all cache levels"""

    # Clear memory cache
    import streamlit as st
    if 'cache' in st.session_state:
        st.session_state.cache = {}

    # Clear database cache
    import sqlite3
    conn = sqlite3.connect('data/commodity_data.db')
    conn.execute("DELETE FROM query_results")
    conn.commit()

    print("All caches cleared")
```

## Debug Logging Configuration

### Enable Detailed Logging
```python
# In main.py or debug script
import logging

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

# Module-specific loggers
logging.getLogger('perplexity_client').setLevel(logging.DEBUG)
logging.getLogger('database').setLevel(logging.DEBUG)
logging.getLogger('streamlit').setLevel(logging.WARNING)
```

### Log Analysis Tools
```bash
# Find errors in logs
grep ERROR logs/commodity_dashboard.log

# Count errors by type
grep ERROR logs/commodity_dashboard.log | cut -d'-' -f4 | sort | uniq -c

# Monitor logs in real-time
tail -f logs/commodity_dashboard.log | grep -E "ERROR|WARNING"
```

## Performance Profiling

### Function Timing
```python
import time
from functools import wraps

def timer_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        end = time.perf_counter()
        print(f"{func.__name__} took {end - start:.4f} seconds")
        return result
    return wrapper

# Usage
@timer_decorator
def slow_function():
    time.sleep(1)
```

### Memory Profiling
```python
from memory_profiler import profile

@profile
def memory_intensive_function():
    large_list = [i for i in range(1000000)]
    return sum(large_list)

# Run with: python -m memory_profiler script.py
```

### Query Performance
```python
import time
import pandas as pd

def profile_query(query: str, params=None):
    """Profile database query performance"""

    start = time.perf_counter()
    df = pd.read_sql_query(query, conn, params=params)
    end = time.perf_counter()

    print(f"Query time: {end - start:.4f}s")
    print(f"Rows returned: {len(df)}")
    print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")

    return df
```

## Interactive Debugging

### Using pdb
```python
import pdb

def problematic_function(data):
    # Set breakpoint
    pdb.set_trace()

    # Or use breakpoint() in Python 3.7+
    breakpoint()

    result = process_data(data)
    return result
```

### IPython for Interactive Debugging
```python
# Install: pip install ipython

from IPython import embed

def debug_context():
    data = load_data()
    processed = process_data(data)

    # Drop into IPython shell with local context
    embed()

    return processed
```

## Remote Debugging (VS Code)

### Setup Remote Debugging
```python
# In your code
import debugpy

# Allow debugger to attach
debugpy.listen(5678)
print("Waiting for debugger...")
debugpy.wait_for_client()
```

### VS Code Configuration
```json
{
    "name": "Python: Remote Attach",
    "type": "python",
    "request": "attach",
    "connect": {
        "host": "localhost",
        "port": 5678
    }
}
```

## Common Error Messages

### SSL Certificate Errors
```
Error: SSL: CERTIFICATE_VERIFY_FAILED
Solution:
1. Update certificates: pip install --upgrade certifi
2. Set environment: export SSL_CERT_FILE=$(python -m certifi)
3. Temporary workaround: verify=False (dev only)
```

### Import Errors
```
Error: ModuleNotFoundError: No module named 'src'
Solution:
1. Check Python path: sys.path
2. Add to path: sys.path.append(os.path.dirname(__file__))
3. Use relative imports: from ..src import module
```

### Database Timeout
```
Error: OperationalError: database is locked
Solution:
1. Check for long-running transactions
2. Increase timeout: conn.execute("PRAGMA busy_timeout = 10000")
3. Use WAL mode: conn.execute("PRAGMA journal_mode = WAL")
```

## Debug Checklist

When debugging an issue:

1. **Reproduce the issue**
   - [ ] Can you reproduce it consistently?
   - [ ] What are the exact steps?
   - [ ] What's the expected vs actual behavior?

2. **Gather information**
   - [ ] Check logs for errors
   - [ ] Note the timestamp of the issue
   - [ ] Check system resources (memory, CPU)
   - [ ] Verify environment variables

3. **Isolate the problem**
   - [ ] Test individual components
   - [ ] Use minimal reproducible example
   - [ ] Check recent code changes

4. **Fix and verify**
   - [ ] Apply fix
   - [ ] Test the fix
   - [ ] Check for side effects
   - [ ] Document the solution

## Related Documentation

- [Setup Dev Environment](./setup-dev-environment.md)
- [Testing Strategy](./testing-strategy.md)
- [Performance Profiling](./performance-profiling.md)