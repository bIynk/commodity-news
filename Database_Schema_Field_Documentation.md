# Commodity Database Schema - Detailed Field Documentation

## Database Overview
**Database Name**: CommodityDB  
**Total Tables**: 13 (9 commodity sector + 4 aviation sector)  
**Total Records**: ~1.5M+ records  
**Design Pattern**: Sector-based organization with composite primary keys  
**Naming Convention**: PascalCase for all column names

---

## COMMODITY SECTOR TABLES

### 1. Commodity_Master Table
**Purpose**: Central reference table for all commodity tickers across all sectors  
**Primary Key**: Commodity_id (IDENTITY)  
**Unique Constraint**: Ticker

| Field | Data Type | Nullable | Description | Possible Values |
|-------|-----------|----------|-------------|-----------------|
| **Commodity_id** | INT IDENTITY(1,1) | NO | Auto-incrementing primary key | 1, 2, 3, ... |
| **Ticker** | VARCHAR(50) | NO | Unique commodity identifier | Examples:<br>• Bloomberg tickers: 'CDSPDRAV Index', 'IOECAU62 Index'<br>• Custom tickers: 'VN HRC', 'HRC HPG'<br>• Fertilizer tickers: 'DAP_DinhVu_61', 'NPK_BinhDien_16-16-8' |
| **Commodity_name** | NVARCHAR(100) | YES | Human-readable commodity name | Examples:<br>• 'Long steel China'<br>• 'Iron Ore 62%'<br>• 'Vietnam HRC'<br>• 'DAP Đình Vũ xanh 61%' |
| **Sector** | VARCHAR(50) | YES | Economic sector classification | Values:<br>• 'Steel'<br>• 'Energy'<br>• 'Metals'<br>• 'Agricultural'<br>• 'Fertilizer'<br>• 'Livestock'<br>• 'Shipping'<br>• 'Fishery' |
| **Subsector** | VARCHAR(50) | YES | Detailed sector classification | Examples:<br>• 'Iron Ore'<br>• 'Coking Coal'<br>• 'Precious Metals'<br>• 'Base Metals' |
| **Unit** | VARCHAR(20) | YES | Measurement unit | Examples:<br>• 'USD/ton'<br>• 'USD/barrel'<br>• 'USD/oz'<br>• 'VND/kg'<br>• 'Index' |
| **Is_active** | BIT | YES | Active status flag | • 1 = Active (default)<br>• 0 = Inactive |
| **Created_date** | DATETIME | YES | Record creation timestamp | Default: GETDATE() |
| **Updated_date** | DATETIME | YES | Last update timestamp | NULL or datetime value |

---

### 2. Steel Table
**Purpose**: Steel and iron commodity pricing data  
**Primary Key**: (Price_date, Ticker)  
**Foreign Key**: Ticker → Commodity_Master(Ticker)  
**Record Count**: ~180,000

| Field | Data Type | Nullable | Description | Possible Values |
|-------|-----------|----------|-------------|-----------------|
| **Price_date** | DATE | NO | Trading/price date | Date range: 2000-01-01 to present |
| **Ticker** | VARCHAR(50) | NO | Commodity ticker | Steel-related tickers:<br>• 'CDSPDRAV Index' (Long steel China)<br>• 'IOECAU62 Index' (Iron Ore 62%)<br>• 'CNMUSHAN Index' (Scrap)<br>• 'CDSPHRAV Index' (HRC China)<br>• 'HRC1 Comdty' (US HRC Future)<br>• 'VN HRC', 'HRC HPG', 'HRC Formosa' |
| **Price** | DECIMAL(18,4) | YES | Price value | Numeric values, e.g., 850.5000, 125.7500 |
| **Price_type** | VARCHAR(20) | YES | Type of price | • 'spot' - Spot price<br>• 'future' - Futures price<br>• 'margin' - Margin calculation<br>• 'moving_avg' - Moving average<br>• 'cash_cost' - Cash cost<br>• NULL - Standard price |
| **Created_date** | DATETIME | YES | Record creation timestamp | Default: GETDATE() |

