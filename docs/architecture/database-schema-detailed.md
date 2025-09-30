# Commodity Database Schema Documentation

## Overview
This document provides comprehensive database schema documentation for the Commodity Database in Microsoft SQL Server. The database contains 18 tables across 12 sectors tracking global commodity prices, aviation metrics, trade data, and AI-powered market intelligence.

## Database Structure

### Sector Overview
1. **Agricultural** - Grains, oilseeds, and agricultural products
2. **Chemicals** - Plastics, petrochemicals, and chemical products
3. **Energy** - Oil, gas, coal, and fuel products
4. **Fertilizer** - DAP, NPK, Urea, and chemical products
5. **Livestock** - Hog prices with regional categorization
6. **Metals** - Precious and base metals
7. **Shipping_Freight** - Baltic shipping indices
8. **Steel** - Steel products, iron ore, and production costs
9. **Aviation** - Airline operations, revenue, and market metrics (4 tables)
10. **Fishery** - Seafood export transactions
11. **Reference** - Ticker metadata and mappings
12. **AI Intelligence** - Perplexity AI query cache, market intelligence, and news (3 tables)

---

## 1. Agricultural Table

### Schema
```sql
CREATE TABLE Agricultural (
    Ticker VARCHAR(50) NOT NULL,
    Date DATE NOT NULL,
    Price DECIMAL(18,6),
    PRIMARY KEY (Ticker, Date)
);

CREATE INDEX idx_agricultural_date ON Agricultural(Date);
```

### Possible Ticker Values (12)
| Ticker | Name |
|--------|------|
| `AUWH0380 Index` | Malting Barley - Australia |
| `C 1 COMB Comdty` | Corn |
| `KO1 Comdty` | Palm Oil |
| `LMA1 Comdty` | Skim milk powder |
| `MLT0CLM1 Index` | Malting Barley - France |
| `OMR1 Comdty` | Whole milk powder |
| `RL10HVM1 Index` | Rice VN Exports |
| `RR1 COMB Comdty` | Rice (US) |
| `S 1 COMB Comdty` | Soybean |
| `SB1 Comdty` | Sugar |
| `SM1 COMB Comdty` | Soybean meal |
| `W 1 COMB Comdty` | Wheat |

---

## 2. Chemicals Table

### Schema
```sql
CREATE TABLE Chemicals (
    Ticker VARCHAR(50) NOT NULL,
    Date DATE NOT NULL,
    Price DECIMAL(18,6),
    PRIMARY KEY (Ticker, Date)
);

CREATE INDEX idx_chemicals_date ON Chemicals(Date);
```

### Possible Ticker Values (4)
| Ticker | Name |
|--------|------|
| `POLIPVSE Index` | PVC Spot SEA |
| `PSEAPVC0 Index` | PVC Contract SEA |
| `MERSPSG2 Index` | SE Asia PE (Polyethylene) |
| `MERSPEH2 Index` | SE Asia PS (Polystyrene) |

---

## 3. Energy Table

### Schema
```sql
CREATE TABLE Energy (
    Ticker VARCHAR(50) NOT NULL,
    Date DATE NOT NULL,
    Price DECIMAL(18,6),
    PRIMARY KEY (Ticker, Date)
);

CREATE INDEX idx_energy_date ON Energy(Date);
```

### Possible Ticker Values (19)
| Ticker | Name |
|--------|------|
| `APCRMINA Index` | APCRMINA Index |
| `BAKETOT Index` | US Rig Count |
| `BAKMFOR Index` | International Rig Count |
| `CL1 COMB Comdty` | WTI Crude Oil |
| `CO1 Comdty` | Brent Crude Oil |
| `CRKS321C Index` | US Crack Spread |
| `CRKSM211 Index` | Asia Crack Spread |
| `GASL500P Index` | Gasoline Index |
| `HARDCOAL Index` | Hard Coal |
| `JETKSPOT Index` | Jet Fuel |
| `JKL1 COMB Comdty` | Asian LNG |
| `LQM1SPVL Index` | Very Low Sulfur Fuel Oil |
| `MOGFM92S Index` | MOGFM92S Index |
| `N6SH180S Index` | Marine Fuel Oil |
| `NG1 COMB Comdty` | US Natural Gas |
| `TRC1 COMB Comdty` | China Thermal Coal |
| `TTD1 Comdty` | EU Natural Gas |
| `W51 COMB Comdty` | Singapore Fuel 380 |
| `XW1 Comdty` | Australia Coal |

