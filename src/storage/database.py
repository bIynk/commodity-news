"""
Database Storage Module
SQLite database for storing commodity query results and historical data
"""

import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import os
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CommodityDatabase:
    """SQLite database for commodity data storage"""
    
    def __init__(self, db_path: str = "data/commodity_data.db"):
        """
        Initialize database connection
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _sanitize_commodity_name(self, name: str) -> str:
        """
        Sanitize commodity name to prevent SQL injection
        
        Args:
            name: Commodity name to sanitize
            
        Returns:
            Sanitized commodity name
            
        Raises:
            ValueError: If name is invalid
        """
        if not name or not isinstance(name, str):
            raise ValueError("Invalid commodity name: must be a non-empty string")
        
        # Allow only alphanumeric, spaces, hyphens, and underscores
        if not re.match(r'^[a-zA-Z0-9\s\-_]+$', name):
            raise ValueError(f"Invalid commodity name format: {name}")
        
        # Additional length check
        if len(name) > 100:
            raise ValueError(f"Commodity name too long: {name}")
        
        return name.strip()
    
    def _sanitize_timeframe(self, timeframe: str) -> str:
        """Sanitize and validate timeframe"""
        valid_timeframes = ["1 week", "1 month"]
        if timeframe not in valid_timeframes:
            raise ValueError(f"Invalid timeframe: {timeframe}. Must be one of {valid_timeframes}")
        return timeframe
    
    def _init_database(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create commodity info table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commodities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    unit TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create query results table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    commodity_name TEXT NOT NULL,
                    timeframe TEXT NOT NULL,
                    query_timestamp TIMESTAMP NOT NULL,
                    success BOOLEAN NOT NULL,
                    current_price TEXT,
                    price_change TEXT,
                    trend TEXT,
                    key_drivers TEXT,
                    recent_news TEXT,
                    sources TEXT,
                    raw_response TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (commodity_name) REFERENCES commodities(name)
                )
            """)
            
            # Create price history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    commodity_name TEXT NOT NULL,
                    price_value REAL,
                    price_unit TEXT,
                    price_date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (commodity_name) REFERENCES commodities(name)
                )
            """)
            
            # Create indices for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_query_results_commodity 
                ON query_results(commodity_name, query_timestamp DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_price_history_commodity 
                ON price_history(commodity_name, price_date DESC)
            """)
            
            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
    
    def save_query_results(
        self,
        results: List[Dict],
        timeframe: str
    ) -> bool:
        """
        Save query results to database
        
        Args:
            results: List of query results from Perplexity
            timeframe: Timeframe used for the query
        
        Returns:
            Success status
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for result in results:
                    # First ensure commodity exists in commodities table
                    if result.get("data"):
                        self._ensure_commodity_exists(
                            cursor,
                            result.get("commodity"),
                            result["data"].get("display_name"),
                            result["data"].get("category"),
                            result["data"].get("unit")
                        )
                    
                    # Prepare data for insertion
                    data = result.get("data", {})
                    
                    cursor.execute("""
                        INSERT INTO query_results (
                            commodity_name,
                            timeframe,
                            query_timestamp,
                            success,
                            current_price,
                            price_change,
                            trend,
                            key_drivers,
                            recent_news,
                            sources,
                            raw_response
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        result.get("commodity"),
                        timeframe,
                        result.get("timestamp", datetime.utcnow().isoformat()),
                        result.get("success", False),
                        data.get("current_price"),
                        data.get("price_change"),
                        data.get("trend"),
                        json.dumps(data.get("key_drivers", [])),
                        json.dumps(data.get("recent_news", [])),
                        json.dumps(data.get("sources", [])),
                        data.get("raw_response")
                    ))
                    
                    # Also save to price history if price is available
                    if data.get("current_price"):
                        self._save_price_history(
                            cursor,
                            result.get("commodity"),
                            data.get("current_price"),
                            data.get("unit", "USD")
                        )
                
                conn.commit()
                logger.info(f"Saved {len(results)} query results to database")
                return True
                
        except Exception as e:
            logger.error(f"Error saving query results: {e}")
            return False
    
    def _ensure_commodity_exists(
        self,
        cursor,
        name: str,
        display_name: Optional[str],
        category: Optional[str],
        unit: Optional[str]
    ):
        """Ensure commodity exists in commodities table"""
        cursor.execute(
            "SELECT id FROM commodities WHERE name = ?",
            (name,)
        )
        
        if not cursor.fetchone():
            cursor.execute("""
                INSERT OR IGNORE INTO commodities (name, display_name, category, unit)
                VALUES (?, ?, ?, ?)
            """, (
                name,
                display_name or name,
                category or "Unknown",
                unit or "USD"
            ))
    
    def _save_price_history(
        self,
        cursor,
        commodity_name: str,
        price_str: str,
        unit: str
    ):
        """Extract and save price to history"""
        try:
            # Extract numeric value from price string
            import re
            match = re.search(r'([\d,]+(?:\.\d+)?)', price_str)
            if match:
                price_value = float(match.group(1).replace(',', ''))
                
                cursor.execute("""
                    INSERT INTO price_history (commodity_name, price_value, price_unit, price_date)
                    VALUES (?, ?, ?, ?)
                """, (
                    commodity_name,
                    price_value,
                    unit,
                    datetime.utcnow().date()
                ))
        except Exception as e:
            logger.error(f"Error saving price history: {e}")
    
    def get_today_results(
        self,
        commodity_name: Optional[str] = None,
        timeframe: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get today's query results from database
        
        Args:
            commodity_name: Filter by commodity name
            timeframe: Filter by timeframe
        
        Returns:
            Query result if found for today, None otherwise
        """
        # Validate inputs
        if commodity_name:
            commodity_name = self._sanitize_commodity_name(commodity_name)
        if timeframe:
            timeframe = self._sanitize_timeframe(timeframe)
            
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            today = datetime.utcnow().date()
            
            query = """
                SELECT * FROM query_results
                WHERE DATE(query_timestamp) = DATE(?)
                AND success = 1
            """
            params = [today]
            
            if commodity_name:
                query += " AND commodity_name = ?"
                params.append(commodity_name)
            
            if timeframe:
                query += " AND timeframe = ?"
                params.append(timeframe)
            
            query += " ORDER BY query_timestamp DESC LIMIT 1"
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            if row:
                result = dict(row)
                # Parse JSON fields
                for field in ['key_drivers', 'recent_news', 'sources']:
                    if result.get(field):
                        try:
                            result[field] = json.loads(result[field])
                        except:
                            pass
                
                # Format as Perplexity response format
                return {
                    "success": True,
                    "commodity": result['commodity_name'],
                    "timeframe": result['timeframe'],
                    "data": {
                        "current_price": result.get('current_price'),
                        "price_change": result.get('price_change'),
                        "trend": result.get('trend'),
                        "key_drivers": result.get('key_drivers', []),
                        "recent_news": result.get('recent_news', []),
                        "sources": result.get('sources', []),
                        "raw_response": result.get('raw_response'),
                        "cached_from_db": True,
                        "cache_timestamp": result.get('query_timestamp')
                    },
                    "timestamp": result.get('query_timestamp')
                }
            
            return None
    
    def get_all_today_results(
        self,
        timeframe: str = "1 week"
    ) -> List[Dict]:
        """
        Get all commodities' results from today's cache
        
        Args:
            timeframe: Timeframe to filter by
        
        Returns:
            List of today's cached results
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            today = datetime.utcnow().date()
            
            cursor.execute("""
                SELECT * FROM query_results
                WHERE DATE(query_timestamp) = DATE(?)
                AND timeframe = ?
                AND success = 1
                ORDER BY commodity_name
            """, (today, timeframe))
            
            results = []
            for row in cursor.fetchall():
                result = dict(row)
                # Parse JSON fields
                for field in ['key_drivers', 'recent_news', 'sources']:
                    if result.get(field):
                        try:
                            result[field] = json.loads(result[field])
                        except:
                            pass
                
                # Format as Perplexity response
                formatted_result = {
                    "success": True,
                    "commodity": result['commodity_name'],
                    "timeframe": result['timeframe'],
                    "data": {
                        "current_price": result.get('current_price'),
                        "price_change": result.get('price_change'),
                        "trend": result.get('trend'),
                        "key_drivers": result.get('key_drivers', []),
                        "recent_news": result.get('recent_news', []),
                        "sources": result.get('sources', []),
                        "raw_response": result.get('raw_response'),
                        "cached_from_db": True,
                        "cache_timestamp": result.get('query_timestamp')
                    },
                    "timestamp": result.get('query_timestamp')
                }
                results.append(formatted_result)
            
            return results
    
    def get_latest_results(
        self,
        commodity_name: Optional[str] = None,
        timeframe: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Get latest query results from database
        
        Args:
            commodity_name: Filter by commodity name
            timeframe: Filter by timeframe
            limit: Maximum number of results
        
        Returns:
            List of query results
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = """
                SELECT * FROM query_results
                WHERE 1=1
            """
            params = []
            
            if commodity_name:
                query += " AND commodity_name = ?"
                params.append(commodity_name)
            
            if timeframe:
                query += " AND timeframe = ?"
                params.append(timeframe)
            
            query += " ORDER BY query_timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            results = []
            
            for row in cursor.fetchall():
                result = dict(row)
                # Parse JSON fields
                for field in ['key_drivers', 'recent_news', 'sources']:
                    if result.get(field):
                        try:
                            result[field] = json.loads(result[field])
                        except:
                            pass
                results.append(result)
            
            return results
    
    def get_price_history(
        self,
        commodity_name: str,
        days: int = 30
    ) -> List[Tuple[str, float]]:
        """
        Get price history for a commodity
        
        Args:
            commodity_name: Name of commodity
            days: Number of days of history
        
        Returns:
            List of (date, price) tuples
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cutoff_date = (datetime.utcnow() - timedelta(days=days)).date()
            
            cursor.execute("""
                SELECT price_date, price_value
                FROM price_history
                WHERE commodity_name = ? AND price_date >= ?
                ORDER BY price_date ASC
            """, (commodity_name, cutoff_date))
            
            return cursor.fetchall()
    
    def get_trend_analysis(
        self,
        commodity_name: str,
        days: int = 7
    ) -> Dict:
        """
        Get trend analysis for a commodity
        
        Args:
            commodity_name: Name of commodity
            days: Number of days to analyze
        
        Returns:
            Trend analysis dictionary
        """
        price_history = self.get_price_history(commodity_name, days)
        
        if len(price_history) < 2:
            return {
                "trend": "unknown",
                "change_percent": 0,
                "data_points": len(price_history)
            }
        
        # Calculate trend
        first_price = price_history[0][1]
        last_price = price_history[-1][1]
        change_percent = ((last_price - first_price) / first_price) * 100
        
        if change_percent > 2:
            trend = "bullish"
        elif change_percent < -2:
            trend = "bearish"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "change_percent": round(change_percent, 2),
            "first_price": first_price,
            "last_price": last_price,
            "data_points": len(price_history)
        }
    
    def cleanup_old_data(self, days_to_keep: int = 90):
        """
        Clean up old data from database
        
        Args:
            days_to_keep: Number of days of data to retain
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
                
                # Clean query results
                cursor.execute("""
                    DELETE FROM query_results
                    WHERE created_at < ?
                """, (cutoff_date,))
                
                deleted_queries = cursor.rowcount
                
                # Clean price history
                cursor.execute("""
                    DELETE FROM price_history
                    WHERE created_at < ?
                """, (cutoff_date,))
                
                deleted_prices = cursor.rowcount
                
                conn.commit()
                
                logger.info(
                    f"Cleaned up {deleted_queries} query results and "
                    f"{deleted_prices} price history records"
                )
                
                # Vacuum to reclaim space
                cursor.execute("VACUUM")
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def export_to_csv(
        self,
        output_path: str,
        commodity_name: Optional[str] = None
    ):
        """
        Export data to CSV file
        
        Args:
            output_path: Path for output CSV file
            commodity_name: Optional filter by commodity
        """
        import csv
        
        results = self.get_latest_results(commodity_name=commodity_name, limit=1000)
        
        if not results:
            logger.warning("No data to export")
            return
        
        with open(output_path, 'w', newline='') as csvfile:
            fieldnames = [
                'commodity_name', 'timeframe', 'query_timestamp',
                'current_price', 'price_change', 'trend'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                writer.writerow({
                    k: result.get(k) for k in fieldnames
                })
        
        logger.info(f"Exported {len(results)} records to {output_path}")