---

### 3. Energy Table
**Purpose**: Energy commodity pricing (oil, gas, coal, jet fuel)  
**Primary Key**: (Price_date, Ticker)  
**Foreign Key**: Ticker → Commodity_Master(Ticker)  
**Record Count**: ~75,000

| Field | Data Type | Nullable | Description | Possible Values |
|-------|-----------|----------|-------------|-----------------|
| **Price_date** | DATE | NO | Trading/price date | Date range: 2000-01-01 to present |
| **Ticker** | VARCHAR(50) | NO | Commodity ticker | Energy tickers:<br>• 'CL1 COMB Comdty' (WTI Crude)<br>• 'CO1 Comdty' (Brent Crude)<br>• 'NG1 COMB Comdty' (Natural Gas)<br>• 'JETKSPOT Index' (Jet Fuel)<br>• 'IAC1 COMB Comdty' (Aus Coking Coal)<br>• 'HARDCOAL Index' (Hard Coal) |
| **Price** | DECIMAL(18,4) | YES | Price value | Numeric values, e.g., 75.2500, 3.4500 |
| **Product_type** | VARCHAR(50) | YES | Energy product category | • 'crude_oil'<br>• 'natural_gas'<br>• 'coal'<br>• 'coking_coal'<br>• 'jet_fuel'<br>• 'gasoline' |
| **Created_date** | DATETIME | YES | Record creation timestamp | Default: GETDATE() |

---

### 4. Metals Table
**Purpose**: Precious and base metals pricing  
**Primary Key**: (Price_date, Ticker)  
**Foreign Key**: Ticker → Commodity_Master(Ticker)  
**Record Count**: ~28,000

| Field | Data Type | Nullable | Description | Possible Values |
|-------|-----------|----------|-------------|-----------------|
| **Price_date** | DATE | NO | Trading/price date | Date range: 2000-01-01 to present |
| **Ticker** | VARCHAR(50) | NO | Commodity ticker | Metal tickers:<br>• 'XAU BGNT Curncy' (Gold)<br>• 'XAG BGNT Curncy' (Silver)<br>• 'HGH4 COMB Comdty' (Copper) |
| **Price** | DECIMAL(18,4) | YES | Price value | Numeric values, e.g., 1850.0000, 24.5000 |
| **Metal_type** | VARCHAR(20) | YES | Specific metal | • 'gold'<br>• 'silver'<br>• 'copper'<br>• 'aluminum'<br>• 'zinc' |
| **Metal_category** | VARCHAR(20) | YES | Metal classification | • 'precious'<br>• 'base' |
| **Price_unit** | VARCHAR(20) | YES | Pricing unit | • 'USD/oz' (precious metals)<br>• 'USD/ton' (base metals)<br>• 'USD/kg' |
| **Created_date** | DATETIME | YES | Record creation timestamp | Default: GETDATE() |

---

### 5. Agricultural Table
**Purpose**: Agricultural commodity pricing (grains, oilseeds, etc.)  
**Primary Key**: (Price_date, Ticker)  
**Foreign Key**: Ticker → Commodity_Master(Ticker)  
**Record Count**: ~37,000

| Field | Data Type | Nullable | Description | Possible Values |
|-------|-----------|----------|-------------|-----------------|
| **Price_date** | DATE | NO | Trading/price date | Date range: 2000-01-01 to present |
| **Ticker** | VARCHAR(50) | NO | Commodity ticker | Agricultural tickers:<br>• 'W51 COMB Comdty' (Wheat)<br>• 'C 1 COMB Comdty' (Corn)<br>• 'CRKSM211 Index' (Asia Crack Spread)<br>• 'CRKS321C Index' (US Crack Spread) |
| **Price** | DECIMAL(18,4) | YES | Price value | Numeric values |
| **Product_type** | VARCHAR(50) | YES | Agricultural product category | • 'grain'<br>• 'oilseed'<br>• 'sugar'<br>• 'coffee'<br>• 'crack_spread' |
| **Created_date** | DATETIME | YES | Record creation timestamp | Default: GETDATE() |