---

## 4. Fertilizer Table

### Schema
```sql
CREATE TABLE Fertilizer (
    Ticker VARCHAR(100) NOT NULL,  -- Larger size for Vietnamese names
    Date DATE NOT NULL,
    Price DECIMAL(18,6),
    PRIMARY KEY (Ticker, Date)
);

CREATE INDEX idx_fertilizer_date ON Fertilizer(Date);
```

### Possible Ticker Values (22)
| Ticker | Name |
|--------|------|
| `CCCNIPYK AMTL Index` | China Fluorspar |
| `CFP MOP Index` | MOP China |
| `CHCNCASO Index` | China Caustic Soda |
| `DAP Vân Thiên Hóa xanh 64%` | DAP Vân Thiên Hóa xanh 64% |
| `DAP Đình Vũ xanh 61%` | DAP Đình Vũ xanh 61% |
| `GCFPAMTP Index` | US Ammonia |
| `GCFPDACN Index` | DAP China |
| `GCFPDANO Index` | DAP US |
| `GCFPPGMW Index` | Potash US |
| `GCFPURCH Index` | China Urea |
| `GCFPURCN Index` | China Urea 2 |
| `GCFPURCP Index` | China Urea Prill |
| `GCFPURGB Index` | Urea US |
| `GCFPURID Index` | Indo Urea |
| `GCFPURMG Index` | Urea Middle East |
| `NPK Bình Điền 16-16-8+13S` | NPK Bình Điền 16-16-8+13S |
| `NPK Cà Mau 16-16-8+TE` | NPK Cà Mau 16-16-8+TE |
| `NPK Phú Mỹ 16-16-8` | NPK Phú Mỹ 16-16-8 |
| `UFC1 Comdty` | Urea US Gulf Future |
| `UFE1 Comdty` | Urea Brazil Future |
| `UMP1 Comdty` | Urea Middle East Future |
| `URIF4 Comdty` | China Urea Futures |

---

## 5. Livestock Table

### Schema
```sql
CREATE TABLE Livestock (
    Ticker VARCHAR(100) NOT NULL,
    Date DATE NOT NULL,
    Price DECIMAL(18,6),
    PRIMARY KEY (Ticker, Date)
);

CREATE INDEX idx_livestock_date ON Livestock(Date);
CREATE INDEX idx_livestock_ticker ON Livestock(Ticker);
```

### Data Sources
1. **Steel_priceDB.xlsx** - Hog china sheet:
   - `JCIAPGDN Index` - China Hog Price Index
   - `LHDF4 Comdty` - Lean Hog Futures

2. **UreDB.xlsx** - Gia Heo sheet:
   - Ticker values are taken from the Categories column
   - Price values are taken from the Average column
   - Categories become ticker names (e.g., Hog_corporate_North, Hog_farmer_South, etc.)

---

## 6. Metals Table

### Schema
```sql
CREATE TABLE Metals (
    Ticker VARCHAR(50) NOT NULL,
    Date DATE NOT NULL,
    Price DECIMAL(18,6),
    PRIMARY KEY (Ticker, Date)
);

CREATE INDEX idx_metals_date ON Metals(Date);
```

### Possible Ticker Values (7)
| Ticker | Name |
|--------|------|
| `HGH4 COMB Comdty` | Copper |
| `LA1 Comdty` | Aluminum |
| `XAG BGNT Curncy` | Silver |
| `XAU BGNT Curncy` | Gold |
| `TGCNZCDU AMTL Index` | China Tungsten |
| `BICNTEBX AMTL Index` | China Bismuth |
| `AACNPC01 SMMC Index` | Alumina |

---

## 7. Shipping_Freight Table

### Schema
```sql
CREATE TABLE Shipping_Freight (
    Ticker VARCHAR(50) NOT NULL,
    Date DATE NOT NULL,
    Price DECIMAL(18,6),
    PRIMARY KEY (Ticker, Date)
);

CREATE INDEX idx_shipping_date ON Shipping_Freight(Date);
```

