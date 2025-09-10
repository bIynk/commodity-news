"""
Centralized Logging Configuration
Provides consistent logging setup across the application
"""

import logging
import logging.handlers
import os
from pathlib import Path
from datetime import datetime
import json


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "logs/commodity_dashboard.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console_output: bool = True
):
    """
    Setup centralized logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        max_bytes: Maximum size of each log file
        backup_count: Number of backup files to keep
        console_output: Whether to output logs to console
    """
    # Create logs directory if it doesn't exist
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # File handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setFormatter(detailed_formatter)
    file_handler.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(file_handler)
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(simple_formatter)
        console_handler.setLevel(logging.INFO)  # Less verbose on console
        root_logger.addHandler(console_handler)
    
    # Configure specific loggers to prevent sensitive data logging
    
    # Reduce noise from external libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("streamlit").setLevel(logging.WARNING)
    
    # Prevent API key logging
    logging.getLogger("src.api.perplexity_client").addFilter(APIKeyFilter())
    
    # Log startup message
    root_logger.info(f"Logging initialized - Level: {log_level}, File: {log_file}")
    
    return root_logger


class APIKeyFilter(logging.Filter):
    """Filter to prevent API keys from being logged"""
    
    def filter(self, record):
        """Remove sensitive data from log records"""
        # List of sensitive patterns to mask
        sensitive_patterns = [
            'api_key', 'API_KEY', 'Bearer', 'Authorization',
            'password', 'secret', 'token', 'PERPLEXITY_API_KEY'
        ]
        
        # Check and mask sensitive data in the message
        if hasattr(record, 'msg'):
            msg = str(record.msg)
            for pattern in sensitive_patterns:
                if pattern.lower() in msg.lower():
                    # Mask the sensitive part
                    import re
                    # This regex will find values after these keys
                    msg = re.sub(
                        rf'({pattern}["\']?\s*[:=]\s*["\']?)([^"\'\s,}}]+)',
                        r'\1***REDACTED***',
                        msg,
                        flags=re.IGNORECASE
                    )
            record.msg = msg
        
        # Check and mask sensitive data in args
        if hasattr(record, 'args') and record.args:
            cleaned_args = []
            for arg in record.args:
                if isinstance(arg, str):
                    for pattern in sensitive_patterns:
                        if pattern.lower() in arg.lower():
                            arg = '***REDACTED***'
                            break
                cleaned_args.append(arg)
            record.args = tuple(cleaned_args)
        
        return True


class StructuredLogger:
    """Wrapper for structured logging with JSON output"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
    def log_event(
        self,
        event_type: str,
        message: str,
        level: str = "INFO",
        **kwargs
    ):
        """
        Log a structured event
        
        Args:
            event_type: Type of event (e.g., 'api_call', 'cache_hit', 'error')
            message: Human-readable message
            level: Log level
            **kwargs: Additional structured data
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "message": message,
            **kwargs
        }
        
        # Remove sensitive data
        for key in list(log_data.keys()):
            if any(sensitive in key.lower() for sensitive in ['key', 'token', 'secret', 'password']):
                log_data[key] = "***REDACTED***"
        
        log_func = getattr(self.logger, level.lower())
        log_func(json.dumps(log_data))
    
    def log_api_call(
        self,
        endpoint: str,
        method: str = "GET",
        duration_ms: float = 0,
        success: bool = True,
        status_code: int = None,
        error: str = None
    ):
        """Log API call with metrics"""
        self.log_event(
            "api_call",
            f"API call to {endpoint}",
            level="INFO" if success else "ERROR",
            endpoint=endpoint,
            method=method,
            duration_ms=duration_ms,
            success=success,
            status_code=status_code,
            error=error
        )
    
    def log_cache_access(
        self,
        cache_type: str,
        cache_key: str,
        hit: bool,
        latency_ms: float = 0
    ):
        """Log cache access"""
        self.log_event(
            "cache_access",
            f"Cache {'hit' if hit else 'miss'} for {cache_type}",
            level="DEBUG",
            cache_type=cache_type,
            cache_key=cache_key,
            hit=hit,
            latency_ms=latency_ms
        )
    
    def log_database_operation(
        self,
        operation: str,
        table: str,
        rows_affected: int = 0,
        duration_ms: float = 0,
        success: bool = True,
        error: str = None
    ):
        """Log database operation"""
        self.log_event(
            "database_operation",
            f"Database {operation} on {table}",
            level="INFO" if success else "ERROR",
            operation=operation,
            table=table,
            rows_affected=rows_affected,
            duration_ms=duration_ms,
            success=success,
            error=error
        )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def get_structured_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance
    
    Args:
        name: Logger name
    
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)


# Export utilities
__all__ = [
    'setup_logging',
    'get_logger',
    'get_structured_logger',
    'StructuredLogger',
    'APIKeyFilter'
]