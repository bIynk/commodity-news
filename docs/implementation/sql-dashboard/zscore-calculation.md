# Z-Score Calculation Implementation

## Overview
The SQL dashboard implements frequency-aware Z-score calculations to identify statistical outliers in commodity price movements, accounting for different data update frequencies (daily vs weekly).

## Implementation Location
`current/sql-dashboard/modules/calculations.py`

## Core Algorithm

### Standard Z-Score Formula
```python
def calculate_zscore(value: float, mean: float, std: float) -> float:
    """Calculate standard Z-score"""
    if std == 0:
        return 0
    return (value - mean) / std
```

### Frequency-Aware Calculation
```python
def calculate_frequency_aware_zscore(df: pd.DataFrame, commodity: str) -> float:
    """Calculate Z-score based on data frequency"""

    # Determine update frequency
    frequency = detect_update_frequency(df, commodity)

    # Apply appropriate calculation window
    if frequency == 'daily':
        window = 30  # 30 days for daily data
    elif frequency == 'weekly':
        window = 12  # 12 weeks for weekly data
    else:
        window = 20  # Default fallback

    # Calculate statistics
    recent_data = df.tail(window)
    mean = recent_data['Price'].mean()
    std = recent_data['Price'].std()
    current_price = df['Price'].iloc[-1]

    return calculate_zscore(current_price, mean, std)
```

## Frequency Detection

### Algorithm
```python
def detect_update_frequency(df: pd.DataFrame, commodity: str) -> str:
    """Detect if commodity updates daily or weekly"""

    # Calculate days between updates
    df['Date'] = pd.to_datetime(df['Date'])
    df['Days_Between'] = df['Date'].diff().dt.days

    # Analyze update pattern
    median_gap = df['Days_Between'].median()

    if median_gap <= 1.5:
        return 'daily'
    elif 5 <= median_gap <= 8:
        return 'weekly'
    else:
        return 'irregular'
```

### Frequency Patterns
```python
FREQUENCY_PATTERNS = {
    'daily': {
        'window_days': 30,
        'min_data_points': 20,
        'staleness_threshold': 7
    },
    'weekly': {
        'window_days': 210,  # 30 weeks (current implementation)
        'min_data_points': 10,
        'staleness_threshold': 14
    }
}
```

## Frequency-Aware Staleness Filtering

### Implementation
```python
def apply_staleness_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Apply frequency-aware staleness thresholds"""
    from modules.constants import DataFreshnessConfig

    current_date = datetime.now()
    df['Days_Since_Update'] = (current_date - df['Date']).dt.days

    # Detect frequency for each commodity
    for commodity in df['Commodities'].unique():
        commodity_data = df[df['Commodities'] == commodity]
        freq = detect_frequency(commodity_data['Price'])

        # Apply appropriate threshold
        if freq == 'weekly':
            threshold = DataFreshnessConfig.WEEKLY_STALENESS_DAYS  # 14 days
        else:
            threshold = DataFreshnessConfig.DAILY_STALENESS_DAYS   # 7 days

        df.loc[df['Commodities'] == commodity, 'Update_Frequency'] = freq
        df.loc[df['Commodities'] == commodity, 'Is_Stale'] = (
            df.loc[df['Commodities'] == commodity, 'Days_Since_Update'] > threshold
        )

    # Mark stale Z-scores
    df.loc[df['Is_Stale'], 'Z_Score'] = np.nan
    df.loc[df['Is_Stale'], 'Display_Text'] = 'Data too old'

    return df
```

### Visual Indicators
```python
def format_zscore_display(zscore: float, is_stale: bool) -> Dict:
    """Format Z-score for display with visual cues"""

    if is_stale or np.isnan(zscore):
        return {
            'value': 'N/A',
            'color': 'gray',
            'icon': '⚠️'
        }

    # Color coding based on magnitude
    if abs(zscore) > 3:
        color = 'red'
        icon = '🔴'
    elif abs(zscore) > 2:
        color = 'orange'
        icon = '🟠'
    elif abs(zscore) > 1:
        color = 'yellow'
        icon = '🟡'
    else:
        color = 'green'
        icon = '🟢'

    return {
        'value': f"{zscore:.2f}",
        'color': color,
        'icon': icon
    }
```

## Rolling Window Calculations

