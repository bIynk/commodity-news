"""
Microsoft SQL Server Database Integration
Following existing CommodityDB schema patterns with composite keys
Designed to be extensible to all commodity sectors
"""

import pyodbc
import os
import json
import logging
from datetime import datetime, date
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote_plus
from sqlalchemy import create_engine
import pandas as pd

logger = logging.getLogger(__name__)


class MSSQLCommodityDatabase:
    """
    SQL Server database interface following existing CommodityDB schema patterns.
    Uses composite primary keys instead of identity columns.
    Designed to be extensible to all commodity sectors.
    """
    
    # Current ticker mapping for Steel sector
    # This can be extended to include Energy, Metals, Agricultural, etc.
    TICKER_MAPPING = {
        # Steel sector mappings
        'iron ore': 'IOECAU62 Index',
        'coking coal': 'IAC1 COMB Comdty',
        'scrap steel': 'CNMUSHAN Index',
        'steel rebar': 'CDSPDRAV Index',
        'steel HRC': 'VN HRC',
        
        # Future extensions (commented for now)
        # 'wti crude': 'CL1 COMB Comdty',
        # 'brent crude': 'CO1 Comdty',
        # 'natural gas': 'NG1 COMB Comdty',
        # 'gold': 'XAU BGNT Curncy',
        # 'silver': 'XAG BGNT Curncy',
        # 'copper': 'HGH4 COMB Comdty',
        # 'wheat': 'W51 COMB Comdty',
        # 'corn': 'C 1 COMB Comdty',
    }
    
    # Table mapping by sector (for future extensibility)
    SECTOR_TABLE_MAPPING = {
        'Steel': 'Steel',
        'Energy': 'Energy',
        'Metals': 'Metals',
        'Agricultural': 'Agricultural',
        'Fertilizer': 'Fertilizer',
        'Livestock': 'Livestock',
        'Shipping': 'Shipping_Freight',
        'Fishery': 'Fishery'
    }
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize SQL Server connection
        
        Args:
            connection_string: Optional connection string, otherwise read from environment
        """
        self.conn_string = connection_string or os.getenv('MSSQL_CONNECTION_STRING')
        if not self.conn_string:
            raise ValueError(
                "MSSQL_CONNECTION_STRING not found. Please set it in .env file or pass it directly."
            )
        
        # Create SQLAlchemy engine for pandas operations
        try:
            params = quote_plus(self.conn_string)
            self.engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
            logger.info("SQL Server connection engine created successfully")
        except Exception as e:
            logger.error(f"Failed to create SQL Server engine: {e}")
            raise
    
    def get_connection(self):
        """Get a new database connection"""
        try:
            return pyodbc.connect(self.conn_string)
        except Exception as e:
            logger.error(f"Failed to connect to SQL Server: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                logger.info("SQL Server connection test successful")
                return result[0] == 1
        except Exception as e:
            logger.error(f"SQL Server connection test failed: {e}")
            return False
    
    def get_ticker(self, ai_commodity_name: str) -> Optional[str]:
        """
        Map AI commodity name to SQL Server ticker
        
        Args:
            ai_commodity_name: Commodity name from AI system
            
        Returns:
            Corresponding ticker in SQL Server or None
        """
        return self.TICKER_MAPPING.get(ai_commodity_name.lower())
    
    def get_commodity_info(self, ticker: str) -> Optional[Dict]:
        """
        Get commodity information from Commodity_Master table
        
        Args:
            ticker: Commodity ticker
            
        Returns:
            Dictionary with commodity information
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    Commodity_id,
                    Ticker,
                    Commodity_name,
                    Sector,
                    Subsector,
                    Unit,
                    Is_active
                FROM Commodity_Master
                WHERE Ticker = ?
            """, (ticker,))
            
            row = cursor.fetchone()
            if row:
                columns = [column[0] for column in cursor.description]
                return dict(zip(columns, row))
        return None
    
    def save_ai_analysis(self, commodity_name: str, analysis_data: Dict, 
                        timeframe: str) -> bool:
        """
        Save AI analysis following existing composite key pattern
        No auto-generated IDs, use (Analysis_date, Ticker, Timeframe) as key
        
        Args:
            commodity_name: AI commodity name
            analysis_data: Analysis results from Perplexity AI
            timeframe: Analysis timeframe ('1 week' or '1 month')
            
        Returns:
            True if successful, False otherwise
        """
        ticker = self.get_ticker(commodity_name)
        if not ticker:
            logger.error(f"No ticker mapping for commodity: {commodity_name}")
            return False
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if record already exists for today
                cursor.execute("""
                    SELECT 1 FROM Commodity_AI_Analysis 
                    WHERE Analysis_date = CAST(GETDATE() AS DATE)
                    AND Ticker = ? 
                    AND Timeframe = ?
                """, (ticker, timeframe))
                
                if cursor.fetchone():
                    # Update existing record
                    cursor.execute("""
                        UPDATE Commodity_AI_Analysis 
                        SET Current_price = ?,
                            Price_change = ?,
                            Trend = ?,
                            Key_drivers = ?,
                            Recent_news = ?,
                            Source_urls = ?,
                            Raw_response = ?,
                            Created_date = GETDATE()
                        WHERE Analysis_date = CAST(GETDATE() AS DATE)
                        AND Ticker = ? 
                        AND Timeframe = ?
                    """, (
                        analysis_data.get('current_price'),
                        analysis_data.get('price_change'),
                        analysis_data.get('trend'),
                        json.dumps(analysis_data.get('key_drivers', [])),
                        json.dumps(analysis_data.get('recent_news', [])),
                        json.dumps(analysis_data.get('source_urls', [])),
                        analysis_data.get('raw_response'),
                        ticker,
                        timeframe
                    ))
                    logger.info(f"Updated existing AI analysis for {ticker}")
                else:
                    # Insert new record
                    cursor.execute("""
                        INSERT INTO Commodity_AI_Analysis 
                        (Analysis_date, Ticker, Timeframe, Current_price, 
                         Price_change, Trend, Key_drivers, Recent_news, 
                         Source_urls, Raw_response)
                        VALUES (CAST(GETDATE() AS DATE), ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ticker,
                        timeframe,
                        analysis_data.get('current_price'),
                        analysis_data.get('price_change'),
                        analysis_data.get('trend'),
                        json.dumps(analysis_data.get('key_drivers', [])),
                        json.dumps(analysis_data.get('recent_news', [])),
                        json.dumps(analysis_data.get('source_urls', [])),
                        analysis_data.get('raw_response')
                    ))
                    logger.info(f"Inserted new AI analysis for {ticker}")
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving AI analysis: {e}")
            return False
    
    def log_query(self, commodity_name: str, timeframe: str, 
                  success: bool, response_time_ms: Optional[int] = None, 
                  cached: bool = False, error_msg: Optional[str] = None) -> bool:
        """
        Log AI query attempts following composite key pattern
        
        Args:
            commodity_name: AI commodity name
            timeframe: Query timeframe
            success: Whether query was successful
            response_time_ms: API response time in milliseconds
            cached: Whether result was from cache
            error_msg: Error message if failed
            
        Returns:
            True if logged successfully
        """
        ticker = self.get_ticker(commodity_name)
        if not ticker:
            return False
        
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO Commodity_AI_Queries 
                    (Query_date, Ticker, Timeframe, Query_timestamp, 
                     Success, API_response_time_ms, Cached_from_db, Error_message)
                    VALUES (CAST(GETDATE() AS DATE), ?, ?, GETDATE(), ?, ?, ?, ?)
                """, (
                    ticker, timeframe, success, response_time_ms, 
                    cached, error_msg[:500] if error_msg else None
                ))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error logging query: {e}")
            return False
    
    def get_today_analysis(self, commodity_name: str, timeframe: str = '1 week') -> Optional[Dict]:
        """
        Get today's analysis using composite key
        
        Args:
            commodity_name: AI commodity name
            timeframe: Analysis timeframe
            
        Returns:
            Analysis data or None
        """
        ticker = self.get_ticker(commodity_name)
        if not ticker:
            return None
        
        query = """
            SELECT 
                Analysis_date,
                Ticker,
                Timeframe,
                Current_price,
                Price_change,
                Trend,
                Key_drivers,
                Recent_news,
                Source_urls,
                Created_date
            FROM Commodity_AI_Analysis 
            WHERE Analysis_date = CAST(GETDATE() AS DATE)
            AND Ticker = ?
            AND Timeframe = ?
        """
        
        try:
            df = pd.read_sql_query(query, self.engine, params=(ticker, timeframe))
            
            if not df.empty:
                result = df.iloc[0].to_dict()
                # Parse JSON fields
                for field in ['Key_drivers', 'Recent_news', 'Source_urls']:
                    if result.get(field):
                        try:
                            result[field] = json.loads(result[field])
                        except:
                            pass
                return result
        except Exception as e:
            logger.error(f"Error getting today's analysis: {e}")
        
        return None
    
    def get_all_today_results(self, timeframe: str = "1 week") -> List[Dict]:
        """
        Get all commodities' results from today's cache
        Compatible with existing SQLite interface
        
        Args:
            timeframe: Timeframe to filter by
            
        Returns:
            List of today's cached results
        """
        query = """
            SELECT 
                ai.Ticker,
                cm.Commodity_name,
                cm.Sector,
                ai.Analysis_date,
                ai.Timeframe,
                ai.Current_price,
                ai.Price_change,
                ai.Trend,
                ai.Key_drivers,
                ai.Recent_news,
                ai.Source_urls,
                ai.Created_date
            FROM Commodity_AI_Analysis ai
            INNER JOIN Commodity_Master cm ON ai.Ticker = cm.Ticker
            WHERE ai.Analysis_date = CAST(GETDATE() AS DATE)
            AND ai.Timeframe = ?
            ORDER BY cm.Sector, cm.Commodity_name
        """
        
        try:
            df = pd.read_sql_query(query, self.engine, params=(timeframe,))
            
            results = []
            for _, row in df.iterrows():
                result = row.to_dict()
                # Parse JSON fields
                for field in ['Key_drivers', 'Recent_news', 'Source_urls']:
                    if result.get(field):
                        try:
                            result[field] = json.loads(result[field])
                        except:
                            pass
                
                # Format to match expected structure
                formatted_result = {
                    "success": True,
                    "commodity": self._get_ai_name_from_ticker(result['Ticker']),
                    "timeframe": result['Timeframe'],
                    "data": {
                        "current_price": result.get('Current_price'),
                        "price_change": result.get('Price_change'),
                        "trend": result.get('Trend'),
                        "key_drivers": result.get('Key_drivers', []),
                        "recent_news": result.get('Recent_news', []),
                        "sources": result.get('Source_urls', []),
                        "source_urls": result.get('Source_urls', []),
                        "cached_from_db": True,
                        "cache_timestamp": result.get('Created_date')
                    },
                    "timestamp": result.get('Created_date')
                }
                results.append(formatted_result)
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting all today's results: {e}")
            return []
    
    def _get_ai_name_from_ticker(self, ticker: str) -> str:
        """Reverse map ticker to AI commodity name"""
        for ai_name, db_ticker in self.TICKER_MAPPING.items():
            if db_ticker == ticker:
                return ai_name
        return ticker  # Return ticker if no mapping found
    
    def get_historical_prices(self, commodity_name: str, days: int = 30) -> pd.DataFrame:
        """
        Fetch historical prices from appropriate sector table
        This method is extensible to all sectors
        
        Args:
            commodity_name: AI commodity name
            days: Number of days of history
            
        Returns:
            DataFrame with price history
        """
        ticker = self.get_ticker(commodity_name)
        if not ticker:
            return pd.DataFrame()
        
        # Get commodity info to determine sector
        commodity_info = self.get_commodity_info(ticker)
        if not commodity_info:
            return pd.DataFrame()
        
        sector = commodity_info.get('Sector')
        table_name = self.SECTOR_TABLE_MAPPING.get(sector, 'Steel')
        
        # Build query based on sector
        if table_name in ['Steel', 'Energy', 'Metals', 'Agricultural']:
            query = f"""
                SELECT 
                    Price_date,
                    Price,
                    CASE 
                        WHEN '{table_name}' = 'Steel' THEN Price_type
                        WHEN '{table_name}' = 'Energy' THEN Product_type
                        WHEN '{table_name}' = 'Metals' THEN Metal_type
                        WHEN '{table_name}' = 'Agricultural' THEN Product_type
                        ELSE NULL
                    END as Type
                FROM {table_name}
                WHERE Ticker = ? 
                AND Price_date >= DATEADD(day, -?, GETDATE())
                ORDER BY Price_date DESC
            """
        else:
            # For other sectors, adapt query as needed
            query = f"""
                SELECT 
                    Price_date,
                    Price
                FROM {table_name}
                WHERE Ticker = ? 
                AND Price_date >= DATEADD(day, -?, GETDATE())
                ORDER BY Price_date DESC
            """
        
        try:
            return pd.read_sql_query(query, self.engine, params=(ticker, days))
        except Exception as e:
            logger.error(f"Error fetching historical prices: {e}")
            return pd.DataFrame()
    
    def get_price_history(self, commodity_name: str, days: int = 30) -> List[Tuple[str, float]]:
        """
        Get price history for a commodity (compatible with SQLite interface)
        
        Args:
            commodity_name: Name of commodity
            days: Number of days of history
            
        Returns:
            List of (date, price) tuples
        """
        df = self.get_historical_prices(commodity_name, days)
        if df.empty:
            return []
        
        # Convert to list of tuples
        return [(row['Price_date'].strftime('%Y-%m-%d'), row['Price']) 
                for _, row in df.iterrows()]
    
    def save_query_results(self, results: List[Dict], timeframe: str) -> bool:
        """
        Save multiple query results (compatible with SQLite interface)
        
        Args:
            results: List of query results from Perplexity
            timeframe: Timeframe used for the query
            
        Returns:
            Success status
        """
        all_success = True
        for result in results:
            if result.get("success") and result.get("data"):
                commodity_name = result.get("commodity")
                analysis_data = result.get("data")
                
                success = self.save_ai_analysis(commodity_name, analysis_data, timeframe)
                if not success:
                    all_success = False
                
                # Log the query
                self.log_query(
                    commodity_name,
                    timeframe,
                    success=True,
                    cached=analysis_data.get('cached_from_db', False)
                )
        
        return all_success
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """
        Clean up old data from database
        
        Args:
            days_to_keep: Number of days of data to retain
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cutoff_date = f"DATEADD(day, -{days_to_keep}, GETDATE())"
                
                # Clean AI analysis
                cursor.execute(f"""
                    DELETE FROM Commodity_AI_Analysis
                    WHERE Created_date < {cutoff_date}
                """)
                
                analysis_deleted = cursor.rowcount
                
                # Clean query logs
                cursor.execute(f"""
                    DELETE FROM Commodity_AI_Queries
                    WHERE Created_date < {cutoff_date}
                """)
                
                queries_deleted = cursor.rowcount
                
                conn.commit()
                
                logger.info(
                    f"Cleaned up {analysis_deleted} analysis records and "
                    f"{queries_deleted} query log records"
                )
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")


# Export the class
__all__ = ['MSSQLCommodityDatabase']