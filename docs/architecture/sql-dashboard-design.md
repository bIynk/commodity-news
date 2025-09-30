# Commodity Market Dashboard - Technical Documentation

## Overview

A Streamlit-based commodity market dashboard that displays real-time commodity price data from a Microsoft SQL Server database. The application features interactive charts, advanced filtering, performance metrics, and comprehensive price analysis across 11 commodity sectors with 200+ tickers.

## System Architecture

### Data Source
- **Primary Source**: Microsoft SQL Server Database (CommodityDB)
- **No Fallback**: Database connection is mandatory - application stops if connection fails
- **Data Coverage**: 11 sectors, 200+ commodity tickers
- **Historical Data**: Varies by commodity (most from 2000-present)

### Technology Stack
- **Frontend**: Streamlit
- **Data Processing**: Pandas, NumPy
- **Visualization**: Plotly, AG-Grid
- **Database**: SQL Server with pyodbc/SQLAlchemy
- **Configuration**: Environment variables / Streamlit secrets

## Async Loading Architecture

### Fragment-Based Loading Pattern
As of January 2025, the dashboard implements an asynchronous loading pattern for heavy operations:

#### AI Intelligence Module
- **Location**: `modules/ai_section.py`
- **Pattern**: Streamlit fragment with `@st.fragment` decorator
- **Behavior**: Loads independently without blocking main dashboard

#### Benefits
1. **Immediate Responsiveness**: Users see main content in < 2 seconds
2. **Progressive Enhancement**: AI features appear when ready
3. **Better UX**: Users can interact with charts/filters while AI loads
4. **Scalability**: Easy to add more async modules

#### Implementation Pattern
```python
# Separate heavy operations into fragments
@st.fragment
def render_async_feature():
    with st.spinner("Loading feature..."):
        # Heavy operation here
        data = expensive_operation()
    # Display when ready
    st.write(data)

# Main dashboard calls fragment
def main():
    # Render immediate content
    display_main_dashboard()

    # Async content loads independently
    render_async_feature()
```

This pattern should be used for any feature that:
- Takes > 2 seconds to load
- Requires external API calls
- Performs heavy computations
- Is not critical for initial dashboard display

## Database Integration

### Connection Configuration

#### Local Development (Environment Variable)
Set the `DC_DB_STRING` environment variable with your complete connection string:

**Windows (Command Prompt):**
```cmd
set DC_DB_STRING="DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=CommodityDB;UID=sa;PWD=YourPassword"
```

**Windows (PowerShell):**
```powershell
$env:DC_DB_STRING="DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=CommodityDB;UID=sa;PWD=YourPassword"
```

**Linux/Mac:**
```bash
export DC_DB_STRING="DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=CommodityDB;UID=sa;PWD=YourPassword"
```


**Connection String Examples:**
- Local with Windows Auth: `DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=CommodityDB;Trusted_Connection=yes`
- Local with SQL Auth: `DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=CommodityDB;UID=sa;PWD=password`
- Remote Server: `DRIVER={ODBC Driver 17 for SQL Server};SERVER=192.168.1.100,1433;DATABASE=CommodityDB;UID=user;PWD=pass;TrustServerCertificate=yes`
- Azure SQL: `DRIVER={ODBC Driver 17 for SQL Server};SERVER=server.database.windows.net;DATABASE=CommodityDB;UID=user@server;PWD=pass;Encrypt=yes`

#### Production Deployment (Streamlit Cloud)
Configure `SQL_CONNECTION_STRING` in Streamlit Cloud Settings > Secrets using the template from `.streamlit/secrets.toml.example`

### Database Schema

The dashboard connects to a SQL Server database with the following structure:

#### Active Sector Tables (7 tables currently in use)
- **Agricultural**: Grains, oilseeds, agricultural products (Price column)
- **Chemicals**: Plastics, petrochemicals (Price column)
- **Energy**: Oil, gas, coal, fuel products (Price column)
- **Fertilizer**: DAP, NPK, Urea products (Price column)
- **Metals**: Precious and base metals (Price column)
- **Shipping_Freight**: Baltic shipping indices (Price column)
- **Steel**: Steel products, iron ore (Price column)

#### Temporarily Disabled Tables (3 tables - pending special processing)
- **Livestock**: Hog prices with regional data (**Average_Price** column) - *DISABLED*
- **Fishery**: Seafood export data (**Selling_Price** column) - *DISABLED*
- **Aviation**: Airline metrics (4 sub-tables - special structure) - *NOT IMPLEMENTED*

