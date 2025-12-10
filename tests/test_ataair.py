"""
Tests for Ataair scraper.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from skysniper.scrapers.ataair import AtaairScraper
from skysniper.scrapers.base import SearchParams


class TestAtaairScraper:
    """Tests for AtaairScraper."""

    def test_ataair_scraper_attributes(self):
        """Test Ataair scraper has correct attributes."""
        scraper = AtaairScraper()
        assert scraper.name == "ataair"
        assert scraper.base_url == "https://app.ataair.ir"
        assert "reservationcoreapi.ataair.ir" in scraper.API_URL

    def test_build_payload(self, sample_search_params):
        """Test building search payload."""
        scraper = AtaairScraper()
        payload = scraper._build_payload(sample_search_params)

        assert payload["originIataCode"] == "THR"
        assert payload["destinationIataCode"] == "MHD"
        assert "2025-01-15" in payload["departureDate"]
        assert payload["adultCount"] == "2"  # String
        assert payload["childCount"] == "0"
        assert payload["airTripType"] == 0

    def test_get_headers(self):
        """Test getting request headers."""
        scraper = AtaairScraper()
        headers = scraper._get_headers()

        assert "Accept" in headers
        assert "Content-Type" in headers
        assert headers["Content-Type"] == "application/json"
        assert scraper.base_url in headers.get("Origin", "")

    def test_build_deep_link(self, sample_search_params):
        """Test building deep link for booking."""
        scraper = AtaairScraper()
        link = scraper._build_deep_link(sample_search_params)

        assert "ataair.ir" in link
        assert "origin=THR" in link
        assert "destination=MHD" in link

    @pytest.mark.asyncio
    async def test_parse_available(self, sample_search_params):
        """Test parsing a flight availability."""
        scraper = AtaairScraper()

        mock_available = {
            "totalPrice": 90669000,
            "seatRemain": 4,
            "originIataCode": "TBZ",
            "destinationIataCode": "IST",
            "flightItineraries": [
                {
                    "airlineName": "آتا",
                    "flightNumber": "6601",
                    "originIataCode": "TBZ",
                    "destinationIataCode": "IST",
                    "departureDateTime": "2025-12-11T08:30:00",
                    "arrivalDateTime": "2025-12-11T10:30:00",
                    "airlineCode": "I3",
                    "adultPrice": 90669000,
                    "cabinTypeName": "اکونومی",
                    "fareClass": "L",
                    "refundMethodType": "Online",
                }
            ],
            "refId": "test-ref-id",
        }

        flight = scraper._parse_available(mock_available, sample_search_params)

        assert flight is not None
        assert flight.airline == "Ata Airlines"
        assert flight.origin == "TBZ"
        assert flight.destination == "IST"
        assert flight.price == 90669000
        assert flight.currency == "IRR"
        assert flight.flight_number == "I36601"
        assert flight.seats_available == 4
        assert flight.is_refundable is True
        assert flight.cabin_class == "economy"
        assert flight.duration_minutes == 120  # 2 hours

    @pytest.mark.asyncio
    async def test_search_success(self, sample_search_params):
        """Test successful search."""
        async with AtaairScraper() as scraper:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "availables": [
                    {
                        "totalPrice": 81869000,
                        "seatRemain": 5,
                        "flightItineraries": [
                            {
                                "flightNumber": "6601",
                                "originIataCode": "TBZ",
                                "destinationIataCode": "IST",
                                "departureDateTime": "2025-12-11T08:30:00",
                                "arrivalDateTime": "2025-12-11T10:30:00",
                                "airlineCode": "I3",
                                "cabinTypeName": "اکونومی",
                                "refundMethodType": "Online",
                            }
                        ],
                    }
                ]
            }
            mock_response.raise_for_status = lambda: None
            scraper._session.post = AsyncMock(return_value=mock_response)

            flights = await scraper.search(sample_search_params)

            assert scraper._session.post.called
            assert len(flights) == 1
            assert flights[0].price == 81869000

    @pytest.mark.asyncio
    async def test_search_handles_errors(self, sample_search_params):
        """Test search handles API errors gracefully."""
        async with AtaairScraper() as scraper:
            scraper._session.post = AsyncMock(side_effect=Exception("Network error"))

            flights = await scraper.search(sample_search_params)

            assert flights == []

    @pytest.mark.asyncio
    async def test_search_empty_response(self, sample_search_params):
        """Test search with no flights available."""
        async with AtaairScraper() as scraper:
            mock_response = MagicMock()
            mock_response.json.return_value = {"availables": []}
            mock_response.raise_for_status = lambda: None
            scraper._session.post = AsyncMock(return_value=mock_response)

            flights = await scraper.search(sample_search_params)

            assert flights == []