### Possible Ticker Values (7)
| Ticker | Name |
|--------|------|
| `BDIY Index` | Baltic Dry Index |
| `BHSI Index` | Baltic Handysize Index |
| `BIDY Index` | Baltic Dirty Tanker Index |
| `BITY Index` | Baltic Clean Tanker Index |
| `SHSPSCFI Index` | Shanghai Container Freight Index |
| `CTEX1100 Index` | 1100 TC (Container Rate) |
| `CTEX1700 Index` | 1700 TC (Container Rate) |

---

## 8. Steel Table

### Schema
```sql
CREATE TABLE Steel (
    Ticker VARCHAR(50) NOT NULL,
    Date DATE NOT NULL,
    Price DECIMAL(18,6),
    PRIMARY KEY (Ticker, Date)
);

CREATE INDEX idx_steel_date ON Steel(Date);
```

### Possible Ticker Values (24+)

#### Bloomberg Tickers
| Ticker | Name |
|--------|------|
| `CDSPDRAV Index` | China Long Steel |
| `CDSPHRAV Index` | China HRC |
| `CNMUSHAN Index` | Scrap Metal |
| `CVCNTLJK AMTL Index` | China Coking Coal |
| `HRC1 Comdty` | US HRC Future |
| `IAC1 COMB Comdty` | Australian Metallurgical Coal |
| `IOECAU62 Index` | Iron Ore 62% Fe |
| `IOECBZ65 Index` | Brazil Iron Ore 65% Fe |
| `IOECIO59 Index` | Iron Ore 58% Fe |
| `RSPR Index` | RSPR Index |
| `RSCURATE Index` | RSCURATE Index |
| `STANHCXW KLSH Index` | HRC US |
| `STCNBIXW KLSH Index` | Billet China |
| `STNWHCXW KLSH Index` | HRC EU |
| `STVNHCCR KLSH Index` | HRC Vietnam Imported |

#### Local/Custom Tickers
| Ticker | Name |
|--------|------|
| `China LS` | China Long Steel Local |
| `HRC Formosa` | Formosa HRC |
| `HRC HPG` | Hoa Phat Group HRC |
| `Spot China HRC` | China HRC Spot Price |
| `Spot China LS` | China Long Steel Spot |
| `Spot VN HRC` | Vietnam HRC Spot |
| `Spot VN LS` | Vietnam Long Steel Spot |
| `VN HRC` | Vietnam HRC |
| `VN LS` | Vietnam Long Steel |

---

## 9. Aviation Sector (4 Tables)

### 9.1 Aviation_Airfare Table

#### Schema
```sql
CREATE TABLE Aviation_Airfare (
    Date DATE NOT NULL,
    Airline VARCHAR(50) NOT NULL,
    Route VARCHAR(20) NOT NULL,
    Flight_time VARCHAR(10) NOT NULL,
    Booking_period VARCHAR(10) NOT NULL,
    Fare DECIMAL(12,2) NOT NULL,
    Created_date DATETIME DEFAULT GETDATE(),
    PRIMARY KEY (Date, Airline, Route, Flight_time, Booking_period)
);

CREATE INDEX idx_aviation_airfare_date ON Aviation_Airfare(Date);
```

#### Column Values
| Column | Possible Values |
|--------|----------------|
| Airline | `VN` (Vietnam Airlines), `VJ` (VietJet) |
| Route | `SGN-HAN`, `HAN-SGN`, `SGN-DAD`, `DAD-SGN` |
| Flight_time | `Morning`, `Afternoon`, `Evening` |
| Booking_period | `1W` (1 week), `1M` (1 month), `1Q` (1 quarter) |

### 9.2 Aviation_Operations Table

#### Schema
```sql
CREATE TABLE Aviation_Operations (
    Date DATE NOT NULL,
    Period_type VARCHAR(20) NOT NULL,
    Airline VARCHAR(50) NOT NULL,
    Metric_type VARCHAR(50) NOT NULL,
    Traffic_type VARCHAR(20),
    Metric_value DECIMAL(18,3),
    Unit VARCHAR(20),
    Created_date DATETIME DEFAULT GETDATE(),
    PRIMARY KEY (Date, Period_type, Airline, Metric_type, Traffic_type)
);

CREATE INDEX idx_aviation_operations_date ON Aviation_Operations(Date);
```

