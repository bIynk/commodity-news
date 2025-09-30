from sqlalchemy import create_engine, text, Engine
from sqlalchemy.pool import QueuePool
import pandas as pd
import streamlit as st
from typing import Optional, Dict, Any
import urllib.parse
import os
import re

def get_connection_string() -> str:
    """
    Get SQL Server connection string from environment variable or st.secrets
    
    For local development: Set DC_DB_STRING environment variable
    For deployment: Configure in Streamlit secrets
    
    Returns:
        str: ODBC connection string
    """
    # First priority: Check direct environment variable (for local development)
    connection_string = os.getenv('DC_DB_STRING')
    if connection_string:
        return connection_string
    
    # Second priority: Try to get from Streamlit secrets (for deployment)
    try:
        if 'SQL_CONNECTION_STRING' in st.secrets:
            return st.secrets['SQL_CONNECTION_STRING']
        
        # Build connection string from individual parameters in secrets
        driver = st.secrets.get('SQL_SERVER_DRIVER', 'ODBC Driver 17 for SQL Server')
        server = st.secrets['SQL_SERVER_HOST']
        database = st.secrets.get('SQL_SERVER_DATABASE', 'CommodityDB')
        username = st.secrets['SQL_SERVER_USERNAME']
        password = st.secrets['SQL_SERVER_PASSWORD']
        port = st.secrets.get('SQL_SERVER_PORT', '1433')
        trust_cert = st.secrets.get('SQL_SERVER_TRUST_CERTIFICATE', 'yes')
        
        return f"""
            DRIVER={{{driver}}};
            SERVER={server},{port};
            DATABASE={database};
            UID={username};
            PWD={password};
            TrustServerCertificate={trust_cert}
        """
    except (KeyError, AttributeError):
        # If neither environment variable nor secrets are available, raise error
        raise ValueError(
            "Database connection string not found. Please set up either:\n"
            "1. For local development: Set DC_DB_STRING environment variable\n"
            "   Windows (cmd): set DC_DB_STRING=\"DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=CommodityDB;UID=user;PWD=pass\"\n"
            "   Windows (PowerShell): $env:DC_DB_STRING=\"DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=CommodityDB;UID=user;PWD=pass\"\n"
            "   Linux/Mac: export DC_DB_STRING=\"DRIVER={ODBC Driver 17 for SQL Server};SERVER=localhost;DATABASE=CommodityDB;UID=user;PWD=pass\"\n"
            "2. For deployment: Configure SQL_CONNECTION_STRING in Streamlit Cloud secrets"
        )


