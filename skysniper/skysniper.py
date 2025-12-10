"""
SkySniper - Find the Cheapest Flights, Automatically.
"""

import asyncio
from datetime import datetime

import click
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.spinner import Spinner
from rich.panel import Panel

from skysniper import __version__, __shortname__
from skysniper.scrapers import SCRAPERS, SearchParams, Flight

console = Console()


def format_price(price: float, currency: str = "IRR") -> str:
    """Format price with thousand separators."""
    if currency == "IRR":
        # Convert to Toman for readability (1 Toman = 10 Rial)
        toman = price / 10
        if toman >= 1_000_000:
            return f"{toman / 1_000_000:.1f}M ت"
        elif toman >= 1_000:
            return f"{toman / 1_000:.0f}K ت"
        return f"{toman:,.0f} ت"
    return f"{price:,.0f} {currency}"


def format_time(dt: datetime) -> str:
    """Format datetime to HH:MM."""
    return dt.strftime("%H:%M")


def format_duration(minutes: int) -> str:
    """Format duration as Xh Ym."""
    hours, mins = divmod(minutes, 60)
    return f"{hours}h {mins:02d}m"


async def run_all_scrapers(params: SearchParams, sources: list[str] | None = None) -> list[Flight]:
    """
    Run all (or selected) scrapers concurrently.

    Args:
        params: Search parameters
        sources: List of scraper names to use, or None for all

    Returns:
        Combined list of flights from all scrapers, sorted by price
    """
    all_flights = []

    # Filter scrapers if specific sources requested
    scrapers_to_use = SCRAPERS
    if sources:
        scrapers_to_use = {k: v for k, v in SCRAPERS.items() if k in sources}

    # Run scrapers concurrently
    async def run_scraper(name: str, scraper_class):
        try:
            async with scraper_class() as scraper:
                flights = await scraper.search(params)
                return flights
        except Exception as e:
            console.print(f"[dim red]⚠ {name}: {e}[/dim red]")
            return []

    tasks = [
        run_scraper(name, scraper_class)
        for name, scraper_class in scrapers_to_use.items()
    ]

    results = await asyncio.gather(*tasks)

    for flights in results:
        all_flights.extend(flights)

    # Sort by price (cheapest first)
    all_flights.sort(key=lambda f: f.price)

    return all_flights


def display_flights(flights: list[Flight], params: SearchParams):
    """Display flights in a rich table."""
    if not flights:
        console.print("\n[yellow]No flights found for this route and date.[/yellow]\n")
        return

    table = Table(
        title=f"✈️  Flights: {params.origin.upper()} → {params.destination.upper()} | {params.date}",
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
    )

    table.add_column("#", style="dim", width=3)
    table.add_column("Airline", style="white", width=18)
    table.add_column("Flight", style="dim", width=10)
    table.add_column("Departure", style="green", width=8)
    table.add_column("Arrival", style="green", width=8)
    table.add_column("Duration", style="dim", width=8)
    table.add_column("Stops", style="yellow", width=6)
    table.add_column("Price", style="bold green", justify="right", width=12)
    table.add_column("Seats", style="dim", width=6)
    table.add_column("Source", style="dim cyan", width=8)

    for idx, flight in enumerate(flights, 1):
        stops_str = "Direct" if flight.stops == 0 else f"{flight.stops} stop{'s' if flight.stops > 1 else ''}"
        seats_str = str(flight.seats_available) if flight.seats_available > 0 else "-"

        # Highlight cheapest flight
        row_style = "bold" if idx == 1 else None

        table.add_row(
            str(idx),
            flight.airline[:18],
            flight.flight_number[:10],
            format_time(flight.departure_time),
            format_time(flight.arrival_time),
            format_duration(flight.duration_minutes),
            stops_str,
            format_price(flight.price, flight.currency),
            seats_str,
            flight.source,
            style=row_style,
        )

    console.print()
    console.print(table)

    # Summary
    if flights:
        cheapest = flights[0]
        console.print(f"\n[bold green]💰 Cheapest:[/bold green] {cheapest.airline} at {format_price(cheapest.price, cheapest.currency)}")
        console.print(f"[dim]   Book at: {cheapest.deep_link}[/dim]\n")


@click.group()
@click.version_option(version=__version__, prog_name=__shortname__)
def cli():
    """✈️  SkySniper - Find the Cheapest Flights, Automatically."""
    pass