#### Column Values
| Column | Possible Values |
|--------|----------------|
| Period_type | `Monthly`, `Quarterly` |
| Airline | `Vietnam Airlines`, `VietJet Air`, `Bamboo Airways`, `Pacific Airlines`, `Vietravel Airlines`, `Total` |
| Metric_type | `Flight_count`, `OTP`, `Load_factor`, `Aircraft_count`, `Passengers`, `Market_share` |
| Traffic_type | `Domestic`, `International`, `N/A` (for non-traffic metrics) |
| Unit | `flights`, `percentage`, `aircraft`, `thousands` |

### 9.3 Aviation_Revenue Table

#### Schema
```sql
CREATE TABLE Aviation_Revenue (
    Date DATE NOT NULL,
    Year INT NOT NULL,
    Quarter INT NOT NULL,
    Airline VARCHAR(50) NOT NULL,
    Revenue_type VARCHAR(50) NOT NULL,
    Revenue_amount DECIMAL(18,2),
    Currency VARCHAR(10) DEFAULT 'VND',
    Created_date DATETIME DEFAULT GETDATE(),
    PRIMARY KEY (Year, Quarter, Airline, Revenue_type)
);

CREATE INDEX idx_aviation_revenue_date ON Aviation_Revenue(Date);
```

#### Column Values
| Column | Possible Values |
|--------|----------------|
| Airline | `HVN` (Vietnam Airlines Group), `VJC` (VietJet Air) |
| Revenue_type | `Revenue`, `EBITDA`, `EBIT`, `PBT`, `PAT` |
| Currency | `VND` |

### 9.4 Aviation_Market Table

#### Schema
```sql
CREATE TABLE Aviation_Market (
    Date DATE NOT NULL,
    Metric_type VARCHAR(50) NOT NULL,
    Metric_name VARCHAR(100) NOT NULL,
    Metric_value DECIMAL(18,3),
    Unit VARCHAR(20),
    Created_date DATETIME DEFAULT GETDATE(),
    PRIMARY KEY (Date, Metric_type, Metric_name)
);

CREATE INDEX idx_aviation_market_date ON Aviation_Market(Date);
```

#### Column Values
| Column | Possible Values |
|--------|----------------|
| Metric_type | `Passengers`, `Load_factor`, `Yield` |
| Metric_name | `Total_Domestic`, `Total_International`, `Industry_Average`, `Domestic_Average`, `International_Average` |
| Unit | `thousands`, `percentage`, `VND/km` |

---

## 10. Fishery Table (Renamed from Livestock_Export)

### Schema
```sql
CREATE TABLE Fishery (
    Date DATE NOT NULL,
    Company VARCHAR(20) NOT NULL,
    Market VARCHAR(20) NOT NULL,
    Volume DECIMAL(18,6),
    Value DECIMAL(18,6),
    Selling_Price DECIMAL(18,6),
    Input_Price DECIMAL(18,6),
    PRIMARY KEY (Date, Company, Market)
);

CREATE INDEX idx_fishery_date ON Fishery(Date);
```

### Column Values
| Column | Possible Values |
|--------|----------------|
| Company | `VHC` (Vinh Hoan), `IDI`, `ANV` |
| Market | `USA`, `EU`, `China`, `Japan`, `Total` |

---

## 11. Ticker_Reference Table

### Schema
```sql
CREATE TABLE Ticker_Reference (
    Ticker VARCHAR(100) PRIMARY KEY,
    Name VARCHAR(255),
    Sector VARCHAR(50),
    Data_Source VARCHAR(100),
    Active BOOLEAN DEFAULT 1
);

CREATE INDEX idx_ticker_sector ON Ticker_Reference(Sector);
```

### Sectors
- Agricultural
- Chemicals
- Energy
- Fertilizer
- Livestock
- Metals
- Shipping_Freight
- Steel
- Aviation (for fuel price reference)
- AI Intelligence (for market analysis)

