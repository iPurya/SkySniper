"""
Tests for scraper registry.
"""

import pytest

from skysniper.scrapers import SCRAPERS, AlibabaScraper, AtaairScraper, MrbilitScraper


class TestScraperRegistry:
    """Tests for scraper registry."""

    def test_scrapers_registry_contains_alibaba(self):
        """Test that Alibaba scraper is registered."""
        assert "alibaba" in SCRAPERS
        assert SCRAPERS["alibaba"] == AlibabaScraper

    def test_scrapers_registry_contains_ataair(self):
        """Test that Ataair scraper is registered."""
        assert "ataair" in SCRAPERS
        assert SCRAPERS["ataair"] == AtaairScraper

    def test_scrapers_registry_contains_mrbilit(self):
        """Test that MrBilit scraper is registered."""
        assert "mrbilit" in SCRAPERS
        assert SCRAPERS["mrbilit"] == MrbilitScraper

    def test_scraper_can_be_instantiated(self):
        """Test that registered scrapers can be instantiated."""
        for name, scraper_class in SCRAPERS.items():
            scraper = scraper_class()
            assert scraper.name == name

    def test_registry_count(self):
        """Test that we have expected number of scrapers."""
        assert len(SCRAPERS) == 3