---

### 6. Fertilizer Table
**Purpose**: Fertilizer pricing data (Vietnamese market focus)  
**Primary Key**: (Price_date, Ticker)  
**Foreign Key**: Ticker → Commodity_Master(Ticker)  
**Record Count**: ~47,000

| Field | Data Type | Nullable | Description | Possible Values |
|-------|-----------|----------|-------------|-----------------|
| **Price_date** | DATE | NO | Trading/price date | Date range: 2000-01-01 to present |
| **Ticker** | VARCHAR(50) | NO | Commodity ticker | Custom tickers for Vietnamese fertilizers |
| **Price** | DECIMAL(18,4) | YES | Price value (VND) | Numeric values, typically in millions VND |
| **Product_type** | VARCHAR(50) | YES | Fertilizer type | • 'DAP' (Diammonium Phosphate)<br>• 'NPK' (Nitrogen-Phosphorus-Potassium)<br>• 'Urea'<br>• 'Potash' |
| **Brand** | NVARCHAR(100) | YES | Manufacturer/brand | • 'Đình Vũ'<br>• 'Vân Thiên Hóa'<br>• 'Bình Điền'<br>• 'Cà Mau'<br>• 'Phú Mỹ' |
| **Specification** | VARCHAR(50) | YES | Chemical composition | • '61%', '64%' (for DAP)<br>• '16-16-8+13S' (for NPK)<br>• '16-16-8+TE' (trace elements)<br>• '46%' (for Urea) |
| **Created_date** | DATETIME | YES | Record creation timestamp | Default: GETDATE() |

---

### 7. Livestock Table
**Purpose**: Vietnamese and Chinese hog/livestock pricing  
**Primary Key**: (Price_date, ISNULL(Ticker, ISNULL(Category, 'Unknown')), ISNULL(Region, 'Unknown'))  
**Record Count**: ~31,000

| Field | Data Type | Nullable | Description | Possible Values |
|-------|-----------|----------|-------------|-----------------|
| **Price_date** | DATE | NO | Trading/price date | Date range: 2019-01-02 to present |
| **Ticker** | VARCHAR(50) | YES | Commodity ticker (China data) | • 'LHDF4 Comdty' (China Hog Future)<br>• 'JCIAPGDN Index' (China Hog Price Index)<br>• NULL (for Vietnamese data) |
| **Category** | NVARCHAR(100) | YES | Vietnamese hog categories | • 'Hog_corporate_North'<br>• 'Hog_farmer_North'<br>• 'Hog_corporate_Middle'<br>• 'Hog_farmer_Middle'<br>• 'Hog_corporate_South'<br>• 'Hog_farmer_South'<br>• 'Hog_corporate_20kg_[Region]'<br>• 'Hog_corporate_baby_pig_6_7kg_[Region]'<br>• 'Hog_farmer_baby_pig_7_9kg_South' |
| **Region** | VARCHAR(50) | YES | Geographic region | • 'North'<br>• 'Middle'<br>• 'South'<br>• 'China'<br>• 'Unknown' (default for NULLs) |
| **Price_low** | DECIMAL(18,2) | YES | Daily low price (VND/kg) | Numeric values, e.g., 45000.00 |
| **Price_high** | DECIMAL(18,2) | YES | Daily high price (VND/kg) | Numeric values, e.g., 48000.00 |
| **Price_average** | DECIMAL(18,2) | YES | Daily average price (VND/kg) | Calculated from low/high |
| **Price** | DECIMAL(18,4) | YES | Single price (China data) | Used for Chinese futures/indices |
| **Currency** | VARCHAR(10) | YES | Price currency | • 'VND' (Vietnamese data)<br>• 'CNY' (Chinese data)<br>• 'USD' (futures) |
| **Created_date** | DATETIME | YES | Record creation timestamp | Default: GETDATE() |

---

