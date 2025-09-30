"""
Error Handling Utilities
Provides decorators and utilities for safe execution with fallback
"""

import functools
import logging
from typing import Any, Callable, Optional, TypeVar, Union
import traceback

logger = logging.getLogger(__name__)

T = TypeVar('T')


def safe_execute(
    default_return: Any = None,
    log_errors: bool = True,
    error_message: Optional[str] = None,
    reraise: bool = False
):
    """
    Decorator for safe execution with fallback
    
    Args:
        default_return: Value to return if exception occurs
        log_errors: Whether to log errors
        error_message: Custom error message for logging
        reraise: Whether to re-raise the exception after handling
    
    Returns:
        Decorated function that handles exceptions gracefully
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    msg = error_message or f"Error in {func.__name__}"
                    logger.error(f"{msg}: {str(e)}", exc_info=True)
                
                if reraise:
                    raise
                
                return default_return
        return wrapper
    return decorator


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator to retry function on failure with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch
    
    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            import time
            
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {str(e)}"
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {str(e)}"
                        )
            
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator


class ErrorContext:
    """Context manager for error handling with cleanup"""
    
    def __init__(
        self,
        operation_name: str,
        cleanup_func: Optional[Callable] = None,
        default_return: Any = None,
        suppress: bool = False
    ):
        """
        Initialize error context
        
        Args:
            operation_name: Name of the operation for logging
            cleanup_func: Function to call for cleanup on error
            default_return: Value to return if error occurs and suppress=True
            suppress: Whether to suppress the exception
        """
        self.operation_name = operation_name
        self.cleanup_func = cleanup_func
        self.default_return = default_return
        self.suppress = suppress
        self.result = None
    
    def __enter__(self):
        logger.debug(f"Starting operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(
                f"Error in {self.operation_name}: {exc_val}",
                exc_info=(exc_type, exc_val, exc_tb)
            )
            
            if self.cleanup_func:
                try:
                    logger.info(f"Running cleanup for {self.operation_name}")
                    self.cleanup_func()
                except Exception as cleanup_error:
                    logger.error(f"Cleanup failed: {cleanup_error}")
            
            if self.suppress:
                self.result = self.default_return
                return True  # Suppress the exception
        
        return False  # Don't suppress the exception


def validate_required_fields(data: dict, required_fields: list) -> bool:
    """
    Validate that all required fields are present and non-empty in data
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
    
    Returns:
        True if all required fields are present and non-empty
    
    Raises:
        ValueError: If validation fails
    """
    missing_fields = []
    empty_fields = []
    
    for field in required_fields:
        if field not in data:
            missing_fields.append(field)
        elif not data[field]:
            empty_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    if empty_fields:
        raise ValueError(f"Empty required fields: {', '.join(empty_fields)}")
    
    return True


def sanitize_user_input(
    input_value: str,
    max_length: int = 1000,
    allowed_chars: Optional[str] = None
) -> str:
    """
    Sanitize user input to prevent injection attacks
    
    Args:
        input_value: User input to sanitize
        max_length: Maximum allowed length
        allowed_chars: Regex pattern of allowed characters
    
    Returns:
        Sanitized input string
    
    Raises:
        ValueError: If input is invalid
    """
    import re
    
    if not input_value or not isinstance(input_value, str):
        raise ValueError("Input must be a non-empty string")
    
    # Truncate to max length
    input_value = input_value[:max_length]
    
    # Remove control characters
    input_value = ''.join(char for char in input_value if ord(char) >= 32 or char == '\n')
    
    # Apply allowed chars filter if specified
    if allowed_chars:
        if not re.match(allowed_chars, input_value):
            raise ValueError(f"Input contains invalid characters")
    
    return input_value.strip()


def create_error_response(
    error: Exception,
    operation: str = "Unknown operation",
    include_traceback: bool = False
) -> dict:
    """
    Create a standardized error response dictionary
    
    Args:
        error: The exception that occurred
        operation: Name of the operation that failed
        include_traceback: Whether to include full traceback
    
    Returns:
        Dictionary with error details
    """
    response = {
        "success": False,
        "error": {
            "type": type(error).__name__,
            "message": str(error),
            "operation": operation
        }
    }
    
    if include_traceback:
        response["error"]["traceback"] = traceback.format_exc()
    
    return response


# Export all utilities
__all__ = [
    'safe_execute',
    'retry_on_failure',
    'ErrorContext',
    'validate_required_fields',
    'sanitize_user_input',
    'create_error_response'
]