**Note**: Livestock and Fishery tables are temporarily disabled (January 2025) due to data mapping issues. These tables have tickers that don't exist in the Ticker_Reference table, causing None values in displays. They require special processing logic to be implemented.

#### Reference Table
- **Ticker_Reference**: Maps tickers to display names and sectors

#### Important Column Name Variations
**CRITICAL**: Different tables use different column names for price data:
- Most tables (Agricultural, Chemicals, Energy, Fertilizer, Metals, Shipping_Freight, Steel): `Price`
- Livestock table: `Average_Price` 
- Fishery table: `Selling_Price`

The query builder (`query_builder.py`) handles these variations automatically by aliasing all price columns to `Price` in the SELECT statements.

#### Commodity Name Display
**USER-FACING DISPLAY**: The dashboard displays human-readable commodity names instead of ticker codes:
- The `Ticker_Reference` table maps ticker codes to display names
- Data loader (`data_loader.py`) automatically maps tickers to names using the `Name` column
- All UI elements (tables, charts, filters) show commodity names for better user experience
- Internal processing still uses ticker codes for database queries

### Query Architecture
- **Dynamic SQL Generation**: `query_builder.py` creates UNION queries across sector tables
- **Connection Pooling**: SQLAlchemy with 5 connections, 10 overflow
- **Caching**: 1-hour TTL on data queries via `@st.cache_data`

## Core Features

### 1. Advanced Filtering System
Located in the sidebar, provides multi-level filtering:

- **Data Last Updated**: Displays the most recent date in the database (reference point for all calculations)
  - Shows formatted date (e.g., "January 15, 2025")
  - Includes explanatory caption about calculation reference point
- **Sector Filter**: Select from 7 active sectors (Livestock and Fishery temporarily disabled)
- **Nation Filter**: Geographic filtering (Global, China, US, etc.)
- **Change Type Filter**: Positive/Negative/Neutral based on weekly performance
- **Commodity Filter**: Dynamic list based on selected sectors
- **Date Range**: Start and end date selection for historical analysis
- **Interval Selection**: Daily, Weekly, Monthly, Quarterly views

### 2. Key Market Metrics (KPI Dashboard)
Eight metric cards in a 2x4 grid layout displaying:

**Market Metrics:**
- **Most Bullish Commodity**: Commodity with highest %Week value (weekly gain)
  - Calculation: `max(%Week)` after filtering invalid values
- **Most Bearish Commodity**: Commodity with lowest %Week value (weekly loss)
  - Calculation: `min(%Week)` after filtering invalid values
- **Highest Volatility**: Placeholder for future implementation (displays "TBD")
- **Monthly Leader**: Commodity with highest %Month value
  - Calculation: `max(%Month)` after filtering invalid values

**Sector Metrics:**
- **Strongest Sector**: Sector with highest average weekly performance
  - Calculation: `groupby('Sector')['%Week'].mean().max()`
- **Extreme Moves Count**: Number of commodities with >±2% weekly change
  - Calculation: `count(abs(%Week) > 0.02)`
- **Future KPI placeholders**: Two slots for additional metrics

### 3. Detailed Price Table
Professional data grid using AG-Grid with:

- **Columns Displayed**:
  - Commodity name (ticker)
  - Sector and Nation
  - Current Price
  - Performance metrics: %Day, %Week, %Month, %Quarter, %YTD
  - Statistics: 30D Average, 52W High/Low
  - Change type classification

- **Features**:
  - Conditional formatting (green for positive, red for negative)
  - Sortable and filterable columns
  - Number formatting with thousand separators
  - Professional styling with Manrope font
  - Scroll view (no pagination)

### 4. Performance Charts
Tab-based visualization system with 5 timeframes:

- **Timeframes**: Daily, Weekly, Monthly, Quarterly, YTD
- **Split View Design**: 
  - Left side: Declining commodities (red bars)
  - Right side: Rising commodities (green bars)
- **Dynamic Height**: Adjusts based on number of items
- **Clean Presentation**: Hidden axes, external labels
- **Hover Information**: Full commodity details on mouseover

### 5. Commodity Price Trends
Interactive line charts showing:

- **Multi-commodity Comparison**: Select multiple commodities to compare
- **Customizable Date Range**: User-defined start and end dates
- **Interval Options**: Daily, Weekly, Monthly, Quarterly aggregation
- **Professional Styling**: Clean lines, proper legends, responsive design

### 6. Vietnamese Stock Integration (Deprecated)
*Note: Stock impact tracking features have been removed in the database version*
- Original CSV version tracked Vietnamese stock correlations
- Direct/Inverse impact columns are maintained for compatibility but not populated