### 8. Shipping_Freight Table
**Purpose**: Shipping and freight indices (Baltic indices)  
**Primary Key**: (Price_date, Ticker)  
**Foreign Key**: Ticker → Commodity_Master(Ticker)  
**Record Count**: ~37,000

| Field | Data Type | Nullable | Description | Possible Values |
|-------|-----------|----------|-------------|-----------------|
| **Price_date** | DATE | NO | Index date | Date range: 2000-01-01 to present |
| **Ticker** | VARCHAR(50) | NO | Index ticker | • 'BDIY Index' (Baltic Dry Index)<br>• 'BHSI Index' (Baltic Handysize)<br>• 'BIDY Index' (Baltic Dirty Tanker)<br>• 'BITY Index' (Baltic Clean Tanker) |
| **Price** | DECIMAL(18,4) | YES | Index value | Numeric index values, e.g., 1250.0000 |
| **Index_type** | VARCHAR(50) | YES | Index category | • 'dry_bulk'<br>• 'tanker_dirty'<br>• 'tanker_clean'<br>• 'handysize' |
| **Created_date** | DATETIME | YES | Record creation timestamp | Default: GETDATE() |

---

### 9. Fishery Table
**Purpose**: Vietnamese fishery export transaction data  
**Primary Key**: (Transaction_date, Company, Market, ISNULL(Product_category, 'Unknown'))  
**Computed Fields**: Price_spread, Margin_pct  
**Record Count**: ~2,000

| Field | Data Type | Nullable | Description | Possible Values |
|-------|-----------|----------|-------------|-----------------|
| **Transaction_date** | DATE | NO | Transaction date | Date range: 2020-12-29 to present |
| **Company** | VARCHAR(50) | NO | Exporting company | • 'VHC' (Vinh Hoan Corp)<br>• 'IDI' (I.D.I International)<br>• 'ANV' (Nam Viet Corp) |
| **Market** | VARCHAR(50) | NO | Export destination | • 'China'<br>• 'USA'<br>• 'EU'<br>• 'Total' (aggregate) |
| **Product_category** | VARCHAR(50) | YES | Product type | • 'Pangasius'<br>• 'Shrimp'<br>• 'Other seafood'<br>• 'Unknown' (default for NULLs) |
| **Volume** | INT | YES | Export volume (tons) | Numeric values, e.g., 1500, 2300 |
| **Value** | BIGINT | YES | Export value (USD) | Large numeric values, e.g., 5000000 |
| **Selling_price** | DECIMAL(18,4) | YES | Price per unit (USD/kg) | Numeric values, e.g., 3.5000 |
| **Input_price** | DECIMAL(18,4) | YES | Cost per unit (USD/kg) | Numeric values, e.g., 2.8000 |
| **Price_spread** | COMPUTED | - | Selling_price - Input_price | Auto-calculated, e.g., 0.7000 |
| **Margin_pct** | COMPUTED | - | (Price_spread / Input_price) * 100 | Auto-calculated percentage |
| **Currency** | VARCHAR(10) | YES | Transaction currency | Default: 'USD' |
| **Created_date** | DATETIME | YES | Record creation timestamp | Default: GETDATE() |

---

## AVIATION SECTOR TABLES

### 10. Aviation_Airfare Table
**Purpose**: Flight ticket pricing data with advance booking periods  
**Primary Key**: (Date, Airline, Route, Flight_time, Booking_period)  
**Record Count**: ~990,000

