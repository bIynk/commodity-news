"""
Rate Limiting Module
Provides rate limiting functionality to prevent API quota exhaustion
"""

import time
import threading
from collections import deque
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Thread-safe rate limiter using sliding window algorithm
    """
    
    def __init__(
        self,
        max_calls: int,
        time_window: int,
        name: str = "default"
    ):
        """
        Initialize rate limiter
        
        Args:
            max_calls: Maximum number of calls allowed in time window
            time_window: Time window in seconds
            name: Name for this rate limiter (for logging)
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.name = name
        self.calls = deque()
        self.lock = threading.Lock()
        
        logger.info(
            f"Rate limiter '{name}' initialized: "
            f"{max_calls} calls per {time_window} seconds"
        )
    
    def allow_request(self) -> bool:
        """
        Check if a request is allowed under the current rate limit
        
        Returns:
            True if request is allowed, False otherwise
        """
        with self.lock:
            now = time.time()
            
            # Remove old calls outside the time window
            while self.calls and self.calls[0] < now - self.time_window:
                self.calls.popleft()
            
            # Check if we can make a new call
            if len(self.calls) < self.max_calls:
                self.calls.append(now)
                return True
            
            return False
    
    def wait_if_needed(self, timeout: Optional[float] = None) -> bool:
        """
        Wait until a request is allowed or timeout is reached
        
        Args:
            timeout: Maximum time to wait in seconds (None for no timeout)
        
        Returns:
            True if request was eventually allowed, False if timeout
        """
        start_time = time.time()
        
        while True:
            if self.allow_request():
                wait_time = time.time() - start_time
                if wait_time > 0.1:  # Only log if we actually waited
                    logger.debug(
                        f"Rate limiter '{self.name}': "
                        f"Waited {wait_time:.2f}s for slot"
                    )
                return True
            
            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    logger.warning(
                        f"Rate limiter '{self.name}': "
                        f"Timeout after {elapsed:.2f}s"
                    )
                    return False
            
            # Short sleep to avoid busy waiting
            time.sleep(0.1)
    
    def get_wait_time(self) -> float:
        """
        Get the estimated wait time until next available slot
        
        Returns:
            Seconds until next slot becomes available (0 if slot available now)
        """
        with self.lock:
            now = time.time()
            
            # Clean old calls
            while self.calls and self.calls[0] < now - self.time_window:
                self.calls.popleft()
            
            # If we have capacity, no wait
            if len(self.calls) < self.max_calls:
                return 0.0
            
            # Otherwise, calculate wait until oldest call expires
            oldest_call = self.calls[0]
            wait_time = (oldest_call + self.time_window) - now
            return max(0.0, wait_time)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get current rate limiter statistics
        
        Returns:
            Dictionary with current stats
        """
        with self.lock:
            now = time.time()
            
            # Clean old calls
            while self.calls and self.calls[0] < now - self.time_window:
                self.calls.popleft()
            
            current_calls = len(self.calls)
            available_calls = self.max_calls - current_calls
            
            return {
                "name": self.name,
                "max_calls": self.max_calls,
                "time_window": self.time_window,
                "current_calls": current_calls,
                "available_calls": available_calls,
                "utilization_percent": (current_calls / self.max_calls) * 100,
                "wait_time": self.get_wait_time()
            }
    
    def reset(self):
        """Reset the rate limiter, clearing all recorded calls"""
        with self.lock:
            self.calls.clear()
            logger.info(f"Rate limiter '{self.name}' reset")


class MultiTierRateLimiter:
    """
    Multi-tier rate limiter for different time windows
    (e.g., per-second, per-minute, per-hour limits)
    """
    
    def __init__(self, name: str = "multi-tier"):
        """
        Initialize multi-tier rate limiter
        
        Args:
            name: Name for this rate limiter
        """
        self.name = name
        self.limiters = {}
        self.lock = threading.Lock()
    
    def add_tier(
        self,
        tier_name: str,
        max_calls: int,
        time_window: int
    ):
        """
        Add a rate limiting tier
        
        Args:
            tier_name: Name of the tier (e.g., 'per_second', 'per_minute')
            max_calls: Maximum calls for this tier
            time_window: Time window in seconds for this tier
        """
        with self.lock:
            self.limiters[tier_name] = RateLimiter(
                max_calls=max_calls,
                time_window=time_window,
                name=f"{self.name}.{tier_name}"
            )
            logger.info(
                f"Added tier '{tier_name}' to multi-tier limiter '{self.name}': "
                f"{max_calls} calls per {time_window}s"
            )
    
    def allow_request(self) -> bool:
        """
        Check if request is allowed across all tiers
        
        Returns:
            True if allowed by all tiers, False otherwise
        """
        with self.lock:
            # Check all tiers
            for tier_name, limiter in self.limiters.items():
                if not limiter.allow_request():
                    logger.debug(
                        f"Multi-tier limiter '{self.name}': "
                        f"Blocked by tier '{tier_name}'"
                    )
                    # If blocked by any tier, we need to rollback
                    # the successful increments
                    for prev_tier, prev_limiter in self.limiters.items():
                        if prev_tier == tier_name:
                            break
                        # Remove the last added call
                        if prev_limiter.calls:
                            prev_limiter.calls.pop()
                    return False
            
            return True
    
    def wait_if_needed(self, timeout: Optional[float] = None) -> bool:
        """
        Wait until request is allowed across all tiers
        
        Args:
            timeout: Maximum time to wait
        
        Returns:
            True if eventually allowed, False if timeout
        """
        start_time = time.time()
        
        while True:
            if self.allow_request():
                return True
            
            # Check timeout
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return False
            
            # Get minimum wait time across all tiers
            min_wait = min(
                limiter.get_wait_time()
                for limiter in self.limiters.values()
            )
            
            # Sleep for minimum wait time (or 0.1s, whichever is smaller)
            time.sleep(min(0.1, min_wait))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics for all tiers"""
        with self.lock:
            return {
                "name": self.name,
                "tiers": {
                    name: limiter.get_stats()
                    for name, limiter in self.limiters.items()
                }
            }


