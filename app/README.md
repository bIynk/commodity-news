# SQL Server Dashboard

## Overview
Real-time commodity market dashboard displaying 200+ commodity prices from Microsoft SQL Server database.

## Setup
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up database connection:
   ```bash
   # Windows (PowerShell)
   $env:DC_DB_STRING="DRIVER={ODBC Driver 17 for SQL Server};SERVER=your_server;DATABASE=CommodityDB;UID=your_user;PWD=your_password"

   # Linux/Mac
   export DC_DB_STRING="DRIVER={ODBC Driver 17 for SQL Server};SERVER=your_server;DATABASE=CommodityDB;UID=your_user;PWD=your_password"
   ```

3. Run the dashboard:
   ```bash
   streamlit run main.py
   ```

## Features
- Real-time data from MS SQL Server
- 200+ commodities across 11 sectors
- Advanced filtering (sector/nation/commodity)
- KPI metrics with frequency-aware staleness filter (7-day for daily, 14-day for weekly)
- Frequency-aware Z-scores (daily vs weekly)
- AG-Grid with conditional formatting
- Performance charts with stock impact labels

## Database
Connects to Microsoft SQL Server. See `/unified/docs/database/schema.md` for database structure.

## Documentation
See `/unified/docs/technical/sql-dashboard.md` for detailed documentation.