class DatabaseConnection:
    """
    Manages SQL Server database connections with connection pooling.
    Supports both pyodbc (local development) and pymssql (Streamlit Cloud).
    """

    def __init__(self, connection_string: str = None):
        """
        Initialize database connection

        Args:
            connection_string: Connection string (ODBC format or pymssql URL). If None, gets from config
        """
        self.conn_string = connection_string or get_connection_string()
        self.engine = None
        self.connection = None
        self._initialize_engine()

    def _parse_connection_string(self, conn_str: str) -> Dict[str, str]:
        """
        Parse connection string in ODBC or key-value format.

        Args:
            conn_str: Connection string to parse

        Returns:
            Dict with parsed parameters: host, port, database, username, password
        """
        params = {}

        # Remove extra whitespace and newlines
        conn_str = re.sub(r'\s+', ' ', conn_str.strip())

        # Parse key=value pairs
        # Handle both semicolon and newline separators
        pairs = re.split(r'[;\n]', conn_str)

        for pair in pairs:
            pair = pair.strip()
            if '=' in pair:
                key, value = pair.split('=', 1)
                key = key.strip().upper()
                value = value.strip().strip('{}')  # Remove curly braces if present

                if key == 'SERVER':
                    # Parse SERVER=host,port or SERVER=host:port or SERVER=host
                    if ',' in value:
                        # Format: host,port
                        host, port = value.split(',', 1)
                        params['host'] = host.strip()
                        params['port'] = port.strip()
                    elif ':' in value:
                        # Format: host:port
                        host, port = value.rsplit(':', 1)
                        params['host'] = host.strip()
                        params['port'] = port.strip()
                    else:
                        # Format: host (no port specified)
                        params['host'] = value
                        params['port'] = '1433'  # Default SQL Server port
                elif key == 'DATABASE':
                    params['database'] = value
                elif key in ('UID', 'USER', 'USERNAME'):
                    params['username'] = value
                elif key in ('PWD', 'PASSWORD'):
                    params['password'] = value

        return params

    def _create_engine(self) -> Engine:
        """
        Create SQLAlchemy engine from connection string.
        Automatically detects and uses appropriate driver (pymssql for cloud, pyodbc for local).

        Returns:
            Engine: SQLAlchemy engine
        """
        try:
            # First, try to parse the connection string
            if 'DRIVER=' in self.conn_string.upper() or '=' in self.conn_string:
                # Parse ODBC or key-value format
                params = self._parse_connection_string(self.conn_string)

                # Validate required parameters
                if not all(key in params for key in ['host', 'database', 'username', 'password']):
                    missing = [k for k in ['host', 'database', 'username', 'password'] if k not in params]
                    raise ValueError(f"Missing required connection parameters: {missing}")

                if 'url' in params:
                    # Already in pymssql format
                    connection_url = params['url']
                else:
                    # Build pymssql connection URL
                    # URL encode password to handle special characters
                    password = urllib.parse.quote_plus(params['password'])
                    username = urllib.parse.quote_plus(params['username'])

                    # Ensure port is just the number (remove any host part if still present)
                    port = params.get('port', '1433')
                    host = params['host']

                    # Double-check: if host still contains ':', split it again
                    if ':' in host:
                        host, port = host.rsplit(':', 1)

                    connection_url = (
                        f"mssql+pymssql://{username}:{password}@"
                        f"{host}:{port}/"
                        f"{params['database']}"
                    )

                    # Add query parameters for Azure SQL
                    connection_url += "?charset=utf8"
            else:
                # Assume it's already a properly formatted URL
                connection_url = self.conn_string

            # Create engine with connection pooling
            engine = create_engine(
                connection_url,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,  # Verify connections before using
                pool_recycle=3600,   # Recycle connections after 1 hour
                echo=False,          # Set to True for SQL debugging
                connect_args={
                    "timeout": 30,   # Connection timeout in seconds
                }
            )

            return engine

        except Exception as e:
            # If pymssql fails, try pyodbc as fallback (for local development)
            try:
                import pyodbc
                # URL encode the connection string for SQLAlchemy
                params = urllib.parse.quote_plus(self.conn_string)
                # Create SQLAlchemy connection URL for pyodbc
                connection_url = f"mssql+pyodbc:///?odbc_connect={params}"

                # Create engine with connection pooling
                engine = create_engine(
                    connection_url,
                    poolclass=QueuePool,
                    pool_size=5,
                    max_overflow=10,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    echo=False,
                    fast_executemany=True
                )

                return engine
            except ImportError:
                # If pyodbc is not available, re-raise the original pymssql error
                raise Exception(
                    f"Failed to create database engine with pymssql: {str(e)}\n"
                    "pyodbc is also not available. Install either pymssql or pyodbc."
                )
            except Exception as pyodbc_error:
                # Re-raise the original pymssql error if pyodbc also fails
                raise Exception(
                    f"Failed to create database engine.\n"
                    f"pymssql error: {str(e)}\n"
                    f"pyodbc error: {str(pyodbc_error)}"
                )

    def _initialize_engine(self):
        """Initialize SQLAlchemy engine with automatic driver detection"""
        try:
            self.engine = self._create_engine()

            # Test connection
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                if result.scalar() != 1:
                    raise Exception("Connection test failed")

        except Exception as e:
            st.error(
                f"Failed to initialize database engine: {str(e)}\n\n"
                "Ensure either pymssql (for Streamlit Cloud) or pyodbc (for local development) is installed."
            )
            raise
    
    def test_connection(self) -> bool:
        """
        Test database connection
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.scalar() == 1
        except Exception as e:
            st.error(f"Database connection test failed: {str(e)}")
            return False
    
    def execute_query(self, query: str, params: Dict[str, Any] = None) -> pd.DataFrame:
        """
        Execute SQL query and return results as DataFrame
        
        Args:
            query: SQL query string
            params: Optional dictionary of query parameters
            
        Returns:
            pd.DataFrame: Query results
        """
        try:
            with self.engine.connect() as conn:
                if params:
                    result = pd.read_sql_query(text(query), conn, params=params)
                else:
                    result = pd.read_sql_query(query, conn)
                return result
        except Exception as e:
            st.error(f"Query execution failed: {str(e)}")
            raise
    
    def get_table_list(self) -> list:
        """
        Get list of all tables in the database
        
        Returns:
            list: List of table names
        """
        query = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
        """
        try:
            df = self.execute_query(query)
            return df['TABLE_NAME'].tolist()
        except:
            return []
    
    def get_sectors(self) -> list:
        """
        Get unique sectors from Ticker_Reference table
        
        Returns:
            list: List of unique sectors
        """
        query = """
        SELECT DISTINCT Sector 
        FROM Ticker_Reference 
        WHERE Active = 1 AND Sector IS NOT NULL
        AND Sector NOT IN ('Livestock', 'Fishery')  -- Temporarily exclude these sectors
        ORDER BY Sector
        """
        try:
            df = self.execute_query(query)
            return df['Sector'].tolist()
        except:
            # Fallback to hardcoded sectors if table doesn't exist (excluding disabled ones)
            return [
                'Agricultural', 'Chemicals', 'Energy', 'Fertilizer',
                'Metals', 'Shipping_Freight', 'Steel'
                # 'Livestock', 'Aviation', 'Fishery' -- Temporarily disabled
            ]
    
    def get_ticker_reference(self) -> pd.DataFrame:
        """
        Get ticker reference data
        
        Returns:
            pd.DataFrame: Ticker reference data with columns [Ticker, Name, Sector, Data_Source, Active]
        """
        query = """
        SELECT Ticker, Name, Sector, Data_Source, Active
        FROM Ticker_Reference
        WHERE Active = 1
        AND Sector NOT IN ('Livestock', 'Fishery')  -- Temporarily exclude these sectors
        ORDER BY Sector, Name
        """
        try:
            return self.execute_query(query)
        except:
            # Return empty DataFrame if table doesn't exist
            return pd.DataFrame(columns=['Ticker', 'Name', 'Sector', 'Data_Source', 'Active'])
    
    def close(self):
        """Close database connection"""
        if self.engine:
            self.engine.dispose()


@st.cache_resource
def get_db_connection(connection_string: str = None) -> DatabaseConnection:
    """
    Get cached database connection instance
    
    Args:
        connection_string: Optional ODBC connection string
        
    Returns:
        DatabaseConnection: Cached connection instance
    """
    return DatabaseConnection(connection_string)


def validate_connection_string(connection_string: str) -> tuple[bool, str]:
    """
    Validate SQL Server connection string format
    
    Args:
        connection_string: ODBC connection string
        
    Returns:
        tuple: (is_valid, error_message)
    """
    required_params = ['DRIVER', 'SERVER', 'DATABASE']
    
    # Check for required parameters
    for param in required_params:
        if param not in connection_string.upper():
            return False, f"Missing required parameter: {param}"
    
    # Try to establish connection
    try:
        db = DatabaseConnection(connection_string)
        if db.test_connection():
            db.close()
            return True, "Connection successful"
        else:
            return False, "Could not connect to database"
    except Exception as e:
        return False, str(e)