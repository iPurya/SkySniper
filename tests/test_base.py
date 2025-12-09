"""
Tests for base scraper classes and data models.
"""

import pytest
from datetime import datetime

from skysniper.scrapers.base import Flight, SearchParams, BaseScraper


class TestFlight:
    """Tests for Flight dataclass."""

    def test_flight_creation(self, sample_flight):
        """Test creating a Flight object."""
        assert sample_flight.origin == "THR"
        assert sample_flight.destination == "MHD"
        assert sample_flight.airline == "Iran Air"
        assert sample_flight.price == 5000000.0

    def test_duration_formatted(self, sample_flight):
        """Test duration formatting."""
        assert sample_flight.duration_formatted == "1h 30m"

    def test_duration_formatted_hours_only(self):
        """Test duration formatting with only hours."""
        flight = Flight(
            origin="THR",
            destination="DXB",
            departure_time=datetime(2025, 1, 15, 10, 0),
            arrival_time=datetime(2025, 1, 15, 13, 0),
            airline="Test",
            flight_number="T123",
            price=1000.0,
            currency="USD",
            duration_minutes=180,
        )
        assert flight.duration_formatted == "3h 0m"

    def test_flight_string_representation(self, sample_flight):
        """Test Flight string representation."""
        flight_str = str(sample_flight)
        assert "Iran Air" in flight_str
        assert "IR123" in flight_str
        assert "THR→MHD" in flight_str
        assert "5,000,000" in flight_str or "5000000" in flight_str

    def test_flight_with_stops(self):
        """Test flight with stops."""
        flight = Flight(
            origin="THR",
            destination="IST",
            departure_time=datetime(2025, 1, 15, 10, 0),
            arrival_time=datetime(2025, 1, 15, 16, 0),
            airline="Test",
            flight_number="T123",
            price=2000.0,
            currency="USD",
            stops=1,
            duration_minutes=360,
        )
        assert flight.stops == 1


class TestSearchParams:
    """Tests for SearchParams dataclass."""

    def test_search_params_creation(self, sample_search_params):
        """Test creating SearchParams."""
        assert sample_search_params.origin == "THR"
        assert sample_search_params.destination == "MHD"
        assert sample_search_params.date == "2025-01-15"
        assert sample_search_params.adults == 2

    def test_search_params_defaults(self):
        """Test SearchParams default values."""
        params = SearchParams(
            origin="THR",
            destination="MHD",
            date="2025-01-15",
        )
        assert params.adults == 1
        assert params.children == 0
        assert params.infants == 0
        assert params.cabin_class == "economy"


class TestBaseScraper:
    """Tests for BaseScraper abstract class."""

    def test_base_scraper_cannot_be_instantiated(self):
        """Test that BaseScraper cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseScraper()

    def test_base_scraper_requires_search_method(self):
        """Test that subclasses must implement search method."""
        class IncompleteScraper(BaseScraper):
            name = "incomplete"

        with pytest.raises(TypeError):
            IncompleteScraper()

    @pytest.mark.asyncio
    async def test_base_scraper_context_manager(self):
        """Test BaseScraper as async context manager."""
        class TestScraper(BaseScraper):
            name = "test"
            base_url = "https://example.com"

            async def search(self, params):
                return []

        async with TestScraper() as scraper:
            assert scraper._session is not None
            assert scraper.name == "test"

        # Session should be closed after context
        assert scraper._session is None
