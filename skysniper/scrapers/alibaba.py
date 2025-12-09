"""
Alibaba.ir flight scraper.

Alibaba is one of the largest Iranian online travel agencies.
Website: https://www.alibaba.ir
"""

from datetime import datetime

from skysniper.scrapers.base import BaseScraper, Flight, SearchParams


class AlibabaScraper(BaseScraper):
    """Scraper for alibaba.ir flight data."""

    name = "alibaba"
    base_url = "https://www.alibaba.ir"

    # API endpoint for flight search
    SEARCH_API = "https://ws.alibaba.ir/api/v1/flights/domestic/available"

    async def search(self, params: SearchParams) -> list[Flight]:
        """
        Search for flights on Alibaba.

        Args:
            params: Search parameters

        Returns:
            List of Flight objects
        """
        flights = []

        # Build request payload
        payload = self._build_search_payload(params)

        try:
            response = await self._session.post(
                self.SEARCH_API,
                json=payload,
                headers=self._get_headers(),
            )
            response.raise_for_status()
            data = response.json()

            # Parse response into Flight objects
            flights = self._parse_response(data, params)

        except Exception as e:
            # TODO: Proper logging
            print(f"[{self.name}] Search failed: {e}")

        return flights

    def _build_search_payload(self, params: SearchParams) -> dict:
        """Build the API request payload."""
        return {
            "origin": params.origin.upper(),
            "destination": params.destination.upper(),
            "departureDate": params.date,
            "adult": params.adults,
            "child": params.children,
            "infant": params.infants,
        }

    def _get_headers(self) -> dict:
        """Get required headers for API requests."""
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/flights",
        }

    def _parse_response(self, data: dict, params: SearchParams) -> list[Flight]:
        """
        Parse API response into Flight objects.

        Args:
            data: Raw API response
            params: Original search params

        Returns:
            List of Flight objects
        """
        flights = []

        # TODO: Inspect actual API response structure and implement parsing
        # This is a skeleton - actual implementation requires API analysis

        results = data.get("result", {}).get("departing", [])

        for item in results:
            try:
                flight = self._parse_flight_item(item, params)
                if flight:
                    flights.append(flight)
            except Exception:
                # Skip malformed entries
                continue

        return flights

    def _parse_flight_item(self, item: dict, params: SearchParams) -> Flight | None:
        """Parse a single flight item from API response."""
        # TODO: Implement actual parsing based on API response structure
        # This requires inspecting the real API response

        # Placeholder structure - adjust based on actual API
        try:
            departure_str = item.get("departureDateTime", "")
            arrival_str = item.get("arrivalDateTime", "")

            return Flight(
                origin=params.origin.upper(),
                destination=params.destination.upper(),
                departure_time=datetime.fromisoformat(departure_str) if departure_str else datetime.now(),
                arrival_time=datetime.fromisoformat(arrival_str) if arrival_str else datetime.now(),
                airline=item.get("airlineName", "Unknown"),
                flight_number=item.get("flightNumber", ""),
                price=float(item.get("price", 0)),
                currency="IRR",
                cabin_class=params.cabin_class,
                stops=item.get("stops", 0),
                duration_minutes=item.get("duration", 0),
                source=self.name,
                deep_link=f"{self.base_url}/flights/{params.origin}-{params.destination}",
                raw_data=item,
            )
        except Exception:
            return None