## Data Processing Pipeline

### 1. Data Loading Flow
```
SQL Server → SQLAlchemy → Pandas DataFrame → Streamlit Cache → UI Components
```

### 2. Price Calculations
The `calculations.py` module computes percentage changes and metrics:

#### Reference Date Determination
- **Selected Date**: Uses the maximum (most recent) date in the database
- **Current Price**: Most recent price on or before the selected date for each commodity

#### Time Period Calculations
- **Daily Change**: Current price vs. previous day
  - Formula: `(Current Price / Price at selected_date - 1 day) - 1`
- **Weekly Change**: Current price vs. previous Friday
  - Formula: `(Current Price / Price at previous Friday) - 1`
  - Uses `pd.offsets.Week(weekday=4)` to find previous Friday
- **Monthly Change**: Current price vs. previous month-end
  - Formula: `(Current Price / Price at previous month-end) - 1`
- **Quarterly Change**: Current price vs. previous quarter-end
  - Formula: `(Current Price / Price at previous quarter-end) - 1`
- **YTD Change**: Current price vs. previous year-end
  - Formula: `(Current Price / Price at previous year-end) - 1`

#### Additional Metrics
- **30-day Average**: Mean price over the last 30 days
- **52-week High/Low**: Maximum and minimum prices over the last 52 weeks
- **Change Type Classification**: 
  - Positive: %Week > 0
  - Negative: %Week < 0
  - Neutral: %Week = 0

#### Data Filtering for Metrics
Before calculating KPI statistics, invalid values are excluded:
- NaN values (missing data)
- Infinite values (division by zero)
- -1.0 values (indicating no historical price exists)
- Rows with missing commodity names

### 3. Performance Optimization
- **Connection Pooling**: Reuses database connections
- **Query Optimization**: Indexed queries with date filtering
- **Data Caching**: 1-hour cache prevents redundant queries
- **Lazy Loading**: Data loads only when needed

## File Structure

```
Commodities-Dashboard-v2/
├── Home.py                    # Main application entry point
├── modules/
│   ├── db_connection.py      # Database connection management
│   ├── query_builder.py      # Dynamic SQL query generation
│   ├── data_loader.py        # Data loading from database
│   ├── calculations.py       # Price change calculations
│   ├── styling.py            # UI styling and AG-Grid config
│   ├── stock_data.py         # Stock data fetching (deprecated)
│   └── news_data.py          # News fetching (deprecated)
├── pages/
│   └── Chart_Analysis.py     # Additional chart pages (empty)
├── data/                      # CSV files (no longer used)
├── .streamlit/
│   └── secrets.toml.example # Streamlit deployment template
├── requirements.txt          # Python dependencies
└── .gitignore               # Version control exclusions
```

## Deployment

### Prerequisites
- Python 3.8+
- SQL Server with CommodityDB database
- ODBC Driver 17 for SQL Server

### Local Installation
```bash
# Clone repository
git clone [repository-url]
cd Commodities-Dashboard-v2

# Install dependencies
pip install -r requirements.txt

# Configure database connection:
# Set environment variable (choose based on your OS/shell):

# Linux/Mac:
export DC_DB_STRING="DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=CommodityDB;UID=sa;PWD=password"

# Windows (cmd):
set DC_DB_STRING="DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=CommodityDB;UID=sa;PWD=password"

# Windows (PowerShell):
$env:DC_DB_STRING="DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=CommodityDB;UID=sa;PWD=password"

# Run application
streamlit run Home.py
```

### Streamlit Cloud Deployment
1. Push code to GitHub
2. Connect repository to Streamlit Cloud
3. Configure secrets in app settings (copy from secrets.toml.example)
4. Deploy application

## Error Handling

### Database Connection Failures
- **Clear Error Messages**: Displays specific connection error
- **Configuration Guidance**: Instructions for setting environment variable or secrets
- **No Silent Failures**: Application stops completely on connection failure

### Data Quality Issues
- **Null Handling**: Removes rows with missing essential data
- **Type Conversion**: Coerces prices to numeric, dates to datetime
- **String Cleaning**: Strips whitespace from all text fields

## Performance Characteristics

### Response Times
- **Initial Load**: 3-5 seconds (database connection + first query)
- **Cached Requests**: <100ms (data cached for 1 hour)
- **Filter Updates**: 1-2 seconds (re-queries database)

