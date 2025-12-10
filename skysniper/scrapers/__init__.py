"""
Flight scrapers module.

Each scraper fetches flight data from a specific source.
"""

from skysniper.scrapers.base import BaseScraper, Flight, SearchParams
from skysniper.scrapers.alibaba import AlibabaScraper
from skysniper.scrapers.ataair import AtaairScraper
from skysniper.scrapers.mrbilit import MrbilitScraper

# Registry of all available scrapers
SCRAPERS: dict[str, type[BaseScraper]] = {
    "alibaba": AlibabaScraper,
    "ataair": AtaairScraper,
    "mrbilit": MrbilitScraper,
}

__all__ = [
    "BaseScraper",
    "Flight",
    "SearchParams",
    "AlibabaScraper",
    "AtaairScraper",
    "MrbilitScraper",
    "SCRAPERS",
]