@cli.command()
@click.argument("origin")
@click.argument("destination")
@click.argument("date")
@click.option("--adults", "-a", default=1, help="Number of adult passengers")
@click.option("--children", "-c", default=0, help="Number of child passengers")
@click.option("--infants", "-i", default=0, help="Number of infant passengers")
@click.option("--source", "-s", multiple=True, help="Specific source(s) to search (default: all)")
@click.option("--domestic", "-d", is_flag=True, help="Search domestic flights only")
def search(origin: str, destination: str, date: str, adults: int, children: int, infants: int, source: tuple, domestic: bool):
    """
    Search for flights between two cities.

    \b
    ORIGIN      - Departure city code (e.g., THR, DXB, IST)
    DESTINATION - Arrival city code (e.g., IST, DXB, THR)
    DATE        - Flight date in YYYY-MM-DD format

    \b
    Examples:
      skysniper search TBZ IST 2025-01-15
      skysniper search THR MHD 2025-01-20 --domestic
      skysniper search THR DXB 2025-02-01 -a 2 -s alibaba
    """
    # Build search params
    params = SearchParams(
        origin=origin.upper(),
        destination=destination.upper(),
        date=date,
        adults=adults,
        children=children,
        infants=infants,
    )

    # Header
    console.print(f"\n[bold blue]✈️  SkySniper Search[/bold blue]")
    console.print(f"   [dim]Route:[/dim] {params.origin} → {params.destination}")
    console.print(f"   [dim]Date:[/dim] {params.date}")
    console.print(f"   [dim]Passengers:[/dim] {adults} adult(s), {children} child(ren), {infants} infant(s)")

    sources_list = list(source) if source else None
    if sources_list:
        console.print(f"   [dim]Sources:[/dim] {', '.join(sources_list)}")
    else:
        console.print(f"   [dim]Sources:[/dim] All ({len(SCRAPERS)} available)")

    # Show spinner while searching
    with console.status("[bold cyan]Searching flights...", spinner="dots"):
        flights = asyncio.run(run_all_scrapers(params, sources_list))

    # Display results
    display_flights(flights, params)


@cli.command()
def sources():
    """List all available flight data sources."""
    table = Table(title="Available Flight Sources")
    table.add_column("Name", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Website")

    # Dynamically load from scrapers registry
    source_info = {
        "alibaba": ("✅ Ready", "alibaba.ir"),
        "ataair": ("✅ Ready", "ataair.ir"),
        "mrbilit": ("✅ Ready", "mrbilit.com"),
    }

    for name, scraper_class in SCRAPERS.items():
        status, website = source_info.get(name, ("🔧 WIP", "N/A"))
        table.add_row(name.title(), status, website)

    console.print(table)
    console.print(f"\n[dim]Total: {len(SCRAPERS)} source(s) available[/dim]\n")


@cli.command()
@click.argument("origin")
@click.argument("destination")
@click.argument("date")
@click.option("--interval", "-n", default=30, help="Check interval in minutes")
@click.option("--target-price", "-t", type=float, help="Alert when price drops below this")
def monitor(origin: str, destination: str, date: str, interval: int, target_price: float | None):
    """
    Monitor a route for price drops.

    \b
    ORIGIN      - Departure city code
    DESTINATION - Arrival city code
    DATE        - Flight date in YYYY-MM-DD format

    \b
    Examples:
      skysniper monitor TBZ IST 2025-01-15
      skysniper monitor THR DXB 2025-02-01 -n 15 -t 50000000
    """
    params = SearchParams(
        origin=origin.upper(),
        destination=destination.upper(),
        date=date,
    )

    console.print(f"\n[bold green]👀 Price Monitor[/bold green]")
    console.print(f"   [dim]Route:[/dim] {params.origin} → {params.destination}")
    console.print(f"   [dim]Date:[/dim] {params.date}")
    console.print(f"   [dim]Interval:[/dim] Every {interval} minutes")
    if target_price:
        console.print(f"   [dim]Target:[/dim] Alert below {format_price(target_price)}")
    console.print()

    lowest_price = None
    check_count = 0

    try:
        while True:
            check_count += 1
            timestamp = datetime.now().strftime("%H:%M:%S")

            with console.status(f"[cyan]Check #{check_count} at {timestamp}...", spinner="dots"):
                flights = asyncio.run(run_all_scrapers(params))

            if flights:
                cheapest = flights[0]
                current_price = cheapest.price

                # Check for price drop
                if lowest_price is None:
                    lowest_price = current_price
                    console.print(f"[{timestamp}] 📊 Initial price: {format_price(current_price)} ({cheapest.airline})")
                elif current_price < lowest_price:
                    drop = lowest_price - current_price
                    drop_pct = (drop / lowest_price) * 100
                    console.print(f"[{timestamp}] [bold green]🔥 PRICE DROP![/bold green] {format_price(current_price)} (-{format_price(drop)}, -{drop_pct:.1f}%)")
                    lowest_price = current_price
                else:
                    console.print(f"[{timestamp}] [dim]💤 No change: {format_price(current_price)}[/dim]")

                # Check target price
                if target_price and current_price <= target_price:
                    console.print(f"\n[bold green]🎯 TARGET REACHED![/bold green] Price is now {format_price(current_price)}")
                    console.print(f"   Book at: {cheapest.deep_link}\n")
                    break
            else:
                console.print(f"[{timestamp}] [yellow]⚠ No flights found[/yellow]")

            # Wait for next check
            console.print(f"[dim]   Next check in {interval} minutes... (Ctrl+C to stop)[/dim]")
            asyncio.run(asyncio.sleep(interval * 60))

    except KeyboardInterrupt:
        console.print(f"\n[yellow]Monitoring stopped.[/yellow]")
        if lowest_price:
            console.print(f"[dim]Lowest price seen: {format_price(lowest_price)}[/dim]\n")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
