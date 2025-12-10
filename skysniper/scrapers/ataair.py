"""
Ataair.ir flight scraper.

Ata Airlines is an Iranian airline.
Website: https://app.ataair.ir

API: Single POST request returns all available flights directly.
"""

from datetime import datetime

from skysniper.scrapers.base import BaseScraper, Flight, SearchParams


class AtaairScraper(BaseScraper):
    """Scraper for ataair.ir flight data."""

    name = "ataair"
    base_url = "https://app.ataair.ir"

    # API endpoint
    API_URL = "https://reservationcoreapi.ataair.ir/Reservation/v1/Flight-api/Available/GetAvailable"

    async def search(self, params: SearchParams) -> list[Flight]:
        """
        Search for flights on Ataair.

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

            # Parse availables
            availables = data.get("availables", [])
            for item in availables:
                flight = self._parse_available(item, params)
                if flight:
                    flights.append(flight)

        except Exception as e:
            print(f"[{self.name}] Search failed: {e}")

        return flights

    def _build_payload(self, params: SearchParams) -> dict:
        """Build the API request payload."""
        # Format date with timezone (Iran Standard Time +03:30)
        departure_date = f"{params.date}T00:00:00+03:30"

        return {
            "originIataCode": params.origin.upper(),
            "destinationIataCode": params.destination.upper(),
            "departureDate": departure_date,
            "adultCount": str(params.adults),  # API expects string
            "childCount": str(params.children),
            "infantCount": str(params.infants),
            "airTripType": 0,  # One-way
            "flightLegType": 0,  # Departure
            "flightReservationType": 0,
        }

    def _get_headers(self) -> dict:
        """Get required headers for API requests."""
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/",
        }

    def _parse_available(self, item: dict, params: SearchParams) -> Flight | None:
        """
        Parse a flight availability item.

        Response structure:
        - totalPrice: Total price in IRR
        - seatRemain: Available seats
        - flightItineraries[]: Flight segments
        - refId: Reference ID for booking
        """
        try:
            # Get first flight itinerary (for direct flights)
            itineraries = item.get("flightItineraries", [])
            if not itineraries:
                return None

            first_leg = itineraries[0]

            # Parse times
            departure_str = first_leg.get("departureDateTime", "")
            arrival_str = first_leg.get("arrivalDateTime", "")

            departure_time = datetime.fromisoformat(departure_str) if departure_str else datetime.now()
            arrival_time = datetime.fromisoformat(arrival_str) if arrival_str else datetime.now()

            # Calculate duration
            duration_minutes = 0
            if departure_time and arrival_time:
                delta = arrival_time - departure_time
                duration_minutes = int(delta.total_seconds() / 60)

            # Build flight number
            airline_code = first_leg.get("airlineCode", "I3")
            flight_number = first_leg.get("flightNumber", "")
            full_flight_number = f"{airline_code}{flight_number}"

            # Map Persian cabin names to English
            cabin_map = {
                "اکونومی": "economy",
                "بیزینس": "business",
                "فرست کلاس": "first",
            }
            cabin_persian = first_leg.get("cabinTypeName", "اکونومی")
            cabin_class = cabin_map.get(cabin_persian, "economy")

            # Check if refundable
            refund_type = first_leg.get("refundMethodType", "")
            is_refundable = refund_type.lower() == "online"

            return Flight(
                origin=first_leg.get("originIataCode", params.origin.upper()),
                destination=first_leg.get("destinationIataCode", params.destination.upper()),
                departure_time=departure_time,
                arrival_time=arrival_time,
                airline="Ata Airlines",
                flight_number=full_flight_number,
                price=float(item.get("totalPrice", 0)),
                currency="IRR",
                cabin_class=cabin_class,
                stops=len(itineraries) - 1,  # Number of connections
                duration_minutes=duration_minutes,
                source=self.name,
                deep_link=self._build_deep_link(params),
                seats_available=item.get("seatRemain", 0),
                is_refundable=is_refundable,
                raw_data=item,
            )

        except Exception as e:
            print(f"[{self.name}] Failed to parse flight: {e}")
            return None

    def _build_deep_link(self, params: SearchParams) -> str:
        """Build a deep link to Ataair for booking."""
        return (
            f"{self.base_url}/flight/available"
            f"?origin={params.origin.upper()}"
            f"&destination={params.destination.upper()}"
            f"&date={params.date}"
        )
