"""
Tests for scraper registry.
"""

import pytest

from skysniper.scrapers import SCRAPERS, AlibabaScraper


class TestScraperRegistry:
    """Tests for scraper registry."""

    def test_scrapers_registry_contains_alibaba(self):
        """Test that Alibaba scraper is registered."""
        assert "alibaba" in SCRAPERS
        assert SCRAPERS["alibaba"] == AlibabaScraper

    def test_scraper_can_be_instantiated(self):
        """Test that registered scrapers can be instantiated."""
        scraper_class = SCRAPERS["alibaba"]
        scraper = scraper_class()
        assert isinstance(scraper, AlibabaScraper)
        assert scraper.name == "alibaba"