---

## 12. AI Intelligence Sector (3 Tables)

### 12.1 AI_Query_Cache Table

#### Schema
```sql
CREATE TABLE AI_Query_Cache (
    Commodity VARCHAR(50) NOT NULL,          -- Natural name: "iron ore", "coking coal"
    Query_Date DATE NOT NULL,                -- Date of query
    Timeframe VARCHAR(20) NOT NULL,          -- "1 week" or "1 month"
    Query_Response NVARCHAR(MAX),            -- Full JSON response from Perplexity
    Created_At DATETIME2 DEFAULT GETDATE(),  -- When cache entry created
    Expires_At DATETIME2,                    -- When cache expires
    Cache_Hit_Count INT DEFAULT 0,           -- Track cache usage
    PRIMARY KEY (Commodity, Query_Date, Timeframe)
);

CREATE INDEX idx_ai_cache_expires ON AI_Query_Cache(Expires_At);
CREATE INDEX idx_ai_cache_commodity ON AI_Query_Cache(Commodity);
```

#### Column Details
| Column | Type | Description |
|--------|------|-------------|
| Commodity | VARCHAR(50) | Natural commodity name from Perplexity API |
| Query_Date | DATE | Date the query was made |
| Timeframe | VARCHAR(20) | Analysis timeframe: "1 week" or "1 month" |
| Query_Response | NVARCHAR(MAX) | Complete JSON response from AI |
| Created_At | DATETIME2 | Timestamp of cache creation |
| Expires_At | DATETIME2 | Cache expiration timestamp |
| Cache_Hit_Count | INT | Number of times cache entry was accessed |

#### Possible Commodity Values (Steel Focus)
| Commodity | Description |
|-----------|-------------|
| `iron ore` | Iron Ore 62% Fe benchmark |
| `coking coal` | Premium hard coking coal |
| `scrap steel` | HMS 1&2, ferrous scrap |
| `steel rebar` | Construction steel, rebar |
| `steel HRC` | Hot Rolled Coil |

### 12.2 AI_Market_Intelligence Table

#### Schema
```sql
CREATE TABLE AI_Market_Intelligence (
    Commodity VARCHAR(50) NOT NULL,           -- Natural commodity name
    Analysis_Date DATE NOT NULL,              -- Date of analysis
    Trend VARCHAR(20),                        -- bullish/bearish/stable
    Key_Drivers NVARCHAR(MAX),                -- JSON array of drivers
    Current_Price DECIMAL(18,6),              -- Current price value
    Price_Unit VARCHAR(20),                   -- USD/ton, USD/barrel, etc.
    Price_Change_Pct DECIMAL(18,6),           -- Percentage change
    Confidence_Score DECIMAL(18,6),           -- AI confidence in analysis
    Created_At DATETIME2 DEFAULT GETDATE(),
    PRIMARY KEY (Commodity, Analysis_Date)
);

CREATE INDEX idx_ai_intelligence_date ON AI_Market_Intelligence(Analysis_Date DESC);
CREATE INDEX idx_ai_intelligence_commodity ON AI_Market_Intelligence(Commodity);
```

#### Column Details
| Column | Type | Description |
|--------|------|-------------|
| Commodity | VARCHAR(50) | Natural commodity name |
| Analysis_Date | DATE | Date of the market analysis |
| Trend | VARCHAR(20) | Market trend: bullish/bearish/stable |
| Key_Drivers | NVARCHAR(MAX) | JSON array of market drivers |
| Current_Price | DECIMAL(18,6) | Extracted price value |
| Price_Unit | VARCHAR(20) | Price unit (USD/ton, etc.) |
| Price_Change_Pct | DECIMAL(18,6) | Percentage price change |
| Confidence_Score | DECIMAL(18,6) | AI confidence score (0-1) |
| Created_At | DATETIME2 | Record creation timestamp |

### 12.3 AI_News_Items Table

