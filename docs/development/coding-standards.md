# Coding Standards

## Python Style Guide

### General Principles
- **Clarity over cleverness** - Code should be immediately understandable
- **Explicit over implicit** - Be explicit about intentions and behavior
- **Fail fast** - Throw errors early, no silent failures
- **Type safety** - Always use type hints, never use `Any`

### Code Formatting

#### PEP 8 Compliance
- Follow PEP 8 with these modifications:
  - Line length: 120 characters (not 80)
  - Use Black formatter for consistency

#### Import Organization
```python
# Standard library imports
import os
import sys
from datetime import datetime

# Third-party imports
import pandas as pd
import numpy as np
from sqlalchemy import create_engine

# Local application imports
from src.api.client import APIClient
from src.utils.helpers import format_data
```

### Type Annotations

#### Always Required
```python
# Good
def calculate_zscore(value: float, mean: float, std: float) -> float:
    return (value - mean) / std

# Bad
def calculate_zscore(value, mean, std):
    return (value - mean) / std
```

#### Complex Types
```python
from typing import Dict, List, Optional, Union, Tuple

def query_commodity(
    commodity: str,
    timeframe: str,
    options: Optional[Dict[str, Any]] = None
) -> Union[Dict[str, Any], None]:
    ...
```

### Error Handling

#### Fail Fast Principle
```python
# Good - Fail immediately
def process_data(data: pd.DataFrame) -> pd.DataFrame:
    if data.empty:
        raise ValueError("Cannot process empty dataframe")

    if 'Price' not in data.columns:
        raise KeyError("Required column 'Price' not found")

    return data.copy()

# Bad - Silent failure
def process_data(data):
    try:
        return data.copy()
    except:
        return pd.DataFrame()  # Never do this
```

#### Specific Exception Handling
```python
# Good
try:
    conn = pyodbc.connect(connection_string)
except pyodbc.OperationalError as e:
    logger.error(f"Database connection failed: {e}")
    raise DatabaseConnectionError(f"Cannot connect to database: {e}")

# Bad
try:
    conn = pyodbc.connect(connection_string)
except Exception:
    pass  # Never catch all and ignore
```

### Function Design

#### Single Responsibility
```python
# Good - Each function does one thing
def fetch_data(commodity: str) -> pd.DataFrame:
    """Fetch raw data from database"""
    ...

def calculate_statistics(data: pd.DataFrame) -> Dict[str, float]:
    """Calculate statistical metrics"""
    ...

def format_for_display(stats: Dict[str, float]) -> str:
    """Format statistics for UI display"""
    ...

# Bad - Function does too much
def process_commodity(commodity: str) -> str:
    """Fetch, process, calculate, and format"""
    data = fetch_from_db(commodity)
    stats = calculate_stats(data)
    formatted = format_output(stats)
    send_email(formatted)
    return formatted
```

#### Pure Functions Preferred
```python
# Good - Pure function
def add_percentage(value: float, percentage: float) -> float:
    return value * (1 + percentage / 100)

# Less ideal - Side effects
def update_price(commodity: str, percentage: float) -> None:
    global price_dict  # Avoid global state
    price_dict[commodity] *= (1 + percentage / 100)
```

### Class Design

#### Dependency Injection
```python
# Good - Dependencies injected
class CommodityAnalyzer:
    def __init__(self, db_client: DatabaseClient, cache: CacheManager):
        self.db_client = db_client
        self.cache = cache

# Bad - Creates own dependencies
class CommodityAnalyzer:
    def __init__(self):
        self.db_client = DatabaseClient()  # Hard to test
        self.cache = CacheManager()
```

#### Property Usage
```python
class Commodity:
    def __init__(self, name: str, price: float):
        self._name = name
        self._price = price

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        if value < 0:
            raise ValueError("Price cannot be negative")
        self._price = value
```

### Documentation

