"""
Base scraper class for all flight data sources.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Flight:
    """Represents a single flight option."""

    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    airline: str
    flight_number: str
    price: float
    currency: str
    cabin_class: str = "economy"
    stops: int = 0
    duration_minutes: int = 0
    source: str = ""  # Which scraper found this flight
    deep_link: str = ""  # URL to book
    seats_available: int = 0  # Number of seats left
    is_refundable: bool = False  # Can be refunded
    raw_data: dict = field(default_factory=dict)

    @property
    def duration_formatted(self) -> str:
        """Return duration as 'Xh Ym' format."""
        hours, minutes = divmod(self.duration_minutes, 60)
        return f"{hours}h {minutes}m"

    def __str__(self) -> str:
        return (
            f"{self.airline} {self.flight_number} | "
            f"{self.origin}→{self.destination} | "
            f"{self.departure_time.strftime('%H:%M')} - {self.arrival_time.strftime('%H:%M')} | "
            f"{self.price:,.0f} {self.currency}"
        )


@dataclass
class SearchParams:
    """Parameters for a flight search."""

    origin: str
    destination: str
    date: str  # YYYY-MM-DD format
    adults: int = 1
    children: int = 0
    infants: int = 0
    cabin_class: str = "economy"


class BaseScraper(ABC):
    """
    Abstract base class for all flight scrapers.

    Each scraper must implement:
    - name: Identifier for the source
    - search(): Fetch flights for given parameters
    """

    name: str = "base"
    base_url: str = ""

    def __init__(self):
        self._session = None

    @abstractmethod
    async def search(self, params: SearchParams) -> list[Flight]:
        """
        Search for flights with the given parameters.

        Args:
            params: Search parameters (origin, destination, date, passengers)

        Returns:
            List of Flight objects found
        """
        pass

    async def __aenter__(self):
        """Async context manager entry."""
        await self._init_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._close_session()

    async def _init_session(self):
        """Initialize HTTP session. Override if needed."""
        import httpx
        self._session = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        )

    async def _close_session(self):
        """Close HTTP session."""
        if self._session:
            await self._session.aclose()
            self._session = None

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} ({self.name})>"
