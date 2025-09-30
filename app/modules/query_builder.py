"""
SQL Query Builder for Commodity Database
Generates dynamic SQL queries for fetching commodity data from multiple tables

IMPORTANT: Handles different price column names across tables:
- Most tables use 'Price' column
- Livestock table uses 'Average_Price' column  
- Fishery table uses 'Selling_Price' column
All are aliased to 'Price' in query results for consistency.

EXCLUSIONS: Calculated/derived tickers are excluded from price movement calculations
but retained in the data for display purposes.
"""

from typing import List, Optional, Dict, Any
import pandas as pd


class CommodityQueryBuilder:
    """Builds SQL queries for commodity data retrieval"""
    
    # Calculated/derived tickers to exclude from price movement calculations
    # These are user-calculated values, not actual commodity price data
    # Identified by keywords: "Moving Avg", "Margin", "Cost", "EAF"
    CALCULATED_TICKERS = {
        'China HRC Margin',
        'China HRC Moving Avg 15',
        'China LS Moving Avg 15', 
        'Cash Cost Moving Avg 15',
        'HPG FE',  # Calculated spread/basis
        'Cash Cost',
        'VN HRC Moving Avg 15',
        'VN LS Moving Avg 15',
        'Cost EAF',
        'EAF',
        'EAF Moving Avg 15'
    }
    
    # Mapping of sectors to their respective table names
    SECTOR_TABLE_MAP = {
        'Agricultural': 'Agricultural',
        'Chemicals': 'Chemicals',
        'Energy': 'Energy',
        'Fertilizer': 'Fertilizer',
        # 'Livestock': 'Livestock',  # TEMPORARILY DISABLED - needs special processing
        'Metals': 'Metals',
        'Shipping_Freight': 'Shipping_Freight',
        'Steel': 'Steel',
        'Aviation': None,  # Special handling - multiple tables
        # 'Fishery': 'Fishery'  # TEMPORARILY DISABLED - needs special processing
    }
    
    @staticmethod
    def build_price_query(
        sectors: Optional[List[str]] = None,
        tickers: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> str:
        """
        Build query to fetch price data from multiple sector tables
        
        Args:
            sectors: List of sectors to include (None = all sectors)
            tickers: List of specific tickers to include (None = all tickers)
            start_date: Start date for data (format: 'YYYY-MM-DD')
            end_date: End date for data (format: 'YYYY-MM-DD')
            
        Returns:
            str: SQL query string
        """
        # Determine which tables to query
        if sectors:
            tables_to_query = [
                CommodityQueryBuilder.SECTOR_TABLE_MAP[sector] 
                for sector in sectors 
                if sector in CommodityQueryBuilder.SECTOR_TABLE_MAP 
                and CommodityQueryBuilder.SECTOR_TABLE_MAP[sector] is not None
            ]
        else:
            # Query all tables except Aviation
            tables_to_query = [
                table for table in CommodityQueryBuilder.SECTOR_TABLE_MAP.values() 
                if table is not None
            ]
        
        if not tables_to_query:
            return "SELECT NULL as Ticker, NULL as Date, NULL as Price WHERE 1=0"
        
        # Build UNION query for all selected tables
        union_queries = []
        
        # NOTE: Fishery and Livestock tables are temporarily disabled in SECTOR_TABLE_MAP
        # They require special processing due to data structure differences
        
        for table in tables_to_query:
            # Handle special cases for different tables
            if table == 'Fishery':
                query = f"""
                SELECT 
                    Company + '_' + Market as Ticker,
                    Date,
                    Selling_Price as Price
                FROM {table}
                WHERE 1=1
                """
            elif table == 'Livestock':
                query = f"""
                SELECT 
                    Ticker,
                    Date,
                    Average_Price as Price
                FROM {table}
                WHERE 1=1
                """
            else:
                query = f"""
                SELECT 
                    Ticker,
                    Date,
                    Price
                FROM {table}
                WHERE 1=1
                """
            
            # Add date filters
            if start_date:
                query += f" AND Date >= '{start_date}'"
            if end_date:
                query += f" AND Date <= '{end_date}'"
            
            # Add ticker filter
            if tickers:
                ticker_list = "', '".join(tickers)
                if table == 'Fishery':
                    query += f" AND Company + '_' + Market IN ('{ticker_list}')"
                else:
                    query += f" AND Ticker IN ('{ticker_list}')"
            
            union_queries.append(query)
        
        # Combine all queries with UNION ALL
        final_query = " UNION ALL ".join(union_queries)
        
        # Add ordering
        final_query = f"""
        SELECT * FROM (
            {final_query}
        ) AS CombinedData
        ORDER BY Date DESC, Ticker
        """
        
        return final_query
    
    @staticmethod
    def is_calculated_ticker(ticker_name: str) -> bool:
        """
        Check if a ticker is a calculated/derived value based on naming patterns.
        
        Args:
            ticker_name: The ticker or commodity name to check
            
        Returns:
            bool: True if ticker is calculated/derived, False otherwise
        """
        if not ticker_name:
            return False
            
        # Check if in explicit list
        if ticker_name in CommodityQueryBuilder.CALCULATED_TICKERS:
            return True
            
        # Check for patterns that indicate calculated values
        calculated_patterns = [
            'Moving Avg',
            'Margin',
            'Cost',
            'EAF',
            'HPG FE'  # Specific calculated spread
        ]
        
        for pattern in calculated_patterns:
            if pattern in ticker_name:
                return True
                
        return False
    
    @staticmethod
    def get_calculated_tickers() -> set:
        """
        Returns the set of calculated/derived tickers that should be excluded
        from price movement calculations.
        
        Returns:
            set: Set of calculated ticker names
        """
        return CommodityQueryBuilder.CALCULATED_TICKERS.copy()
    
    @staticmethod
    def build_ticker_list_query(sectors: Optional[List[str]] = None) -> str:
        """
        Build query to get list of available tickers
        
        Args:
            sectors: List of sectors to include (None = all sectors)
            
        Returns:
            str: SQL query string
        """
        if sectors:
            sector_list = "', '".join(sectors)
            where_clause = f"WHERE Sector IN ('{sector_list}')"
        else:
            where_clause = ""
        
        query = f"""
        SELECT 
            Ticker,
            Name,
            Sector,
            Data_Source
        FROM Ticker_Reference
        {where_clause}
            {'AND' if where_clause else 'WHERE'} Active = 1
        ORDER BY Sector, Name
        """
        
        return query
    
    @staticmethod
    def build_latest_prices_query(sectors: Optional[List[str]] = None) -> str:
        """
        Build query to get latest prices for all commodities
        
        Args:
            sectors: List of sectors to include
            
        Returns:
            str: SQL query string
        """
        # Get tables to query
        if sectors:
            tables_to_query = [
                CommodityQueryBuilder.SECTOR_TABLE_MAP[sector] 
                for sector in sectors 
                if sector in CommodityQueryBuilder.SECTOR_TABLE_MAP 
                and CommodityQueryBuilder.SECTOR_TABLE_MAP[sector] is not None
            ]
        else:
            tables_to_query = [
                table for table in CommodityQueryBuilder.SECTOR_TABLE_MAP.values() 
                if table is not None
            ]
        
        if not tables_to_query:
            return "SELECT NULL as Ticker, NULL as Date, NULL as Price WHERE 1=0"
        
        # Build subqueries for each table to get latest prices
        union_queries = []
        
        # NOTE: Fishery and Livestock tables are temporarily disabled in SECTOR_TABLE_MAP
        
        for table in tables_to_query:
            if table == 'Fishery':
                query = f"""
                SELECT 
                    t1.Company + '_' + t1.Market as Ticker,
                    t1.Date,
                    t1.Selling_Price as Price
                FROM {table} t1
                INNER JOIN (
                    SELECT Company, Market, MAX(Date) as MaxDate
                    FROM {table}
                    GROUP BY Company, Market
                ) t2 ON t1.Company = t2.Company 
                    AND t1.Market = t2.Market 
                    AND t1.Date = t2.MaxDate
                """
            elif table == 'Livestock':
                query = f"""
                SELECT 
                    t1.Ticker,
                    t1.Date,
                    t1.Average_Price as Price
                FROM {table} t1
                INNER JOIN (
                    SELECT Ticker, MAX(Date) as MaxDate
                    FROM {table}
                    WHERE Average_Price IS NOT NULL
                    GROUP BY Ticker
                ) t2 ON t1.Ticker = t2.Ticker AND t1.Date = t2.MaxDate
                """
            else:
                query = f"""
                SELECT 
                    t1.Ticker,
                    t1.Date,
                    t1.Price
                FROM {table} t1
                INNER JOIN (
                    SELECT Ticker, MAX(Date) as MaxDate
                    FROM {table}
                    WHERE Price IS NOT NULL
                    GROUP BY Ticker
                ) t2 ON t1.Ticker = t2.Ticker AND t1.Date = t2.MaxDate
                """
            
            union_queries.append(query)
        
        # Combine all queries
        final_query = " UNION ALL ".join(union_queries)
        
        return final_query
    
    @staticmethod
    def build_date_range_query() -> str:
        """
        Build query to get available date range across all tables
        
        Returns:
            str: SQL query string
        """
        tables = [
            table for table in CommodityQueryBuilder.SECTOR_TABLE_MAP.values() 
            if table is not None
        ]
        
        union_queries = []
        for table in tables:
            query = f"""
            SELECT MIN(Date) as MinDate, MAX(Date) as MaxDate
            FROM {table}
            """
            union_queries.append(query)
        
        final_query = f"""
        SELECT 
            MIN(MinDate) as MinDate,
            MAX(MaxDate) as MaxDate
        FROM (
            {" UNION ALL ".join(union_queries)}
        ) AS DateRanges
        """
        
        return final_query
    
    @staticmethod
    def build_aviation_metrics_query(
        metric_type: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> str:
        """
        Build query for aviation-specific metrics
        
        Args:
            metric_type: Type of aviation metric ('airfare', 'operations', 'revenue', 'market')
            start_date: Start date for data
            end_date: End date for data
            
        Returns:
            str: SQL query string
        """
        date_filter = "WHERE 1=1"
        if start_date:
            date_filter += f" AND Date >= '{start_date}'"
        if end_date:
            date_filter += f" AND Date <= '{end_date}'"
        
        if metric_type == 'airfare':
            query = f"""
            SELECT 
                Date,
                Airline + '_' + Route + '_' + Booking_period as Ticker,
                Fare as Price
            FROM Aviation_Airfare
            {date_filter}
            ORDER BY Date DESC
            """
        elif metric_type == 'operations':
            query = f"""
            SELECT 
                Date,
                Airline + '_' + Metric_type as Ticker,
                Metric_value as Price
            FROM Aviation_Operations
            {date_filter}
            ORDER BY Date DESC
            """
        elif metric_type == 'revenue':
            query = f"""
            SELECT 
                Date,
                Airline + '_' + Revenue_type as Ticker,
                Revenue_amount as Price
            FROM Aviation_Revenue
            {date_filter}
            ORDER BY Date DESC
            """
        elif metric_type == 'market':
            query = f"""
            SELECT 
                Date,
                Metric_type + '_' + Metric_name as Ticker,
                Metric_value as Price
            FROM Aviation_Market
            {date_filter}
            ORDER BY Date DESC
            """
        else:
            query = "SELECT NULL as Date, NULL as Ticker, NULL as Price WHERE 1=0"
        
        return query