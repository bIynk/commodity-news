"""
Migration Script for SQL Server Database Setup
Creates tables and migrates data from SQLite to SQL Server
"""

import os
import sys
import pyodbc
import sqlite3
import json
import logging
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class MSSQLMigration:
    """Handle migration to Microsoft SQL Server"""
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize migration with connection string
        
        Args:
            connection_string: Optional SQL Server connection string
        """
        self.conn_string = connection_string or os.getenv('MSSQL_CONNECTION_STRING')
        if not self.conn_string:
            raise ValueError(
                "MSSQL_CONNECTION_STRING not found. Please set it in .env file:\n"
                "Example: MSSQL_CONNECTION_STRING=Driver={ODBC Driver 17 for SQL Server};"
                "Server=your-server;Database=CommodityDB;Uid=username;Pwd=password;"
            )
        
        logger.info("Migration initialized with SQL Server connection")
    
    def get_connection(self):
        """Get SQL Server connection"""
        try:
            return pyodbc.connect(self.conn_string)
        except Exception as e:
            logger.error(f"Failed to connect to SQL Server: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                logger.info("✅ SQL Server connection successful")
                return True
        except Exception as e:
            logger.error(f"❌ SQL Server connection failed: {e}")
            return False
    
    def create_ai_tables(self) -> bool:
        """
        Create AI-related tables in SQL Server
        Following existing composite key patterns
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Check if tables already exist
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME = 'Commodity_AI_Analysis'
                """)
                
                if cursor.fetchone()[0] > 0:
                    logger.info("Table Commodity_AI_Analysis already exists")
                    return True
                
                logger.info("Creating Commodity_AI_Analysis table...")
                
                # Create Commodity_AI_Analysis table
                cursor.execute("""
                    CREATE TABLE Commodity_AI_Analysis (
                        -- Composite key fields
                        Analysis_date DATE NOT NULL,
                        Ticker VARCHAR(50) NOT NULL,
                        Timeframe VARCHAR(20) NOT NULL,
                        
                        -- Analysis data
                        Current_price DECIMAL(18,4) NULL,
                        Price_change VARCHAR(50) NULL,
                        Trend VARCHAR(20) NULL,
                        
                        -- JSON fields for structured data
                        Key_drivers NVARCHAR(MAX) NULL,
                        Recent_news NVARCHAR(MAX) NULL,
                        Source_urls NVARCHAR(MAX) NULL,
                        
                        -- Raw response for debugging
                        Raw_response NVARCHAR(MAX) NULL,
                        
                        -- Audit field
                        Created_date DATETIME NULL DEFAULT GETDATE(),
                        
                        -- Primary key
                        CONSTRAINT PK_Commodity_AI_Analysis 
                            PRIMARY KEY (Analysis_date, Ticker, Timeframe),
                        
                        -- Foreign key to Commodity_Master
                        CONSTRAINT FK_Commodity_AI_Analysis_Ticker 
                            FOREIGN KEY (Ticker) REFERENCES Commodity_Master(Ticker)
                    )
                """)
                
                # Create index
                cursor.execute("""
                    CREATE INDEX IX_Commodity_AI_Analysis_Date 
                    ON Commodity_AI_Analysis(Analysis_date DESC, Ticker)
                """)
                
                logger.info("✅ Created Commodity_AI_Analysis table")
                
                # Create Commodity_AI_Queries table
                logger.info("Creating Commodity_AI_Queries table...")
                
                cursor.execute("""
                    CREATE TABLE Commodity_AI_Queries (
                        -- Composite key fields
                        Query_date DATE NOT NULL,
                        Ticker VARCHAR(50) NOT NULL,
                        Timeframe VARCHAR(20) NOT NULL,
                        Query_timestamp DATETIME NOT NULL,
                        
                        -- Query metadata
                        Success BIT NULL,
                        API_response_time_ms INT NULL,
                        Cached_from_db BIT NULL DEFAULT 0,
                        Error_message NVARCHAR(500) NULL,
                        
                        -- Audit field
                        Created_date DATETIME NULL DEFAULT GETDATE(),
                        
                        -- Primary key
                        CONSTRAINT PK_Commodity_AI_Queries 
                            PRIMARY KEY (Query_date, Ticker, Timeframe, Query_timestamp),
                        
                        -- Foreign key to Commodity_Master
                        CONSTRAINT FK_Commodity_AI_Queries_Ticker 
                            FOREIGN KEY (Ticker) REFERENCES Commodity_Master(Ticker)
                    )
                """)
                
                # Create index
                cursor.execute("""
                    CREATE INDEX IX_Commodity_AI_Queries_Date 
                    ON Commodity_AI_Queries(Query_date DESC, Success)
                """)
                
                logger.info("✅ Created Commodity_AI_Queries table")
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            return False
    
    def ensure_commodity_tickers(self) -> bool:
        """
        Ensure required commodity tickers exist in Commodity_Master
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Tickers needed for AI system
                tickers_to_ensure = [
                    ('IOECAU62 Index', 'Iron Ore 62% Fe CFR China', 'Steel', 'Iron Ore', 'USD/ton'),
                    ('IAC1 COMB Comdty', 'Australian Coking Coal Future', 'Energy', 'Coking Coal', 'USD/ton'),
                    ('CNMUSHAN Index', 'China Scrap Steel', 'Steel', 'Scrap', 'USD/ton'),
                    ('CDSPDRAV Index', 'China Steel Rebar Average', 'Steel', 'Long Products', 'USD/ton'),
                    ('VN HRC', 'Vietnam Hot Rolled Coil', 'Steel', 'Flat Products', 'USD/ton')
                ]
                
                for ticker, name, sector, subsector, unit in tickers_to_ensure:
                    # Check if ticker exists
                    cursor.execute(
                        "SELECT COUNT(*) FROM Commodity_Master WHERE Ticker = ?",
                        (ticker,)
                    )
                    
                    if cursor.fetchone()[0] == 0:
                        # Insert ticker
                        cursor.execute("""
                            INSERT INTO Commodity_Master 
                            (Ticker, Commodity_name, Sector, Subsector, Unit, Is_active, Created_date)
                            VALUES (?, ?, ?, ?, ?, 1, GETDATE())
                        """, (ticker, name, sector, subsector, unit))
                        
                        logger.info(f"✅ Added ticker: {ticker}")
                    else:
                        logger.info(f"✓ Ticker already exists: {ticker}")
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error ensuring commodity tickers: {e}")
            return False
    
    def migrate_from_sqlite(self, sqlite_path: str = "data/commodity_data.db") -> bool:
        """
        Migrate existing data from SQLite to SQL Server
        
        Args:
            sqlite_path: Path to SQLite database
        """
        if not os.path.exists(sqlite_path):
            logger.info("No SQLite database found to migrate")
            return True
        
        try:
            logger.info(f"Migrating data from SQLite: {sqlite_path}")
            
            # Mapping from SQLite commodity names to SQL Server tickers
            ticker_mapping = {
                'iron ore': 'IOECAU62 Index',
                'coking coal': 'IAC1 COMB Comdty',
                'scrap steel': 'CNMUSHAN Index',
                'steel rebar': 'CDSPDRAV Index',
                'steel HRC': 'VN HRC'
            }
            
            # Connect to SQLite
            sqlite_conn = sqlite3.connect(sqlite_path)
            sqlite_cursor = sqlite_conn.cursor()
            
            # Get query results from SQLite
            sqlite_cursor.execute("""
                SELECT 
                    commodity_name,
                    timeframe,
                    DATE(query_timestamp) as query_date,
                    current_price,
                    price_change,
                    trend,
                    key_drivers,
                    recent_news,
                    sources,
                    raw_response,
                    created_at
                FROM query_results
                WHERE success = 1
                ORDER BY query_timestamp DESC
            """)
            
            rows = sqlite_cursor.fetchall()
            logger.info(f"Found {len(rows)} records to migrate")
            
            if rows:
                with self.get_connection() as mssql_conn:
                    mssql_cursor = mssql_conn.cursor()
                    
                    migrated_count = 0
                    for row in rows:
                        commodity_name = row[0]
                        ticker = ticker_mapping.get(commodity_name)
                        
                        if not ticker:
                            logger.warning(f"No ticker mapping for: {commodity_name}")
                            continue
                        
                        # Check if record already exists
                        mssql_cursor.execute("""
                            SELECT COUNT(*) FROM Commodity_AI_Analysis
                            WHERE Analysis_date = ?
                            AND Ticker = ?
                            AND Timeframe = ?
                        """, (row[2], ticker, row[1]))
                        
                        if mssql_cursor.fetchone()[0] == 0:
                            # Insert record
                            mssql_cursor.execute("""
                                INSERT INTO Commodity_AI_Analysis
                                (Analysis_date, Ticker, Timeframe, Current_price,
                                 Price_change, Trend, Key_drivers, Recent_news,
                                 Source_urls, Raw_response, Created_date)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                row[2],  # query_date
                                ticker,
                                row[1],  # timeframe
                                row[3],  # current_price
                                row[4],  # price_change
                                row[5],  # trend
                                row[6],  # key_drivers (already JSON)
                                row[7],  # recent_news (already JSON)
                                row[8],  # sources
                                row[9],  # raw_response
                                row[10]  # created_at
                            ))
                            migrated_count += 1
                    
                    mssql_conn.commit()
                    logger.info(f"✅ Migrated {migrated_count} records to SQL Server")
            
            sqlite_conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Error migrating from SQLite: {e}")
            return False
    
    def create_stored_procedures(self) -> bool:
        """Create useful stored procedures"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Drop existing procedure if it exists
                cursor.execute("""
                    IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'sp_GetCommodityAnalysis')
                        DROP PROCEDURE sp_GetCommodityAnalysis
                """)
                
                # Create stored procedure for getting combined view
                cursor.execute("""
                    CREATE PROCEDURE sp_GetCommodityAnalysis
                        @Ticker VARCHAR(50),
                        @Timeframe VARCHAR(20) = '1 week'
                    AS
                    BEGIN
                        SET NOCOUNT ON;
                        
                        SELECT 
                            cm.Commodity_name,
                            cm.Sector,
                            cm.Subsector,
                            cm.Unit,
                            s.Price as Latest_historical_price,
                            s.Price_date as Latest_price_date,
                            ai.Analysis_date,
                            ai.Current_price as AI_current_price,
                            ai.Price_change,
                            ai.Trend,
                            ai.Key_drivers,
                            ai.Recent_news,
                            ai.Source_urls
                        FROM Commodity_Master cm
                        LEFT JOIN (
                            SELECT TOP 1 Price, Price_date, Ticker
                            FROM Steel 
                            WHERE Ticker = @Ticker 
                            ORDER BY Price_date DESC
                        ) s ON cm.Ticker = s.Ticker
                        LEFT JOIN Commodity_AI_Analysis ai 
                            ON cm.Ticker = ai.Ticker 
                            AND ai.Analysis_date = CAST(GETDATE() AS DATE)
                            AND ai.Timeframe = @Timeframe
                        WHERE cm.Ticker = @Ticker;
                    END
                """)
                
                logger.info("✅ Created stored procedure: sp_GetCommodityAnalysis")
                
                # Create cleanup procedure
                cursor.execute("""
                    IF EXISTS (SELECT * FROM sys.procedures WHERE name = 'sp_CleanOldAIData')
                        DROP PROCEDURE sp_CleanOldAIData
                """)
                
                cursor.execute("""
                    CREATE PROCEDURE sp_CleanOldAIData
                        @DaysToKeep INT = 90
                    AS
                    BEGIN
                        SET NOCOUNT ON;
                        
                        DECLARE @CutoffDate DATE = DATEADD(day, -@DaysToKeep, GETDATE());
                        
                        DELETE FROM Commodity_AI_Analysis
                        WHERE Created_date < @CutoffDate;
                        
                        DELETE FROM Commodity_AI_Queries
                        WHERE Created_date < @CutoffDate;
                    END
                """)
                
                logger.info("✅ Created stored procedure: sp_CleanOldAIData")
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error creating stored procedures: {e}")
            return False
    
    def run_migration(self):
        """Run complete migration process"""
        logger.info("=" * 60)
        logger.info("Starting SQL Server Migration")
        logger.info("=" * 60)
        
        # Step 1: Test connection
        if not self.test_connection():
            logger.error("Migration aborted: Cannot connect to SQL Server")
            return False
        
        # Step 2: Create tables
        logger.info("\n📋 Creating AI tables...")
        if not self.create_ai_tables():
            logger.error("Migration aborted: Failed to create tables")
            return False
        
        # Step 3: Ensure commodity tickers
        logger.info("\n🏷️ Ensuring commodity tickers...")
        if not self.ensure_commodity_tickers():
            logger.error("Migration aborted: Failed to ensure tickers")
            return False
        
        # Step 4: Migrate existing data
        logger.info("\n📦 Migrating existing data...")
        self.migrate_from_sqlite()
        
        # Step 5: Create stored procedures
        logger.info("\n⚙️ Creating stored procedures...")
        self.create_stored_procedures()
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Migration completed successfully!")
        logger.info("=" * 60)
        
        # Print configuration instructions
        logger.info("\n📝 Next steps:")
        logger.info("1. Set DATABASE_TYPE=mssql in your .env file")
        logger.info("2. Ensure MSSQL_CONNECTION_STRING is set in .env")
        logger.info("3. Run the dashboard: streamlit run app.py")
        
        return True


if __name__ == "__main__":
    # Check if connection string is provided as argument
    conn_string = None
    if len(sys.argv) > 1:
        conn_string = sys.argv[1]
    
    try:
        migration = MSSQLMigration(conn_string)
        success = migration.run_migration()
        
        if success:
            logger.info("\n✨ Migration successful! The database is ready for use.")
            sys.exit(0)
        else:
            logger.error("\n❌ Migration failed. Please check the errors above.")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"\n❌ Migration failed: {e}")
        sys.exit(1)