| Field | Data Type | Nullable | Description | Possible Values |
|-------|-----------|----------|-------------|-----------------|
| **Date** | DATE | NO | Departure date | Date range: Historical to present |
| **Airline** | VARCHAR(50) | NO | Airline name | • 'Vietnam Airlines'<br>• 'VietJet Air'<br>• 'Bamboo Airways'<br>• 'Pacific Airlines' |
| **Route** | VARCHAR(20) | NO | Flight route code | Format: XXX-YYY<br>Examples:<br>• 'SGN-HAN' (Saigon-Hanoi)<br>• 'HAN-DAD' (Hanoi-Da Nang)<br>• 'SGN-PQC' (Saigon-Phu Quoc)<br>• 'HAN-SGN' (Hanoi-Saigon)<br>Total: 14 major routes |
| **Flight_time** | VARCHAR(10) | NO | Scheduled departure time | Format: HH:MM<br>Examples: '06:30', '10:45', '16:55', '21:15' |
| **Booking_period** | VARCHAR(10) | NO | Advance booking period | • '1W' (1 week advance)<br>• '1M' (1 month advance)<br>• '1Q' (1 quarter/3 months advance) |
| **Fare** | DECIMAL(12,2) | NO | Ticket price (VND) | Numeric values, e.g., 1250000.00 |
| **Created_date** | DATETIME | YES | Record creation timestamp | Default: GETDATE() |

---

### 11. Aviation_Operations Table
**Purpose**: Airline operational metrics and performance indicators  
**Primary Key**: (Date, Period_type, Airline, Metric_type, Traffic_type)  
**Check Constraint**: CK_Aviation_Traffic_Type  
**Record Count**: ~2,500

| Field | Data Type | Nullable | Description | Possible Values |
|-------|-----------|----------|-------------|-----------------|
| **Date** | DATE | NO | Reporting date | Date range: Monthly or quarterly data |
| **Period_type** | VARCHAR(20) | NO | Reporting period | • 'Monthly'<br>• 'Quarterly' |
| **Airline** | VARCHAR(50) | NO | Airline name | • 'Vietnam Airlines'<br>• 'VietJet'<br>• 'Bamboo'<br>• 'Pacific'<br>• 'Vietravel'<br>• 'VASCO' |
| **Metric_type** | VARCHAR(50) | NO | Performance metric | • 'Flight_count' - Number of flights<br>• 'OTP' - On-time performance<br>• 'Load_factor' - Seat utilization<br>• 'Aircraft_count' - Fleet size<br>• 'Passengers' - Passenger volume<br>• 'Market_share' - Market percentage |
| **Traffic_type** | VARCHAR(20) | NO | Traffic classification | **Constrained values:**<br>• 'Domestic' (for Passengers, Market_share)<br>• 'International' (for Passengers, Market_share)<br>• 'N/A' (for all other metrics) |
| **Metric_value** | DECIMAL(18,3) | YES | Metric value | Examples:<br>• Flight_count: 1250.000<br>• OTP: 85.500 (percentage)<br>• Load_factor: 78.250 (percentage)<br>• Aircraft_count: 45.000<br>• Passengers: 2.450 (millions)<br>• Market_share: 35.750 (percentage) |
| **Unit** | VARCHAR(20) | YES | Measurement unit | • 'flights'<br>• 'percentage'<br>• 'millions'<br>• 'aircraft' |
| **Created_date** | DATETIME | YES | Record creation timestamp | Default: GETDATE() |

**CHECK Constraint Details:**
```sql
CONSTRAINT CK_Aviation_Traffic_Type CHECK (
    (Metric_type IN ('Market_share', 'Passengers') 
     AND Traffic_type IN ('Domestic', 'International'))
    OR 
    (Metric_type NOT IN ('Market_share', 'Passengers') 
     AND Traffic_type = 'N/A')
)
```

---

### 12. Aviation_Revenue Table
**Purpose**: Quarterly airline revenue breakdown by type  
**Primary Key**: (Year, Quarter, Airline, Revenue_type)  
**Record Count**: ~160