#### Schema
```sql
CREATE TABLE AI_News_Items (
    News_ID INT IDENTITY(1,1) PRIMARY KEY,
    Commodity VARCHAR(50),                    -- Related commodity
    News_Date DATE,                           -- Date of news event
    Headline NVARCHAR(500),                   -- News headline
    Summary NVARCHAR(MAX),                    -- News summary
    Source_URLs NVARCHAR(MAX),                -- JSON array of source URLs
    Sentiment VARCHAR(20),                    -- positive/negative/neutral
    Impact_Score DECIMAL(18,6),               -- Impact score (0-1)
    Created_At DATETIME2 DEFAULT GETDATE()
);

CREATE INDEX idx_news_commodity_date ON AI_News_Items(Commodity, News_Date DESC);
CREATE INDEX idx_news_date ON AI_News_Items(News_Date DESC);
```

#### Column Details
| Column | Type | Description |
|--------|------|-------------|
| News_ID | INT IDENTITY | Auto-incrementing primary key |
| Commodity | VARCHAR(50) | Associated commodity |
| News_Date | DATE | Date of the news event |
| Headline | NVARCHAR(500) | News headline (up to 500 chars) |
| Summary | NVARCHAR(MAX) | Full news summary |
| Source_URLs | NVARCHAR(MAX) | JSON array of source URLs |
| Sentiment | VARCHAR(20) | Sentiment: positive/negative/neutral |
| Impact_Score | DECIMAL(18,6) | Impact score (0-1 scale) |
| Created_At | DATETIME2 | Record creation timestamp |

### Helper Views

#### v_AI_Latest_Intelligence
```sql
CREATE VIEW v_AI_Latest_Intelligence AS
SELECT
    mi.*,
    DATEDIFF(DAY, mi.Analysis_Date, GETDATE()) as Days_Old
FROM AI_Market_Intelligence mi
INNER JOIN (
    SELECT Commodity, MAX(Analysis_Date) as Latest_Date
    FROM AI_Market_Intelligence
    GROUP BY Commodity
) latest ON mi.Commodity = latest.Commodity
    AND mi.Analysis_Date = latest.Latest_Date;
```

#### v_AI_Active_Cache
```sql
CREATE VIEW v_AI_Active_Cache AS
SELECT
    Commodity,
    Query_Date,
    Timeframe,
    Cache_Hit_Count,
    DATEDIFF(HOUR, Created_At, GETDATE()) as Hours_Old,
    DATEDIFF(HOUR, GETDATE(), Expires_At) as Hours_Until_Expiry
FROM AI_Query_Cache
WHERE Expires_At > GETDATE();
```

### Stored Procedures

#### sp_AI_Cleanup_Cache
```sql
CREATE PROCEDURE sp_AI_Cleanup_Cache
    @DaysToKeep INT = 7
AS
BEGIN
    DELETE FROM AI_Query_Cache
    WHERE Expires_At < GETDATE()
        OR Created_At < DATEADD(DAY, -@DaysToKeep, GETDATE());
END
```

#### sp_AI_Get_Cached_Query
```sql
CREATE PROCEDURE sp_AI_Get_Cached_Query
    @Commodity VARCHAR(50),
    @Query_Date DATE,
    @Timeframe VARCHAR(20)
AS
BEGIN
    -- Update hit count
    UPDATE AI_Query_Cache
    SET Cache_Hit_Count = Cache_Hit_Count + 1
    WHERE Commodity = @Commodity
        AND Query_Date = @Query_Date
        AND Timeframe = @Timeframe
        AND Expires_At > GETDATE();

    -- Return cached data
    SELECT Query_Response
    FROM AI_Query_Cache
    WHERE Commodity = @Commodity
        AND Query_Date = @Query_Date
        AND Timeframe = @Timeframe
        AND Expires_At > GETDATE();
END
```

---

## Performance Optimization

### Composite Primary Keys
All tables use composite primary keys based on business columns rather than artificial IDs:
- Standard commodity tables: `(Ticker, Date)`
- Livestock: `(Ticker, Date, Category, Region)`
- Fishery: `(Date, Company, Market)`
- Aviation tables: Various combinations based on business requirements

### Indexing Strategy
1. **Clustered Indexes**: On primary keys for optimal sequential access
2. **Non-clustered Indexes**: On Date columns for time-series queries
3. **Additional Indexes**: On Sector in reference table for filtering

