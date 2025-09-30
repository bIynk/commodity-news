"""
Sector configuration module for loading news source mappings.
Provides sector-specific news sources for Perplexity AI queries.
"""

import yaml
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class SectorConfig:
    """Manages sector-specific news source configuration."""

    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if SectorConfig._config is None:
            self._load_config()

    def _load_config(self) -> None:
        """Load news sources configuration from YAML file."""
        # Get config file path relative to current module
        current_dir = Path(__file__).parent.parent.parent
        config_path = current_dir / 'config' / 'news_sources.yaml'

        if not config_path.exists():
            error_msg = f"News sources config not found at {config_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                SectorConfig._config = yaml.safe_load(f)

            # Validate config structure
            required_keys = ['default_settings', 'general_sources', 'sectors']
            for key in required_keys:
                if key not in SectorConfig._config:
                    error_msg = f"Missing required key '{key}' in news sources config"
                    logger.error(error_msg)
                    raise ValueError(error_msg)

            logger.info(f"Successfully loaded news sources config with {len(SectorConfig._config.get('sectors', {}))} sectors")

        except Exception as e:
            logger.error(f"Error loading news sources config: {str(e)}")
            raise

    def get_sector_sources(self, sector: str) -> List[str]:
        """
        Get news sources for a specific sector.

        Args:
            sector: Name of the sector

        Returns:
            List of news source names for the sector
        """
        if not SectorConfig._config:
            return []

        # Get sector-specific sources
        sector_data = SectorConfig._config.get('sectors', {}).get(sector, {})
        sector_sources_raw = sector_data.get('sources', [])

        # Extract source names (handle both dict and string formats)
        sector_sources = []
        for source in sector_sources_raw:
            if isinstance(source, dict):
                sector_sources.append(source.get('name', ''))
            else:
                sector_sources.append(str(source))

        # Add general sources if enabled
        settings = SectorConfig._config.get('default_settings', {})
        if settings.get('include_general_sources', True):
            general_sources_raw = SectorConfig._config.get('general_sources', [])
            # Extract general source names
            for source in general_sources_raw:
                if isinstance(source, dict):
                    sector_sources.append(source.get('name', ''))
                else:
                    sector_sources.append(str(source))

        # Remove empty strings
        sector_sources = [s for s in sector_sources if s]
        return sector_sources

    def get_sector_sources_with_urls(self, sector: str) -> List[Dict[str, str]]:
        """
        Get news sources with URLs for a specific sector.

        Args:
            sector: Name of the sector

        Returns:
            List of dicts with 'name' and 'url' keys
        """
        if not SectorConfig._config:
            return []

        # Get sector-specific sources
        sector_data = SectorConfig._config.get('sectors', {}).get(sector, {})
        sector_sources_raw = sector_data.get('sources', [])

        # Extract sources with URLs
        sector_sources = []
        for source in sector_sources_raw:
            if isinstance(source, dict) and source.get('name') and source.get('url'):
                sector_sources.append({
                    'name': source['name'],
                    'url': source['url']
                })

        # Add general sources if enabled
        settings = SectorConfig._config.get('default_settings', {})
        if settings.get('include_general_sources', True):
            general_sources_raw = SectorConfig._config.get('general_sources', [])
            for source in general_sources_raw:
                if isinstance(source, dict) and source.get('name') and source.get('url'):
                    sector_sources.append({
                        'name': source['name'],
                        'url': source['url']
                    })

        return sector_sources

    def get_vietnam_sources(self, sector: str) -> List[str]:
        """
        Get Vietnam-specific sources for a sector.

        Args:
            sector: Name of the sector

        Returns:
            List of Vietnam-specific news sources
        """
        if not SectorConfig._config:
            return []

        sector_data = SectorConfig._config.get('sectors', {}).get(sector, {})
        vietnam_sources_raw = sector_data.get('vietnam_specific', [])

        # Extract source names (handle both dict and string formats)
        vietnam_sources = []
        for source in vietnam_sources_raw:
            if isinstance(source, dict):
                name = source.get('name', '')
                if name:
                    vietnam_sources.append(name)
            else:
                vietnam_sources.append(str(source))

        return vietnam_sources

    def get_prompt_template(self) -> str:
        """Get the prompt template for queries."""
        if not SectorConfig._config:
            return "Analyze {commodity_name} ({ticker}) in the {sector} sector."

        query_settings = SectorConfig._config.get('query_settings', {})
        return query_settings.get('prompt_template',
                                 "Analyze {commodity_name} ({ticker}) in the {sector} sector.")

    def get_api_parameters(self) -> Dict[str, Any]:
        """Get API parameters for Perplexity queries."""
        if not SectorConfig._config:
            return {'temperature': 0.2, 'max_tokens': 1500}

        query_settings = SectorConfig._config.get('query_settings', {})
        return query_settings.get('api_parameters', {'temperature': 0.2, 'max_tokens': 1500})

    def get_cache_duration(self) -> int:
        """Get cache duration in hours."""
        if not SectorConfig._config:
            return 24

        settings = SectorConfig._config.get('default_settings', {})
        return settings.get('cache_duration_hours', 24)

    def is_vietnam_focus_enabled(self) -> bool:
        """Check if Vietnam market focus is enabled."""
        if not SectorConfig._config:
            return True

        settings = SectorConfig._config.get('default_settings', {})
        return settings.get('vietnam_focus', True)

    def get_all_sectors(self) -> List[str]:
        """Get list of all configured sectors."""
        if not SectorConfig._config:
            return []

        return list(SectorConfig._config.get('sectors', {}).keys())


# Singleton instance
_sector_config = None

def get_sector_config() -> SectorConfig:
    """Get the singleton sector configuration instance."""
    global _sector_config
    if _sector_config is None:
        _sector_config = SectorConfig()
    return _sector_config