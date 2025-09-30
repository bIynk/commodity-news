"""
Constants and configuration values for the SQL Dashboard.
Centralizes magic numbers and thresholds used throughout the application.
"""

class DataFreshnessConfig:
    """Configuration for data staleness detection"""

    # Staleness thresholds (in days)
    DAILY_STALENESS_DAYS = 7   # Commodities updated daily are stale after 7 days
    WEEKLY_STALENESS_DAYS = 14  # Commodities updated weekly are stale after 14 days

    # Frequency detection parameters (aligns with existing detect_frequency algorithm)
    FREQUENCY_LOOKBACK_DAYS = 90  # Look at last 90 days of data
    DAILY_THRESHOLD = 0.5  # If >50% of returns are non-zero, classify as daily


class ZScoreConfig:
    """Configuration for Z-score calculations"""

    # Window sizes for rolling statistics
    # Note: These are applied AFTER resampling, so units differ:
    # - For daily data: window is in days
    # - For weekly data: window is in weeks
    DEFAULT_WINDOW_SIZE = 30  # Daily: 30-day window, Weekly: 30-week window (current implementation)
    WEEKLY_WINDOW_SIZE = 12   # Not currently used - kept for future implementation

    # Z-score thresholds
    EXTREME_THRESHOLD = 3.0  # Extreme moves
    NOTABLE_THRESHOLD = 2.0  # Notable moves
    NOTICE_THRESHOLD = 1.0   # Worth notice


class DisplayConfig:
    """Configuration for display and formatting"""

    # Number formatting
    PRICE_DECIMALS = 2
    PERCENT_DECIMALS = 2

    # Table display
    MAX_ROWS_PER_PAGE = 50
    DEFAULT_ROW_HEIGHT = 35