#### Docstring Format (Google Style)
```python
def calculate_moving_average(
    prices: pd.Series,
    window: int = 30
) -> pd.Series:
    """Calculate moving average for price series.

    Args:
        prices: Series of commodity prices
        window: Number of periods for moving average

    Returns:
        Series with moving average values

    Raises:
        ValueError: If window size exceeds data length

    Example:
        >>> prices = pd.Series([100, 102, 98, 101])
        >>> ma = calculate_moving_average(prices, window=2)
    """
    if len(prices) < window:
        raise ValueError(f"Need at least {window} data points")
    return prices.rolling(window=window).mean()
```

#### Inline Comments
```python
# Use sparingly, only for non-obvious logic
zscore = (value - mean) / std  # No comment needed

# Complex business logic needs explanation
if days_old > 7 and frequency == 'daily':
    # Apply staleness filter per business requirement:
    # Daily data older than 7 days is considered stale
    return None
```

### Testing

#### Test Naming Convention
```python
def test_calculate_zscore_with_valid_input():
    """Test Z-score calculation with normal values"""
    ...

def test_calculate_zscore_raises_on_zero_std():
    """Test that zero standard deviation raises ValueError"""
    ...
```

#### Test Structure (AAA Pattern)
```python
def test_commodity_query():
    # Arrange
    commodity = "iron ore"
    timeframe = "1 week"
    client = MockPerplexityClient()

    # Act
    result = client.query_commodity(commodity, timeframe)

    # Assert
    assert result["commodity"] == commodity
    assert "price" in result
```

### Security

#### No Hardcoded Secrets
```python
# Good
api_key = os.getenv("PERPLEXITY_API_KEY")

# Bad
api_key = "sk-1234567890abcdef"  # Never do this
```

#### SQL Injection Prevention
```python
# Good - Parameterized query
cursor.execute(
    "SELECT * FROM commodities WHERE ticker = ?",
    [ticker]
)

# Bad - String formatting
cursor.execute(
    f"SELECT * FROM commodities WHERE ticker = '{ticker}'"
)
```

### Performance

#### Generator Usage for Large Data
```python
# Good - Memory efficient
def process_large_dataset(filepath: str):
    for chunk in pd.read_csv(filepath, chunksize=1000):
        yield process_chunk(chunk)

# Less efficient for large files
def process_large_dataset(filepath: str):
    data = pd.read_csv(filepath)  # Loads entire file
    return process_all(data)
```

#### Caching Expensive Operations
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_calculation(commodity: str, date: str) -> float:
    """Cache results of expensive calculations"""
    ...
```

## Code Review Checklist

- [ ] Type hints on all functions
- [ ] Docstrings for public functions/classes
- [ ] Error handling with specific exceptions
- [ ] No hardcoded values or secrets
- [ ] Tests for new functionality
- [ ] No commented-out code
- [ ] Consistent naming conventions
- [ ] SQL injection prevention
- [ ] Performance considerations for large data

## Naming Conventions

### Variables and Functions
```python
# snake_case for variables and functions
commodity_price = 100.5
def calculate_moving_average():
    pass
```

### Classes
```python
# PascalCase for classes
class CommodityAnalyzer:
    pass
```

### Constants
```python
# UPPER_SNAKE_CASE for constants
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30
```

### Private Members
```python
class DataProcessor:
    def __init__(self):
        self._internal_state = {}  # Single underscore for internal
        self.__private = None      # Double underscore for name mangling (rare)
```

## File Organization

### Module Structure
```python
"""Module docstring explaining purpose.

This module handles commodity data processing for the dashboard.
"""

# Imports (organized as shown above)

# Module-level constants
DEFAULT_WINDOW = 30

# Module-level functions

# Classes

# Main execution (if applicable)
if __name__ == "__main__":
    main()
```

## Related Documentation

- [Setup Dev Environment](./setup-dev-environment.md)
- [Testing Strategy](./testing-strategy.md)
- [Git Workflow](./git-workflow.md)