"""
Tests for Alibaba scraper.
"""

import pytest
from unittest.mock import AsyncMock, patch

from skysniper.scrapers.alibaba import AlibabaScraper
from skysniper.scrapers.base import SearchParams


class TestAlibabaScraper:
    """Tests for AlibabaScraper."""

    def test_alibaba_scraper_attributes(self):
        """Test Alibaba scraper has correct attributes."""
        scraper = AlibabaScraper()
        assert scraper.name == "alibaba"
        assert scraper.base_url == "https://www.alibaba.ir"
        assert scraper.SEARCH_API == "https://ws.alibaba.ir/api/v1/flights/domestic/available"

    def test_build_search_payload(self, sample_search_params):
        """Test building search payload."""
        scraper = AlibabaScraper()
        payload = scraper._build_search_payload(sample_search_params)

        assert payload["origin"] == "THR"
        assert payload["destination"] == "MHD"
        assert payload["departureDate"] == "2025-01-15"
        assert payload["adult"] == 2

    def test_get_headers(self):
        """Test getting request headers."""
        scraper = AlibabaScraper()
        headers = scraper._get_headers()

        assert "Accept" in headers
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"
        assert scraper.base_url in headers.get("Origin", "")

    @pytest.mark.asyncio
    async def test_search_with_mock_response(self, sample_search_params):
        """Test search method with mocked API response."""
        mock_response_data = {
            "result": {
                "departing": [
                    {
                        "departureDateTime": "2025-01-15T10:30:00",
                        "arrivalDateTime": "2025-01-15T12:00:00",
                        "airlineName": "Iran Air",
                        "flightNumber": "IR123",
                        "price": 5000000,
                        "stops": 0,
                        "duration": 90,
                    }
                ]
            }
        }

        async with AlibabaScraper() as scraper:
            # Mock the session.post method
            mock_response = AsyncMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = lambda: None  # Synchronous method
            scraper._session.post = AsyncMock(return_value=mock_response)

            flights = await scraper.search(sample_search_params)

            # Verify API was called
            assert scraper._session.post.called
            call_args = scraper._session.post.call_args
            assert call_args[0][0] == scraper.SEARCH_API

            # Note: Actual parsing will work once we implement _parse_response properly
            # For now, this tests the structure

    @pytest.mark.asyncio
    async def test_search_handles_errors(self, sample_search_params):
        """Test search handles API errors gracefully."""
        async with AlibabaScraper() as scraper:
            # Mock a failed request
            scraper._session.post = AsyncMock(side_effect=Exception("Network error"))

            flights = await scraper.search(sample_search_params)

            # Should return empty list on error
            assert flights == []
