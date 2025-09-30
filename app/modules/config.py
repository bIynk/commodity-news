"""
Configuration module for unified dashboard
Handles environment variables and feature configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database Configuration
DC_DB_STRING = os.getenv('DC_DB_STRING')
DC_DB_STRING_MASTER = os.getenv('DC_DB_STRING_MASTER', DC_DB_STRING)  # Falls back to regular connection

# AI Configuration - Always enabled in unified dashboard
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
if not PERPLEXITY_API_KEY:
    raise ValueError(
        "Perplexity API key is required for the unified dashboard.\n"
        "Please set PERPLEXITY_API_KEY environment variable."
    )

# Cache Configuration
AI_CACHE_HOURS = int(os.getenv('AI_CACHE_HOURS', '24'))
AI_CACHE_ENABLED = os.getenv('AI_CACHE_ENABLED', 'true').lower() == 'true'

# Rate Limiting
PERPLEXITY_RATE_LIMIT = int(os.getenv('PERPLEXITY_RATE_LIMIT', '50'))  # requests per minute
PERPLEXITY_TIMEOUT = int(os.getenv('PERPLEXITY_TIMEOUT', '30'))  # seconds

# Display Configuration
MAX_NEWS_ITEMS = int(os.getenv('MAX_NEWS_ITEMS', '6'))
DEFAULT_TIMEFRAME = os.getenv('DEFAULT_TIMEFRAME', '1 week')

# AI Query Threshold Configuration
AI_ZSCORE_THRESHOLD = float(os.getenv('AI_ZSCORE_THRESHOLD', '2.0'))

# Debug Configuration
DEBUG_MODE = os.getenv('DEBUG', 'false').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Export configuration
__all__ = [
    'DC_DB_STRING',
    'DC_DB_STRING_MASTER',
    'PERPLEXITY_API_KEY',
    'AI_CACHE_HOURS',
    'AI_CACHE_ENABLED',
    'PERPLEXITY_RATE_LIMIT',
    'PERPLEXITY_TIMEOUT',
    'MAX_NEWS_ITEMS',
    'DEFAULT_TIMEFRAME',
    'AI_ZSCORE_THRESHOLD',
    'DEBUG_MODE',
    'LOG_LEVEL'
]