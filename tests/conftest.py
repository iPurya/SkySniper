"""
Pytest configuration and shared fixtures.
"""

import pytest
from datetime import datetime

from skysniper.scrapers.base import Flight, SearchParams


@pytest.fixture
def sample_search_params():
    """Sample search parameters for testing."""
    return SearchParams(
        origin="THR",
        destination="MHD",
        date="2025-01-15",
        adults=2,
        children=0,
        infants=0,
    )


@pytest.fixture
def sample_flight():
    """Sample flight object for testing."""
    return Flight(
        origin="THR",
        destination="MHD",
        departure_time=datetime(2025, 1, 15, 10, 30),
        arrival_time=datetime(2025, 1, 15, 12, 0),
        airline="Iran Air",
        flight_number="IR123",
        price=5000000.0,
        currency="IRR",
        cabin_class="economy",
        stops=0,
        duration_minutes=90,
        source="alibaba",
        deep_link="https://www.alibaba.ir/flights/THR-MHD",
    )


@pytest.fixture
def sample_flights(sample_flight):
    """Multiple sample flights for testing."""
    flight2 = Flight(
        origin="THR",
        destination="MHD",
        departure_time=datetime(2025, 1, 15, 14, 0),
        arrival_time=datetime(2025, 1, 15, 15, 30),
        airline="Mahan Air",
        flight_number="W5123",
        price=4500000.0,
        currency="IRR",
        cabin_class="economy",
        stops=0,
        duration_minutes=90,
        source="alibaba",
    )
    return [sample_flight, flight2]
