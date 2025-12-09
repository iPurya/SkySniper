"""
Tests for Alibaba scraper.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from skysniper.scrapers.alibaba import AlibabaScraper
from skysniper.scrapers.base import SearchParams


class TestAlibabaScraper:
    """Tests for AlibabaScraper."""

    def test_alibaba_scraper_attributes(self):
        """Test Alibaba scraper has correct attributes."""
        scraper = AlibabaScraper()
        assert scraper.name == "alibaba"
        assert scraper.base_url == "https://www.alibaba.ir"
        assert scraper.INTERNATIONAL_API == "https://ws.alibaba.ir/api/v1/flights/international/proposal-requests"
        assert scraper.DOMESTIC_API == "https://ws.alibaba.ir/api/v1/flights/domestic/available"

    def test_build_international_payload(self, sample_search_params):
        """Test building international search payload."""
        scraper = AlibabaScraper()
        payload = scraper._build_international_payload(sample_search_params)

        # Should add ALL suffix for international
        assert payload["origin"] == "THRALL"
        assert payload["destination"] == "MHDALL"
        assert payload["departureDate"] == "2025-01-15"
        assert payload["adult"] == 2
        assert payload["flightClass"] == "economy"

    def test_build_domestic_payload(self, sample_search_params):
        """Test building domestic search payload."""
        scraper = AlibabaScraper()
        payload = scraper._build_domestic_payload(sample_search_params)

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
        assert "ab-channel" in headers

    def test_build_deep_link(self, sample_search_params):
        """Test building deep link for booking."""
        scraper = AlibabaScraper()
        link = scraper._build_deep_link(sample_search_params)

        assert "alibaba.ir/flights/THR-MHD" in link
        assert "departing=2025-01-15" in link
        assert "adult=2" in link

    @pytest.mark.asyncio
    async def test_parse_proposal(self, sample_search_params):
        """Test parsing a flight proposal."""
        scraper = AlibabaScraper()

        mock_proposal = {
            "total": 79000000.0,
            "seat": 6,
            "isRefundable": True,
            "leavingFlightGroup": {
                "airlineName": "IRAN AIRTOUR",
                "origin": "TBZ",
                "destination": "IST",
                "departureDateTime": "2025-12-10T10:40:00",
                "arrivalDateTime": "2025-12-10T12:55:00",
                "durationMin": 165,
                "numberOfStop": 0,
                "cabinTypeName": "Economy",
                "flightDetails": [
                    {
                        "marketingCarrier": "B9",
                        "flightNumber": "9709",
                        "airlineName": "IRAN AIRTOUR",
                    }
                ],
            },
        }

        flight = scraper._parse_proposal(mock_proposal, sample_search_params)

        assert flight is not None
        assert flight.airline == "IRAN AIRTOUR"
        assert flight.origin == "TBZ"
        assert flight.destination == "IST"
        assert flight.price == 79000000.0
        assert flight.currency == "IRR"
        assert flight.stops == 0
        assert flight.duration_minutes == 165
        assert flight.seats_available == 6
        assert flight.is_refundable is True
        assert "B9" in flight.flight_number

    @pytest.mark.asyncio
    async def test_search_international_flow(self, sample_search_params):
        """Test the two-step international search flow."""
        async with AlibabaScraper() as scraper:
            # Mock POST response (step 1)
            mock_post_response = MagicMock()
            mock_post_response.json.return_value = {
                "result": {"requestId": "test-request-id-123"}
            }
            mock_post_response.raise_for_status = lambda: None

            # Mock GET response (step 2)
            mock_get_response = MagicMock()
            mock_get_response.json.return_value = {
                "result": {
                    "isCompleted": True,
                    "proposals": [
                        {
                            "total": 79000000.0,
                            "seat": 6,
                            "isRefundable": True,
                            "leavingFlightGroup": {
                                "airlineName": "Test Air",
                                "origin": "THR",
                                "destination": "IST",
                                "departureDateTime": "2025-01-15T10:00:00",
                                "arrivalDateTime": "2025-01-15T12:00:00",
                                "durationMin": 120,
                                "numberOfStop": 0,
                                "cabinTypeName": "Economy",
                                "flightDetails": [{"marketingCarrier": "TA", "flightNumber": "123"}],
                            },
                        }
                    ],
                }
            }
            mock_get_response.raise_for_status = lambda: None

            # Mock session methods
            scraper._session.post = AsyncMock(return_value=mock_post_response)
            scraper._session.get = AsyncMock(return_value=mock_get_response)

            flights = await scraper.search(sample_search_params, is_international=True)

            # Verify POST was called for proposal creation
            assert scraper._session.post.called
            # Verify GET was called to fetch results
            assert scraper._session.get.called
            # Verify we got flights
            assert len(flights) >= 1
            assert flights[0].airline == "Test Air"

    @pytest.mark.asyncio
    async def test_search_handles_errors(self, sample_search_params):
        """Test search handles API errors gracefully."""
        async with AlibabaScraper() as scraper:
            # Mock a failed request
            scraper._session.post = AsyncMock(side_effect=Exception("Network error"))

            flights = await scraper.search(sample_search_params)

            # Should return empty list on error
            assert flights == []

    @pytest.mark.asyncio
    async def test_search_handles_no_request_id(self, sample_search_params):
        """Test search handles missing requestId."""
        async with AlibabaScraper() as scraper:
            mock_response = MagicMock()
            mock_response.json.return_value = {"result": {}}
            mock_response.raise_for_status = lambda: None
            scraper._session.post = AsyncMock(return_value=mock_response)

            flights = await scraper.search(sample_search_params, is_international=True)

            assert flights == []
