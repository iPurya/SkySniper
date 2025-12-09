"""
Alibaba.ir flight scraper.

Alibaba is one of the largest Iranian online travel agencies.
Website: https://www.alibaba.ir

API Flow:
1. POST /proposal-requests - Create search request, get requestId
2. GET /proposal-requests/{requestId} - Poll for results until isCompleted=True
"""

import asyncio
import time
from datetime import datetime

from skysniper.scrapers.base import BaseScraper, Flight, SearchParams


class AlibabaScraper(BaseScraper):
    """Scraper for alibaba.ir flight data."""

    name = "alibaba"
    base_url = "https://www.alibaba.ir"

    # API endpoints
    API_BASE = "https://ws.alibaba.ir/api/v1/flights"
    DOMESTIC_API = f"{API_BASE}/domestic/available"
    INTERNATIONAL_API = f"{API_BASE}/international/proposal-requests"

    # Polling settings
    MAX_POLL_ATTEMPTS = 10
    DEFAULT_POLL_INTERVAL_MS = 2000

    async def search(self, params: SearchParams, is_international: bool = True) -> list[Flight]:
        """
        Search for flights on Alibaba.

        Args:
            params: Search parameters
            is_international: Whether this is an international flight

        Returns:
            List of Flight objects
        """
        flights = []

        try:
            if is_international:
                flights = await self._search_international(params)
            else:
                flights = await self._search_domestic(params)
        except Exception as e:
            print(f"[{self.name}] Search failed: {e}")

        return flights

    async def _search_international(self, params: SearchParams) -> list[Flight]:
        """Search for international flights using two-step API."""
        # Step 1: Create proposal request
        payload = self._build_international_payload(params)

        response = await self._session.post(
            self.INTERNATIONAL_API,
            json=payload,
            headers=self._get_headers(),
        )
        response.raise_for_status()
        data = response.json()

        request_id = data.get("result", {}).get("requestId")
        if not request_id:
            print(f"[{self.name}] No requestId in response")
            return []

        # Step 2: Poll for results
        return await self._poll_for_results(request_id, params)

    async def _poll_for_results(self, request_id: str, params: SearchParams) -> list[Flight]:
        """Poll the API until results are complete."""
        flights = []

        for attempt in range(self.MAX_POLL_ATTEMPTS):
            response = await self._session.get(
                f"{self.INTERNATIONAL_API}/{request_id}",
                headers=self._get_headers(),
            )
            response.raise_for_status()
            data = response.json()

            result = data.get("result", {})
            proposals = result.get("proposals", [])

            # Parse current proposals
            for proposal in proposals:
                flight = self._parse_proposal(proposal, params)
                if flight and flight not in flights:
                    flights.append(flight)

            # Check if search is complete
            if result.get("isCompleted", False):
                break

            # Wait before next poll
            poll_interval = result.get("nextRequestThreshold", self.DEFAULT_POLL_INTERVAL_MS)
            await asyncio.sleep(poll_interval / 1000)

        return flights

    async def _search_domestic(self, params: SearchParams) -> list[Flight]:
        """Search for domestic flights (single request)."""
        payload = self._build_domestic_payload(params)

        response = await self._session.post(
            self.DOMESTIC_API,
            json=payload,
            headers=self._get_headers(),
        )
        response.raise_for_status()
        data = response.json()

        flights = []
        departing = data.get("result", {}).get("departing", [])

        for item in departing:
            flight = self._parse_domestic_flight(item, params)
            if flight:
                flights.append(flight)

        return flights

    def _build_international_payload(self, params: SearchParams) -> dict:
        """Build payload for international flight search."""
        # International uses city codes with ALL suffix (e.g., THRALL, ISTALL)
        origin = params.origin.upper()
        destination = params.destination.upper()

        # Add ALL suffix if not present (for city-wide search)
        if not origin.endswith("ALL") and len(origin) == 3:
            origin = f"{origin}ALL"
        if not destination.endswith("ALL") and len(destination) == 3:
            destination = f"{destination}ALL"

        return {
            "origin": origin,
            "destination": destination,
            "departureDate": params.date,
            "adult": params.adults,
            "child": params.children,
            "infant": params.infants,
            "flightClass": params.cabin_class,
            "userVariant": None,
            "isReIssueRequest": False,
        }

    def _build_domestic_payload(self, params: SearchParams) -> dict:
        """Build payload for domestic flight search."""
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
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/",
            "ab-channel": "WEB-NEW,PRODUCTION,CSR,www.alibaba.ir,desktop,Chrome,120.0.0.0,N,N,Mac OS,10.15.7,3.221.4",
        }

    def _parse_proposal(self, proposal: dict, params: SearchParams) -> Flight | None:
        """
        Parse an international flight proposal.

        The proposal structure:
        - total: Total price
        - leavingFlightGroup: Flight group details
          - airlineName: Airline name
          - origin/destination: Airport codes
          - departureDateTime/arrivalDateTime: Times
          - durationMin: Duration in minutes
          - numberOfStop: Number of stops
          - cabinTypeName: Cabin class
          - flightDetails[]: Individual segments
        """
        try:
            flight_group = proposal.get("leavingFlightGroup")
            if not flight_group:
                return None

            # Get flight details (first segment for flight number)
            flight_details = flight_group.get("flightDetails", [])
            first_segment = flight_details[0] if flight_details else {}

            # Parse times
            departure_str = flight_group.get("departureDateTime", "")
            arrival_str = flight_group.get("arrivalDateTime", "")

            departure_time = datetime.fromisoformat(departure_str) if departure_str else datetime.now()
            arrival_time = datetime.fromisoformat(arrival_str) if arrival_str else datetime.now()

            # Build flight number from segments
            flight_numbers = [seg.get("flightNumber", "") for seg in flight_details]
            flight_number = "/".join(filter(None, flight_numbers))

            # Get marketing carrier code
            carrier_code = first_segment.get("marketingCarrier", "")
            if carrier_code and flight_numbers:
                flight_number = f"{carrier_code}{flight_numbers[0]}"
                if len(flight_numbers) > 1:
                    flight_number += f" (+{len(flight_numbers) - 1})"

            return Flight(
                origin=flight_group.get("origin", params.origin.upper()),
                destination=flight_group.get("destination", params.destination.upper()),
                departure_time=departure_time,
                arrival_time=arrival_time,
                airline=flight_group.get("airlineName", "Unknown"),
                flight_number=flight_number,
                price=float(proposal.get("total", 0)),
                currency="IRR",
                cabin_class=flight_group.get("cabinTypeName", "Economy").lower(),
                stops=flight_group.get("numberOfStop", 0),
                duration_minutes=flight_group.get("durationMin", 0),
                source=self.name,
                deep_link=self._build_deep_link(params),
                seats_available=proposal.get("seat", 0),
                is_refundable=proposal.get("isRefundable", False),
                raw_data=proposal,
            )
        except Exception as e:
            print(f"[{self.name}] Failed to parse proposal: {e}")
            return None

    def _parse_domestic_flight(self, item: dict, params: SearchParams) -> Flight | None:
        """Parse a domestic flight item."""
        try:
            departure_str = item.get("departureDateTime", "")
            arrival_str = item.get("arrivalDateTime", "")

            return Flight(
                origin=item.get("origin", params.origin.upper()),
                destination=item.get("destination", params.destination.upper()),
                departure_time=datetime.fromisoformat(departure_str) if departure_str else datetime.now(),
                arrival_time=datetime.fromisoformat(arrival_str) if arrival_str else datetime.now(),
                airline=item.get("airlineName", "Unknown"),
                flight_number=item.get("flightNumber", ""),
                price=float(item.get("adultPrice", item.get("price", 0))),
                currency="IRR",
                cabin_class=item.get("cabinType", "economy").lower(),
                stops=0,  # Domestic flights are typically non-stop
                duration_minutes=item.get("flightDuration", 0),
                source=self.name,
                deep_link=self._build_deep_link(params),
                raw_data=item,
            )
        except Exception as e:
            print(f"[{self.name}] Failed to parse domestic flight: {e}")
            return None

    def _build_deep_link(self, params: SearchParams) -> str:
        """Build a deep link to Alibaba for booking."""
        origin = params.origin.upper()
        dest = params.destination.upper()
        date = params.date

        return (
            f"{self.base_url}/flights/{origin}-{dest}"
            f"?departing={date}"
            f"&adult={params.adults}"
            f"&child={params.children}"
            f"&infant={params.infants}"
        )
