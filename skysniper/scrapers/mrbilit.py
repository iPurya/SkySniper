"""
MrBilit flight scraper.

MrBilit is an Iranian online travel agency.
Website: https://mrbilit.com
API: https://flight.atighgasht.com

API: Single POST request returns all available flights directly.
"""

import uuid
from datetime import datetime

from skysniper.scrapers.base import BaseScraper, Flight, SearchParams


class MrbilitScraper(BaseScraper):
    """Scraper for mrbilit.com flight data."""

    name = "mrbilit"
    base_url = "https://mrbilit.com"

    # API endpoint (different domain)
    API_URL = "https://flight.atighgasht.com/api/Flights"

    # Static bearer token from the website
    BEARER_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJidXMiOiI0ZiIsInRybiI6IjE3Iiwic3JjIjoiMiJ9.vvpr9fgASvk7B7I4KQKCz-SaCmoErab_p3csIvULG1w"

    async def search(self, params: SearchParams) -> list[Flight]:
        """
        Search for flights on MrBilit.

        Args:
            params: Search parameters

        Returns:
            List of Flight objects
        """
        flights = []

        try:
            payload = self._build_payload(params)
            response = await self._session.post(
                self.API_URL,
                json=payload,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            data = response.json()

            # Parse flights
            for flight_data in data.get("Flights", []):
                parsed_flights = self._parse_flight(flight_data, params)
                flights.extend(parsed_flights)

        except Exception as e:
            print(f"[{self.name}] Search failed: {e}")

        return flights

    def _build_payload(self, params: SearchParams) -> dict:
        """Build the API request payload."""
        # For international destinations, add ALL suffix
        dest_code = params.destination.upper()
        if len(dest_code) == 3:
            dest_code = f"{dest_code}ALL"

        return {
            "AdultCount": params.adults,
            "ChildCount": params.children,
            "InfantCount": params.infants,
            "CabinClass": "All",
            "Routes": [
                {
                    "OriginCode": params.origin.upper(),
                    "DestinationCode": dest_code,
                    "DepartureDate": params.date,
                }
            ],
            "Baggage": True,
            "IncludeFlightsWithHigherCapacity": False,
        }

    def _get_headers(self) -> dict:
        """Get required headers for API requests."""
        session_id = f"session_{uuid.uuid4()}"
        player_id = str(uuid.uuid4())

        return {
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json-patch+json",
            "Authorization": f"Bearer {self.BEARER_TOKEN}",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/",
            "sessionid": session_id,
            "x-playerid": player_id,
        }

    def _parse_flight(self, flight_data: dict, params: SearchParams) -> list[Flight]:
        """
        Parse a flight and its price options.

        Each flight can have multiple price options (different fare classes).

        Response structure:
        - Prices[]: List of price options
        - Segments[]: Flight segments with Legs[]
        """
        flights = []

        segments = flight_data.get("Segments", [])
        if not segments:
            return flights

        # Get first segment and leg for flight info
        first_segment = segments[0]
        legs = first_segment.get("Legs", [])
        if not legs:
            return flights

        first_leg = legs[0]

        # Parse times
        departure_str = first_leg.get("DepartureTime", "")
        arrival_str = first_leg.get("ArrivalTime", "")

        try:
            # Handle timezone in ISO format: 2025-12-12T19:50:00+03:30
            departure_time = datetime.fromisoformat(departure_str) if departure_str else datetime.now()
            arrival_time = datetime.fromisoformat(arrival_str) if arrival_str else datetime.now()
        except ValueError:
            departure_time = datetime.now()
            arrival_time = datetime.now()

        # Parse duration from JourneyTime (e.g., "02:45:00")
        journey_time = first_leg.get("JourneyTime", "00:00:00")
        duration_minutes = self._parse_duration(journey_time)

        # If duration is 0, try to calculate from segment TotalTime
        if duration_minutes == 0:
            total_time = first_segment.get("TotalTime", "00:00:00")
            duration_minutes = self._parse_duration(total_time)

        # Get airline info
        airline_info = first_leg.get("Airline", {})
        airline_name = airline_info.get("EnglishTitle") or airline_info.get("PersianTitle", "Unknown")
        airline_code = first_leg.get("AirlineCode", "")
        flight_number = first_leg.get("FlightNumber", "")

        # Origin/Destination
        origin = first_leg.get("OriginCode", params.origin.upper())
        destination = first_leg.get("DestinationCode", params.destination.upper())

        # Calculate stops (total legs - 1)
        total_stops = sum(leg.get("Stops", 0) for leg in legs)
        if len(legs) > 1:
            total_stops += len(legs) - 1

        # Parse each price option
        for price_option in flight_data.get("Prices", []):
            try:
                # Get adult fare
                passenger_fares = price_option.get("PassengerFares", [])
                adult_fare = next(
                    (f for f in passenger_fares if f.get("PaxType") == "ADL"),
                    passenger_fares[0] if passenger_fares else {}
                )
                price = float(adult_fare.get("TotalFare", 0))

                # Cabin class
                cabin_class = price_option.get("CabinClass", "Economy").lower()

                # Capacity
                capacity = price_option.get("Capacity", 0)

                # Charter or system flight
                is_charter = price_option.get("IsCharter", False)

                flight = Flight(
                    origin=origin,
                    destination=destination,
                    departure_time=departure_time,
                    arrival_time=arrival_time,
                    airline=airline_name,
                    flight_number=f"{airline_code}{flight_number}",
                    price=price,
                    currency="IRR",
                    cabin_class=cabin_class,
                    stops=total_stops,
                    duration_minutes=duration_minutes,
                    source=self.name,
                    deep_link=self._build_deep_link(params),
                    seats_available=capacity,
                    is_refundable=not is_charter,  # Charter flights usually non-refundable
                    raw_data={
                        "flight_id": flight_data.get("Id"),
                        "booking_class": price_option.get("BookingClass"),
                        "is_charter": is_charter,
                        "baggage": price_option.get("Baggage"),
                        "baggage_type": price_option.get("BaggageType"),
                    },
                )
                flights.append(flight)

            except Exception as e:
                print(f"[{self.name}] Failed to parse price option: {e}")
                continue

        return flights

    def _parse_duration(self, time_str: str) -> int:
        """Parse duration string (HH:MM:SS) to minutes."""
        try:
            parts = time_str.split(":")
            if len(parts) >= 2:
                hours = int(parts[0])
                minutes = int(parts[1])
                return hours * 60 + minutes
        except (ValueError, IndexError):
            pass
        return 0

    def _build_deep_link(self, params: SearchParams) -> str:
        """Build a deep link to MrBilit for booking."""
        return (
            f"{self.base_url}/flight/search"
            f"?origin={params.origin.upper()}"
            f"&destination={params.destination.upper()}"
            f"&date={params.date}"
            f"&adult={params.adults}"
            f"&child={params.children}"
            f"&infant={params.infants}"
        )
