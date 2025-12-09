"""
Flight scrapers module.

Each scraper fetches flight data from a specific source.
"""

from skysniper.scrapers.base import BaseScraper, Flight, SearchParams
from skysniper.scrapers.alibaba import AlibabaScraper

# Registry of all available scrapers
SCRAPERS: dict[str, type[BaseScraper]] = {
    "alibaba": AlibabaScraper,
}

__all__ = [
    "BaseScraper",
    "Flight",
    "SearchParams",
    "AlibabaScraper",
    "SCRAPERS",
]