### Scalability
- **Data Volume**: Handles 200+ tickers with millions of price points
- **Concurrent Users**: Connection pooling supports multiple users
- **Query Optimization**: Indexed queries and UNION ALL for efficiency

## Limitations

1. **No CSV Fallback**: Requires active database connection
2. **Stock Impact**: Vietnamese stock correlation features removed
3. **News Integration**: News fetching functionality removed (vnstock deprecated)
4. **Aviation Data**: Complex multi-table structure not fully integrated
5. **Real-time Updates**: Data refreshes hourly (cache TTL)
6. **Disabled Tables**: Livestock and Fishery tables temporarily disabled (ticker mapping issues)

## Future Enhancements

### Planned Features
1. Historical trend charts with technical indicators
2. Volatility calculations and risk metrics
3. Export functionality (Excel, PDF reports)
4. Price alerts and notifications
5. Multi-user authentication
6. Real-time data streaming

### Technical Improvements
1. Implement WebSocket for real-time updates
2. Add Redis caching layer
3. Containerize with Docker
4. Add comprehensive unit tests
5. Implement CI/CD pipeline

## Re-enabling Livestock and Fishery Tables

To re-enable the temporarily disabled tables:

### 1. Fix Ticker Mapping
Add missing ticker mappings to the `Ticker_Reference` table:
```sql
-- Example for Livestock tickers
INSERT INTO Ticker_Reference (Ticker, Name, Sector, Active)
VALUES 
    ('JCIAPGDN Index', 'China Hog Price Index', 'Livestock', 1),
    ('LHDF4 Comdty', 'Lean Hog Futures', 'Livestock', 1),
    ('Hog_corporate_North', 'Corporate Hog North', 'Livestock', 1),
    ('Hog_farmer_South', 'Farmer Hog South', 'Livestock', 1);

-- Example for Fishery tickers (Company_Market format)
INSERT INTO Ticker_Reference (Ticker, Name, Sector, Active)
VALUES 
    ('CompanyA_EU', 'Company A Europe', 'Fishery', 1),
    ('CompanyB_US', 'Company B USA', 'Fishery', 1);
```

### 2. Re-enable in Code
Uncomment the tables in `modules/query_builder.py`:
```python
SECTOR_TABLE_MAP = {
    # ... other sectors ...
    'Livestock': 'Livestock',  # Uncomment this line
    'Fishery': 'Fishery'       # Uncomment this line
}
```

### 3. Handle Special Processing
Consider implementing special handling for unmapped tickers in `modules/data_loader.py` if some tickers cannot be added to Ticker_Reference.

## Troubleshooting

### Common Issues

#### "Database connection failed"
- Verify SQL Server is running and accessible
- Check firewall rules for port 1433
- Confirm DC_DB_STRING environment variable is set
- Test connection string with SQL Server Management Studio

#### "No data displayed"
- Verify Ticker_Reference table is populated
- Check sector tables contain recent data
- Review date range filters
- Clear Streamlit cache: `streamlit cache clear`

#### Performance Issues
- Check database indexes are properly created
- Monitor SQL Server query performance
- Reduce date range or commodity selection
- Increase cache TTL if appropriate

## Security Considerations

1. **Credentials**: Never hardcode connection strings in code
2. **SQL Injection**: Parameterized queries prevent injection attacks
3. **Network Security**: Use TLS/SSL for database connections in production
4. **Access Control**: Implement database user permissions appropriately
5. **Secrets Management**: Use Streamlit secrets for deployment

## Support and Maintenance

### Configuration Files
- `.streamlit/secrets.toml.example`: Template for deployment
- `requirements.txt`: Python package dependencies

### Monitoring
- Database connection status shown in sidebar
- Error messages display in main area
- Logs available in Streamlit Cloud dashboard

### Updates
- Database schema changes require updating `query_builder.py`
- New sectors need mapping in `SECTOR_TABLE_MAP`
- UI changes primarily in `Home.py` and `styling.py`

---

## Changelog

### January 2025 Updates
- **Added**: Data Last Updated display in sidebar showing most recent database date
- **Fixed**: None values in Most Bearish metric by filtering invalid data
- **Fixed**: AG-Grid null value handling (displays "-" instead of errors)
- **Changed**: Commodity names now display instead of ticker codes
- **Disabled**: Livestock and Fishery tables temporarily (ticker mapping issues)
- **Added**: Comprehensive documentation of KPI calculation methodology
- **Enhanced**: Error handling for database connection failures

---

*Last Updated: January 2025*
*Version: 2.1 (Enhanced with commodity name display and data filtering)*