class PerplexityRateLimiter(MultiTierRateLimiter):
    """
    Pre-configured rate limiter for Perplexity AI API
    Based on typical API limits
    """
    
    def __init__(self):
        """Initialize with Perplexity-specific rate limits"""
        super().__init__(name="perplexity")
        
        # Add typical API rate limit tiers
        # These should be adjusted based on actual Perplexity API limits
        self.add_tier("per_second", max_calls=2, time_window=1)
        self.add_tier("per_minute", max_calls=50, time_window=60)
        self.add_tier("per_hour", max_calls=1000, time_window=3600)
        
        logger.info("Perplexity rate limiter initialized with default tiers")


# Global rate limiter instance for Perplexity API
_perplexity_limiter = None


def get_perplexity_rate_limiter() -> PerplexityRateLimiter:
    """
    Get singleton instance of Perplexity rate limiter
    
    Returns:
        PerplexityRateLimiter instance
    """
    global _perplexity_limiter
    if _perplexity_limiter is None:
        _perplexity_limiter = PerplexityRateLimiter()
    return _perplexity_limiter


def rate_limit_decorator(rate_limiter: RateLimiter):
    """
    Decorator to apply rate limiting to a function
    
    Args:
        rate_limiter: RateLimiter instance to use
    
    Returns:
        Decorated function with rate limiting
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Wait for rate limit slot
            if not rate_limiter.wait_if_needed(timeout=30):
                raise TimeoutError(
                    f"Rate limit timeout for {rate_limiter.name}"
                )
            
            # Execute function
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Log the error but don't remove from rate limit
                # (failed requests still count against quota)
                logger.error(f"Error in rate-limited function: {e}")
                raise
        
        return wrapper
    return decorator


# Export utilities
__all__ = [
    'RateLimiter',
    'MultiTierRateLimiter',
    'PerplexityRateLimiter',
    'get_perplexity_rate_limiter',
    'rate_limit_decorator'
]