### Query Optimization Tips
- Use date ranges in WHERE clauses rather than date functions
- Leverage composite keys for efficient lookups
- Consider partitioning large tables by date for better performance
- Create indexed views for frequently accessed aggregations

---

## Data Characteristics

### Date Ranges
- **Historical Data**: Most commodities from 2000-01-01 to present
- **Vietnamese Hog Data**: From 2019-01-02 to present
- **Fishery Export Data**: From 2020-12-29 to present
- **Aviation Data**: Varies by table (daily to quarterly updates)

### Data Types
- **Prices**: DECIMAL(18,6) for precision
- **Tickers**: VARCHAR(50-100) to accommodate Bloomberg codes and Vietnamese names
- **Dates**: DATE type for daily granularity
- **Categories**: VARCHAR for flexible categorization

### Special Considerations
- **Unicode Support**: Required for Vietnamese product names
- **NULL Handling**: Some metrics may have NULL values (intentional)
- **Currency**: All prices in original currency (mostly USD, some VND)
- **Units**: Vary by commodity (documented in reference table)

---

## Migration Notes

### Data Sources
1. **Steel_priceDB.xlsx**: 
   - Daily sheet → Steel table
   - Commodities sheet → Multiple sector tables
   - Hog china sheet → Livestock table

2. **UreDB.xlsx**:
   - Giá heo sheet → Livestock table (regional categories)
   - VHC Export sheet → Fishery table

3. **Aviation pickle files**:
   - 14 pickle files → 4 Aviation tables
   - Already migrated (skip in new migrations)

### Data Transformation Rules
- Unpivot wide-format Excel data to long format
- Handle missing values appropriately
- Convert Vietnamese text to Unicode
- Standardize date formats
- Calculate averages where needed (e.g., Livestock High/Low prices)

---

## Database Connection

### SQL Server Configuration
```sql
-- Database settings
CREATE DATABASE CommodityDB
COLLATE Latin1_General_CI_AS;

-- Enable Unicode support
ALTER DATABASE CommodityDB 
SET COMPATIBILITY_LEVEL = 150;

-- Set recovery model
ALTER DATABASE CommodityDB 
SET RECOVERY SIMPLE;
```

### Connection String Examples

#### SQL Dashboard (Read-Only Access)
```python
import pyodbc
import sqlalchemy

# Read-only connection for SQL Dashboard
conn_string = """
    DRIVER={ODBC Driver 17 for SQL Server};
    SERVER=your_server;
    DATABASE=CommodityDB;
    UID=readonly_user;
    PWD=password;
    TrustServerCertificate=yes
"""

# SQLAlchemy connection
engine = sqlalchemy.create_engine(
    f"mssql+pyodbc:///?odbc_connect={conn_string}",
    fast_executemany=True
)
```

#### AI Dashboard (Write Access Required)
```python
import pyodbc
import sqlalchemy

# Write-enabled connection for AI Dashboard
conn_string = """
    DRIVER={ODBC Driver 17 for SQL Server};
    SERVER=your_server;
    DATABASE=CommodityDB;
    UID=write_user;
    PWD=password;
    TrustServerCertificate=yes
"""

# SQLAlchemy connection with pooling
engine = sqlalchemy.create_engine(
    f"mssql+pyodbc:///?odbc_connect={conn_string}",
    fast_executemany=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600
)
```

---

## Maintenance and Updates

### Daily Updates
- Commodity prices from data providers
- Aviation airfare from web scraping
- AI market intelligence queries (cached for 24 hours)
- Perplexity AI news aggregation

### Monthly Updates
- Aviation operations metrics
- Market statistics

### Quarterly Updates
- Aviation revenue data
- Financial reports

### Automated Maintenance
- AI cache cleanup (expires after 24-48 hours)
- Old cache entries purged after 7 days
- Cache hit statistics tracking

### Data Validation
- Check for duplicate entries before insertion
- Validate ticker codes against reference table
- Ensure date continuity
- Monitor for outliers and data quality issues
- Sanitize commodity names for AI tables
- JSON validation for AI response data

---

## Contact Information
For questions about the database schema or access:
- Database Administrator: [Contact Information]
- Data Team: [Contact Information]
- Last Updated: 2025-01-17

---

*End of Documentation*