| Field | Data Type | Nullable | Description | Possible Values |
|-------|-----------|----------|-------------|-----------------|
| **Date** | DATE | NO | Quarter start date | First day of quarter |
| **Year** | INT | NO | Fiscal year | 2020, 2021, 2022, 2023, 2024 |
| **Quarter** | INT | NO | Fiscal quarter | • 1 (Q1: Jan-Mar)<br>• 2 (Q2: Apr-Jun)<br>• 3 (Q3: Jul-Sep)<br>• 4 (Q4: Oct-Dec) |
| **Airline** | VARCHAR(50) | NO | Airline code | • 'HVN' (Vietnam Airlines)<br>• 'VJC' (VietJet Air) |
| **Revenue_type** | VARCHAR(50) | NO | Revenue category | • 'Passenger' - Ticket revenue<br>• 'Cargo' - Freight revenue<br>• 'Ancillary' - Additional services<br>• 'Charter' - Charter flights |
| **Revenue_amount** | DECIMAL(18,2) | YES | Revenue value | Numeric values in billions VND |
| **Currency** | VARCHAR(10) | YES | Revenue currency | Default: 'VND' |
| **Created_date** | DATETIME | YES | Record creation timestamp | Default: GETDATE() |

---

### 13. Aviation_Market Table
**Purpose**: Market-wide aviation metrics and indicators  
**Primary Key**: (Date, Metric_type, Metric_name)  
**Record Count**: ~250

| Field | Data Type | Nullable | Description | Possible Values |
|-------|-----------|----------|-------------|-----------------|
| **Date** | DATE | NO | Measurement date | Monthly data points |
| **Metric_type** | VARCHAR(50) | NO | Metric category | • 'Throughput' - Passenger traffic<br>• 'Fuel_price' - Aviation fuel costs<br>• 'Passenger_mix' - Country breakdown |
| **Metric_name** | VARCHAR(100) | NO | Specific metric | **For Throughput:**<br>• 'Domestic'<br>• 'International'<br>• 'Total'<br><br>**For Fuel_price:**<br>• 'Singapore_fuel' (Jet fuel Singapore)<br><br>**For Passenger_mix:**<br>• 'China'<br>• 'Korea'<br>• 'Japan'<br>• 'Thailand'<br>• 'USA'<br>• 'Others' |
| **Metric_value** | DECIMAL(18,3) | YES | Metric value | Examples:<br>• Throughput: 5.250 (million passengers)<br>• Fuel_price: 95.750 (USD/barrel)<br>• Passenger_mix: 25.500 (percentage) |
| **Unit** | VARCHAR(20) | YES | Measurement unit | • 'passengers'<br>• 'USD/barrel'<br>• 'percentage'<br>• 'millions' |
| **Created_date** | DATETIME | YES | Record creation timestamp | Default: GETDATE() |

---

## Data Quality Notes

### NULL Handling in Primary Keys
- All PRIMARY KEY columns use ISNULL() function with default values ('Unknown', 'N/A') to prevent NULL conflicts
- This ensures data integrity while allowing flexibility in data import

### Computed Fields
- **Fishery.Price_spread**: Automatically calculated as (Selling_price - Input_price)
- **Fishery.Margin_pct**: Automatically calculated as ((Selling_price - Input_price) / Input_price * 100)
- These fields are PERSISTED for query performance

### Data Validation Rules
1. **Aviation_Operations.Traffic_type**: Must be 'Domestic' or 'International' for Passengers/Market_share metrics, 'N/A' for others
2. **All Date fields**: Must be valid SQL DATE format (YYYY-MM-DD)
3. **Price fields**: DECIMAL(18,4) allows for 14 digits before decimal and 4 after
4. **Foreign Keys**: All Ticker values must exist in Commodity_Master table

### Index Strategy
- Primary keys create clustered indexes automatically
- Additional non-clustered indexes on frequently queried columns (Ticker, Date, Airline)
- INCLUDE columns added for covering indexes to improve query performance

---

## Migration and Update Patterns

### Data Sources
- **Commodity data**: Excel files (Steel_priceDB.xlsx, UreDB.xlsx)
- **Aviation data**: Pickle files (.pkl format)
- **Update frequency**: Varies by sector (daily for commodities, monthly/quarterly for aviation)

### Duplicate Prevention
- Composite primary keys prevent duplicate records
- Migration scripts check existing data before insertion
- Update operations use MERGE or INSERT...WHERE NOT EXISTS patterns

### Performance Considerations
- Bulk insert operations using `fast_executemany=True`
- Batch processing in 10,000 record chunks
- Indexed foreign key columns for JOIN performance