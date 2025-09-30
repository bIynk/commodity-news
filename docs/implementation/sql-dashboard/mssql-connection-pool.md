# MS SQL Server Connection Pool

## Overview
The SQL dashboard uses pyodbc with connection pooling to efficiently manage database connections to Microsoft SQL Server containing 200+ commodity price records.

## Connection Management

### File Location
`current/sql-dashboard/modules/db_connection.py`

### Connection String
```python
# Environment variable
DC_DB_STRING="DRIVER={ODBC Driver 17 for SQL Server};SERVER=server_name;DATABASE=CommodityDB;UID=user;PWD=password"
```

### Connection Pool Implementation
```python
class DatabaseConnection:
    """Manages SQL Server connection pool"""

    def __init__(self, connection_string=None):
        self.connection_string = connection_string or os.getenv('DC_DB_STRING')
        self.pool = []
        self.pool_size = 5
        self.active_connections = 0

    def get_connection(self):
        """Get connection from pool or create new"""
        if self.pool:
            return self.pool.pop()

        if self.active_connections < self.pool_size:
            conn = pyodbc.connect(self.connection_string)
            self.active_connections += 1
            return conn

        # Wait for available connection
        return self._wait_for_connection()

    def return_connection(self, conn):
        """Return connection to pool"""
        if conn and not conn.closed:
            self.pool.append(conn)
```

## Query Execution

### Safe Query Wrapper
```python
def execute_query(query: str, params: List = None) -> pd.DataFrame:
    """Execute query with automatic connection management"""
    conn = None
    try:
        conn = db_pool.get_connection()
        df = pd.read_sql_query(query, conn, params=params)
        return df
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise
    finally:
        if conn:
            db_pool.return_connection(conn)
```

### Parameterized Queries
```python
def get_commodity_prices(commodity: str, start_date: str) -> pd.DataFrame:
    """Fetch prices with SQL injection protection"""
    query = """
        SELECT Date, Price, Ticker
        FROM Agricultural
        WHERE Ticker = ?
        AND Date >= ?
        ORDER BY Date DESC
    """
    return execute_query(query, [commodity, start_date])
```

## Connection Configuration

### Timeout Settings
```python
connection_config = {
    'timeout': 30,  # Connection timeout in seconds
    'login_timeout': 10,  # Login timeout
    'packet_size': 4096,  # Network packet size
    'autocommit': True,  # Auto-commit transactions
}
```

### Retry Logic
```python
@retry(attempts=3, delay=1, backoff=2)
def connect_with_retry():
    """Establish connection with exponential backoff"""
    try:
        return pyodbc.connect(connection_string, **connection_config)
    except pyodbc.Error as e:
        logger.warning(f"Connection attempt failed: {e}")
        raise
```

## Performance Optimization

### Connection Pooling Benefits
- Reduces connection overhead
- Improves response times
- Manages concurrent requests
- Prevents connection exhaustion

### Query Optimization
```python
def optimize_query(base_query: str) -> str:
    """Add query hints for performance"""
    optimizations = [
        "SET NOCOUNT ON",  # Reduce network traffic
        "SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED",  # Prevent locking
    ]
    return "; ".join(optimizations) + "; " + base_query
```

### Batch Operations
```python
def fetch_multiple_commodities(commodities: List[str]) -> pd.DataFrame:
    """Fetch multiple commodities in single query"""
    placeholders = ','.join(['?'] * len(commodities))
    query = f"""
        SELECT * FROM Agricultural
        WHERE Ticker IN ({placeholders})
        AND Date >= DATEADD(day, -30, GETDATE())
    """
    return execute_query(query, commodities)
```

## Error Handling

### Connection Errors
```python
class ConnectionErrorHandler:
    @staticmethod
    def handle_connection_error(error):
        """Categorize and handle connection errors"""
        error_code = error.args[0]

        if error_code == '08001':  # SQL Server does not exist
            return "Database server not found"
        elif error_code == '28000':  # Login failed
            return "Authentication failed"
        elif error_code == '08S01':  # Communication link failure
            return "Network connection lost"
        else:
            return f"Database error: {error}"
```

### Query Timeout Handling
```python
def execute_with_timeout(query: str, timeout: int = 30):
    """Execute query with timeout"""
    conn = db_pool.get_connection()
    conn.timeout = timeout

    try:
        cursor = conn.execute(query)
        return cursor.fetchall()
    except pyodbc.Error as e:
        if 'HYT00' in str(e):  # Timeout error code
            raise TimeoutError("Query execution timed out")
        raise
```

## Database Schema Access

### Table Discovery
```python
def get_available_tables() -> List[str]:
    """List all commodity tables"""
    query = """
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_TYPE = 'BASE TABLE'
        AND TABLE_NAME IN (
            'Agricultural', 'Chemicals', 'Energy',
            'Fertilizer', 'Livestock', 'Metals',
            'Shipping_Freight', 'Steel'
        )
    """
    return execute_query(query)['TABLE_NAME'].tolist()
```

### Column Information
```python
def get_table_schema(table_name: str) -> pd.DataFrame:
    """Get table column details"""
    query = """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ?
    """
    return execute_query(query, [table_name])
```

## Monitoring

### Connection Pool Metrics
```python
def get_pool_stats() -> Dict:
    """Monitor connection pool health"""
    return {
        'pool_size': db_pool.pool_size,
        'available_connections': len(db_pool.pool),
        'active_connections': db_pool.active_connections,
        'total_queries': db_pool.query_count,
        'failed_queries': db_pool.error_count
    }
```

### Query Performance Logging
```python
def log_slow_queries(query: str, execution_time: float):
    """Log queries exceeding threshold"""
    if execution_time > 1.0:  # 1 second threshold
        logger.warning(f"Slow query ({execution_time:.2f}s): {query[:100]}...")
```

## Testing

### Mock Connection
```python
class MockConnection:
    """Test database connection"""
    def execute(self, query):
        return MockCursor(test_data)

    def close(self):
        pass
```

### Connection String Validation
```python
def validate_connection_string(conn_str: str) -> bool:
    """Verify connection string format"""
    required_keys = ['DRIVER', 'SERVER', 'DATABASE']
    return all(key in conn_str for key in required_keys)
```

## Security Considerations

### Credential Management
- Never hardcode credentials
- Use environment variables
- Implement credential rotation
- Use Windows Authentication when possible

### SQL Injection Prevention
- Always use parameterized queries
- Validate input types
- Escape special characters
- Limit query permissions

## Related Documentation

- [Database Schema](../../architecture/database-design.md)
- [Query Builder](./query-builder.md)
- [Data Loader](./data-loader.md)