### Implementation
```python
def calculate_rolling_zscore(df: pd.DataFrame, window: int = 30) -> pd.Series:
    """Calculate rolling Z-scores over time"""

    # Calculate rolling statistics
    rolling_mean = df['Price'].rolling(window=window).mean()
    rolling_std = df['Price'].rolling(window=window).std()

    # Calculate Z-score for each point
    zscores = (df['Price'] - rolling_mean) / rolling_std

    return zscores
```

### Adaptive Windows
```python
def get_adaptive_window(commodity: str, data_frequency: str) -> int:
    """Determine optimal window based on commodity characteristics"""

    volatile_commodities = ['natural gas', 'crude oil', 'wheat']
    stable_commodities = ['gold', 'silver', 'copper']

    if commodity.lower() in volatile_commodities:
        # Shorter window for volatile commodities
        return 20 if data_frequency == 'daily' else 8
    elif commodity.lower() in stable_commodities:
        # Longer window for stable commodities
        return 60 if data_frequency == 'daily' else 16
    else:
        # Default window
        return 30 if data_frequency == 'daily' else 12
```

## Outlier Detection

### Multi-Level Thresholds
```python
def classify_outlier(zscore: float) -> str:
    """Classify price movements by Z-score magnitude"""

    abs_z = abs(zscore)

    if abs_z > 4:
        return 'extreme_outlier'
    elif abs_z > 3:
        return 'severe_outlier'
    elif abs_z > 2:
        return 'moderate_outlier'
    elif abs_z > 1:
        return 'mild_outlier'
    else:
        return 'normal'
```

### Outlier Alerts
```python
def generate_outlier_alerts(df: pd.DataFrame) -> List[Dict]:
    """Generate alerts for significant outliers"""

    alerts = []

    for _, row in df.iterrows():
        if abs(row['Z_Score']) > 3:
            alerts.append({
                'commodity': row['Ticker'],
                'zscore': row['Z_Score'],
                'price': row['Price'],
                'date': row['Date'],
                'severity': 'high',
                'message': f"{row['Ticker']} showing extreme deviation ({row['Z_Score']:.2f}σ)"
            })

    return alerts
```

## Performance Optimization

### Vectorized Operations
```python
def calculate_batch_zscores(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate Z-scores for all commodities efficiently"""

    # Group by commodity
    grouped = df.groupby('Ticker')

    # Vectorized calculation
    df['Z_Score'] = grouped['Price'].transform(
        lambda x: (x - x.rolling(30).mean()) / x.rolling(30).std()
    )

    return df
```

### Caching Calculations
```python
@lru_cache(maxsize=128)
def get_cached_statistics(commodity: str, date: str) -> Tuple[float, float]:
    """Cache mean and std for repeated calculations"""
    df = load_commodity_data(commodity, date)
    return df['Price'].mean(), df['Price'].std()
```

## Visualization

### Z-Score Distribution
```python
def plot_zscore_distribution(zscores: pd.Series) -> plotly.Figure:
    """Create Z-score distribution plot"""

    fig = go.Figure()

    # Histogram
    fig.add_trace(go.Histogram(
        x=zscores,
        nbinsx=50,
        name='Z-Score Distribution'
    ))

    # Add normal distribution overlay
    x = np.linspace(-4, 4, 100)
    y = norm.pdf(x, 0, 1) * len(zscores) * 0.2

    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode='lines',
        name='Normal Distribution'
    ))

    # Add threshold lines
    for threshold in [-3, -2, 2, 3]:
        fig.add_vline(x=threshold, line_dash="dash")

    return fig
```

## Testing

### Unit Tests
```python
def test_zscore_calculation():
    """Test Z-score calculation accuracy"""

    # Test data
    values = [100, 102, 98, 101, 99, 105, 95]
    mean = np.mean(values)
    std = np.std(values)

    # Calculate Z-score for last value
    zscore = calculate_zscore(95, mean, std)

    assert abs(zscore - (-1.07)) < 0.01  # Expected Z-score
```

### Edge Cases
```python
def test_edge_cases():
    """Test handling of edge cases"""

    # Zero standard deviation
    assert calculate_zscore(100, 100, 0) == 0

    # Missing data
    assert np.isnan(calculate_zscore(np.nan, 100, 10))

    # Insufficient data points
    df_small = pd.DataFrame({'Price': [100, 101]})
    assert calculate_frequency_aware_zscore(df_small, 'test') == 0
```

## Related Documentation

- [Calculation Module](./calculations.md)
- [Data Loader](./data-loader.md)
- [Dashboard Visualization](./ag-grid-implementation.md)