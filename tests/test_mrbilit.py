"""
Tests for MrBilit scraper.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from skysniper.scrapers.mrbilit import MrbilitScraper
from skysniper.scrapers.base import SearchParams


class TestMrbilitScraper:
    """Tests for MrbilitScraper."""

    def test_mrbilit_scraper_attributes(self):
        """Test MrBilit scraper has correct attributes."""
        scraper = MrbilitScraper()
        assert scraper.name == "mrbilit"
        assert scraper.base_url == "https://mrbilit.com"
        assert "atighgasht.com" in scraper.API_URL

    def test_build_payload(self, sample_search_params):
        """Test building search payload."""
        scraper = MrbilitScraper()
        payload = scraper._build_payload(sample_search_params)

        assert payload["AdultCount"] == 2
        assert payload["ChildCount"] == 0
        assert payload["InfantCount"] == 0
        assert payload["CabinClass"] == "All"
        assert len(payload["Routes"]) == 1
        assert payload["Routes"][0]["OriginCode"] == "THR"
        assert payload["Routes"][0]["DestinationCode"] == "MHDALL"  # ALL suffix added
        assert payload["Routes"][0]["DepartureDate"] == "2025-01-15"

    def test_get_headers(self):
        """Test getting request headers."""
        scraper = MrbilitScraper()
        headers = scraper._get_headers()

        assert "Accept" in headers
        assert "Content-Type" in headers
        assert "Authorization" in headers
        assert "Bearer" in headers["Authorization"]
        assert "sessionid" in headers
        assert "x-playerid" in headers

    def test_build_deep_link(self, sample_search_params):
        """Test building deep link for booking."""
        scraper = MrbilitScraper()
        link = scraper._build_deep_link(sample_search_params)

        assert "mrbilit.com" in link
        assert "origin=THR" in link
        assert "destination=MHD" in link

    def test_parse_duration(self):
        """Test duration parsing."""
        scraper = MrbilitScraper()

        assert scraper._parse_duration("02:45:00") == 165
        assert scraper._parse_duration("00:30:00") == 30
        assert scraper._parse_duration("10:00:00") == 600
        assert scraper._parse_duration("invalid") == 0

    @pytest.mark.asyncio
    async def test_parse_flight(self, sample_search_params):
        """Test parsing a flight from API response."""
        scraper = MrbilitScraper()

        mock_flight_data = {
            "Id": "21590454",
            "Prices": [
                {
                    "Capacity": 5,
                    "BookingClass": "Y",
                    "PassengerFares": [
                        {"TotalFare": 72319000, "PaxType": "ADL"},
                        {"TotalFare": 72319000, "PaxType": "CHD"},
                    ],
                    "Baggage": 20,
                    "BaggageType": "KG",
                    "CabinClass": "Economy",
                    "IsCharter": True,
                }
            ],
            "Segments": [
                {
                    "TotalTime": "02:45:00",
                    "Legs": [
                        {
                            "FlightNumber": "7908",
                            "OriginCode": "TBZ",
                            "DestinationCode": "IST",
                            "AirlineCode": "IV",
                            "Airline": {
                                "EnglishTitle": "Caspian",
                                "PersianTitle": "کاسپین",
                            },
                            "DepartureTime": "2025-12-12T19:50:00+03:30",
                            "ArrivalTime": "2025-12-12T22:05:00+03:30",
                            "JourneyTime": "02:45:00",
                            "Stops": 0,
                        }
                    ],
                }
            ],
        }

        flights = scraper._parse_flight(mock_flight_data, sample_search_params)

        assert len(flights) == 1
        flight = flights[0]
        assert flight.airline == "Caspian"
        assert flight.origin == "TBZ"
        assert flight.destination == "IST"
        assert flight.price == 72319000
        assert flight.flight_number == "IV7908"
        assert flight.seats_available == 5
        assert flight.duration_minutes == 165
        assert flight.cabin_class == "economy"

    @pytest.mark.asyncio
    async def test_search_success(self, sample_search_params):
        """Test successful search."""
        async with MrbilitScraper() as scraper:
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "Meta": {"MinPrice": 72319000},
                "Flights": [
                    {
                        "Id": "test-flight",
                        "Prices": [
                            {
                                "Capacity": 5,
                                "PassengerFares": [{"TotalFare": 72319000, "PaxType": "ADL"}],
                                "CabinClass": "Economy",
                                "IsCharter": False,
                            }
                        ],
                        "Segments": [
                            {
                                "TotalTime": "02:45:00",
                                "Legs": [
                                    {
                                        "FlightNumber": "123",
                                        "OriginCode": "TBZ",
                                        "DestinationCode": "IST",
                                        "AirlineCode": "XX",
                                        "Airline": {"EnglishTitle": "Test Air"},
                                        "DepartureTime": "2025-12-12T10:00:00+03:30",
                                        "ArrivalTime": "2025-12-12T12:45:00+03:30",
                                        "JourneyTime": "02:45:00",
                                        "Stops": 0,
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
            mock_response.raise_for_status = lambda: None
            scraper._session.post = AsyncMock(return_value=mock_response)

            flights = await scraper.search(sample_search_params)

            assert scraper._session.post.called
            assert len(flights) == 1
            assert flights[0].price == 72319000

    @pytest.mark.asyncio
    async def test_search_handles_errors(self, sample_search_params):
        """Test search handles API errors gracefully."""
        async with MrbilitScraper() as scraper:
            scraper._session.post = AsyncMock(side_effect=Exception("Network error"))

            flights = await scraper.search(sample_search_params)

            assert flights == []

    @pytest.mark.asyncio
    async def test_search_empty_response(self, sample_search_params):
        """Test search with no flights available."""
        async with MrbilitScraper() as scraper:
            mock_response = MagicMock()
            mock_response.json.return_value = {"Meta": {}, "Flights": []}
            mock_response.raise_for_status = lambda: None
            scraper._session.post = AsyncMock(return_value=mock_response)

            flights = await scraper.search(sample_search_params)

            assert flights == []

    @pytest.mark.asyncio
    async def test_multiple_price_options(self, sample_search_params):
        """Test parsing flight with multiple fare classes."""
        scraper = MrbilitScraper()

        mock_flight_data = {
            "Id": "test",
            "Prices": [
                {
                    "Capacity": 5,
                    "PassengerFares": [{"TotalFare": 72000000, "PaxType": "ADL"}],
                    "CabinClass": "Economy",
                    "BookingClass": "Y",
                    "IsCharter": False,
                },
                {
                    "Capacity": 3,
                    "PassengerFares": [{"TotalFare": 115000000, "PaxType": "ADL"}],
                    "CabinClass": "Business",
                    "BookingClass": "C",
                    "IsCharter": False,
                },
            ],
            "Segments": [
                {
                    "TotalTime": "02:00:00",
                    "Legs": [
                        {
                            "FlightNumber": "100",
                            "OriginCode": "THR",
                            "DestinationCode": "IST",
                            "AirlineCode": "XX",
                            "Airline": {"EnglishTitle": "Test"},
                            "DepartureTime": "2025-01-15T10:00:00+03:30",
                            "ArrivalTime": "2025-01-15T12:00:00+03:30",
                            "JourneyTime": "02:00:00",
                            "Stops": 0,
                        }
                    ],
                }
            ],
        }

        flights = scraper._parse_flight(mock_flight_data, sample_search_params)

        # Should return 2 flights (one for each fare class)
        assert len(flights) == 2
        assert flights[0].price == 72000000
        assert flights[0].cabin_class == "economy"
        assert flights[1].price == 115000000
        assert flights[1].cabin_class == "business"
