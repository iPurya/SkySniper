"""
SkySniper - Find the Cheapest Flights, Automatically.
"""

import click
from rich.console import Console
from rich.table import Table

from skysniper import __version__, __shortname__

console = Console()


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
def search(origin: str, destination: str, date: str, adults: int, children: int, infants: int):
    """
    Search for flights between two cities.

    \b
    ORIGIN      - Departure city code (e.g., THR, DXB, IST)
    DESTINATION - Arrival city code (e.g., IST, DXB, THR)
    DATE        - Flight date in YYYY-MM-DD format
    """
    console.print(f"\n[bold blue]✈️  Searching flights...[/bold blue]")
    console.print(f"   [dim]Route:[/dim] {origin.upper()} → {destination.upper()}")
    console.print(f"   [dim]Date:[/dim] {date}")
    console.print(f"   [dim]Passengers:[/dim] {adults} adult(s), {children} child(ren), {infants} infant(s)\n")

    # TODO: Implement actual scraping
    console.print("[yellow]⚠️  Scraping not yet implemented. Coming soon![/yellow]\n")


@cli.command()
def sources():
    """List all available flight data sources."""
    table = Table(title="Available Sources")
    table.add_column("Source", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Description")

    # TODO: Dynamically load from scrapers
    table.add_row("Alibaba", "🔧 WIP", "alibaba.ir - Iranian flight booking")

    console.print(table)


@cli.command()
@click.argument("origin")
@click.argument("destination")
@click.argument("date")
@click.option("--interval", "-n", default=30, help="Check interval in minutes")
def monitor(origin: str, destination: str, date: str, interval: int):
    """
    Monitor a route for price drops.

    \b
    ORIGIN      - Departure city code
    DESTINATION - Arrival city code
    DATE        - Flight date in YYYY-MM-DD format
    """
    console.print(f"\n[bold green]👀 Monitoring started[/bold green]")
    console.print(f"   [dim]Route:[/dim] {origin.upper()} → {destination.upper()}")
    console.print(f"   [dim]Date:[/dim] {date}")
    console.print(f"   [dim]Interval:[/dim] Every {interval} minutes\n")

    # TODO: Implement monitoring loop
    console.print("[yellow]⚠️  Monitoring not yet implemented. Coming soon![/yellow]\n")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
