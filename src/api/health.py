"""
Health Check Module
Provides endpoints and functions for monitoring application health
"""

import os
import sqlite3
import requests
from datetime import datetime
from typing import Dict, Optional
import time
import logging

logger = logging.getLogger(__name__)


def check_database_health(db_path: str = "data/commodity_data.db") -> Dict:
    """
    Check database connectivity and basic operations
    
    Args:
        db_path: Path to SQLite database
    
    Returns:
        Dictionary with health status and details
    """
    start_time = time.time()
    
    try:
        # Test connection
        conn = sqlite3.connect(db_path, timeout=5.0)
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT COUNT(*) FROM commodities")
        commodity_count = cursor.fetchone()[0]
        
        # Test query results table
        cursor.execute("""
            SELECT COUNT(*) FROM query_results 
            WHERE DATE(query_timestamp) = DATE('now')
        """)
        today_queries = cursor.fetchone()[0]
        
        # Check database size
        cursor.execute("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
        db_size = cursor.fetchone()[0]
        
        conn.close()
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
            "details": {
                "commodities_count": commodity_count,
                "today_queries": today_queries,
                "database_size_mb": round(db_size / (1024 * 1024), 2)
            }
        }
        
    except sqlite3.OperationalError as e:
        if "locked" in str(e):
            return {
                "status": "degraded",
                "error": "Database is locked",
                "latency_ms": (time.time() - start_time) * 1000
            }
        else:
            return {
                "status": "unhealthy",
                "error": str(e),
                "latency_ms": (time.time() - start_time) * 1000
            }
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "latency_ms": (time.time() - start_time) * 1000
        }


def check_api_health(api_key: Optional[str] = None) -> Dict:
    """
    Check Perplexity API connectivity
    
    Args:
        api_key: Perplexity API key (if not provided, reads from environment)
    
    Returns:
        Dictionary with API health status
    """
    start_time = time.time()
    
    if not api_key:
        api_key = os.getenv("PERPLEXITY_API_KEY")
    
    if not api_key:
        return {
            "status": "unhealthy",
            "error": "API key not configured",
            "latency_ms": 0
        }
    
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Minimal test query
        payload = {
            "model": "sonar-small-online",
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 1,
            "temperature": 0
        }
        
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        latency_ms = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            return {
                "status": "healthy",
                "latency_ms": round(latency_ms, 2),
                "status_code": response.status_code
            }
        elif response.status_code == 429:
            return {
                "status": "degraded",
                "error": "Rate limited",
                "latency_ms": round(latency_ms, 2),
                "status_code": response.status_code
            }
        elif response.status_code == 401:
            return {
                "status": "unhealthy",
                "error": "Invalid API key",
                "latency_ms": round(latency_ms, 2),
                "status_code": response.status_code
            }
        else:
            return {
                "status": "unhealthy",
                "error": f"API returned status {response.status_code}",
                "latency_ms": round(latency_ms, 2),
                "status_code": response.status_code
            }
            
    except requests.exceptions.Timeout:
        return {
            "status": "unhealthy",
            "error": "API request timeout",
            "latency_ms": (time.time() - start_time) * 1000
        }
        
    except requests.exceptions.ConnectionError:
        return {
            "status": "unhealthy",
            "error": "Cannot connect to API",
            "latency_ms": (time.time() - start_time) * 1000
        }
        
    except Exception as e:
        logger.error(f"API health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "latency_ms": (time.time() - start_time) * 1000
        }


def check_cache_health() -> Dict:
    """
    Check cache system health
    
    Returns:
        Dictionary with cache health status
    """
    try:
        # Check if cache directory exists and is writable
        cache_dir = "data"
        if os.path.exists(cache_dir) and os.access(cache_dir, os.W_OK):
            # Get cache statistics
            db_path = os.path.join(cache_dir, "commodity_data.db")
            cache_size = 0
            if os.path.exists(db_path):
                cache_size = os.path.getsize(db_path)
            
            return {
                "status": "healthy",
                "details": {
                    "cache_directory": cache_dir,
                    "writable": True,
                    "cache_size_mb": round(cache_size / (1024 * 1024), 2)
                }
            }
        else:
            return {
                "status": "unhealthy",
                "error": "Cache directory not accessible"
            }
            
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


def check_dependencies_health() -> Dict:
    """
    Check if all required dependencies are available
    
    Returns:
        Dictionary with dependencies health status
    """
    required_modules = [
        'streamlit',
        'pandas',
        'plotly',
        'requests',
        'yaml',
        'dotenv'
    ]
    
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        return {
            "status": "unhealthy",
            "error": f"Missing modules: {', '.join(missing_modules)}"
        }
    else:
        return {
            "status": "healthy",
            "details": {
                "modules_checked": len(required_modules),
                "all_present": True
            }
        }


def perform_full_health_check() -> Dict:
    """
    Perform comprehensive health check of all systems
    
    Returns:
        Dictionary with complete health status
    """
    health_status = {
        "timestamp": datetime.utcnow().isoformat(),
        "overall_status": "healthy",
        "components": {}
    }
    
    # Check each component
    components_checks = [
        ("database", check_database_health()),
        ("api", check_api_health()),
        ("cache", check_cache_health()),
        ("dependencies", check_dependencies_health())
    ]
    
    unhealthy_count = 0
    degraded_count = 0
    
    for component_name, component_status in components_checks:
        health_status["components"][component_name] = component_status
        
        if component_status["status"] == "unhealthy":
            unhealthy_count += 1
        elif component_status["status"] == "degraded":
            degraded_count += 1
    
    # Determine overall status
    if unhealthy_count > 0:
        health_status["overall_status"] = "unhealthy"
    elif degraded_count > 0:
        health_status["overall_status"] = "degraded"
    
    # Add summary
    health_status["summary"] = {
        "healthy_components": len(components_checks) - unhealthy_count - degraded_count,
        "degraded_components": degraded_count,
        "unhealthy_components": unhealthy_count,
        "total_components": len(components_checks)
    }
    
    return health_status


def format_health_for_display(health_data: Dict) -> str:
    """
    Format health check data for display
    
    Args:
        health_data: Health check results
    
    Returns:
        Formatted string for display
    """
    status_emoji = {
        "healthy": "✅",
        "degraded": "⚠️",
        "unhealthy": "❌"
    }
    
    lines = []
    lines.append(f"**Overall Status**: {status_emoji.get(health_data['overall_status'], '❓')} {health_data['overall_status'].upper()}")
    lines.append(f"**Checked**: {health_data['timestamp']}")
    lines.append("")
    lines.append("**Components:**")
    
    for component, status in health_data.get('components', {}).items():
        emoji = status_emoji.get(status['status'], '❓')
        lines.append(f"- {component.capitalize()}: {emoji} {status['status']}")
        
        if 'latency_ms' in status:
            lines.append(f"  - Latency: {status['latency_ms']}ms")
        
        if 'error' in status:
            lines.append(f"  - Error: {status['error']}")
        
        if 'details' in status:
            for key, value in status['details'].items():
                lines.append(f"  - {key.replace('_', ' ').title()}: {value}")
    
    return "\n".join(lines)


# Export functions
__all__ = [
    'check_database_health',
    'check_api_health',
    'check_cache_health',
    'check_dependencies_health',
    'perform_full_health_check',
    'format_health_for_display'
]