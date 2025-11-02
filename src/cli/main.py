"""Main CLI entry point for multi-agent collaboration system."""

import asyncio
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .commands import demo_command, interactive_command


console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Multi-Agent Collaboration System.

    A Python-based multi-agent collaboration system featuring voice net protocol
    communication, squad-based coordination, and MCP tool integration.
    """
    pass


@cli.command()
def demo():
    """Run a simple demo with 2 agents exchanging messages."""
    asyncio.run(demo_command())


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to configuration file"
)
@click.option(
    "--agents",
    "-a",
    type=int,
    default=2,
    help="Number of agents to create (default: 2)"
)
def interactive(config, agents):
    """Start an interactive collaboration session."""
    asyncio.run(interactive_command(config, agents))


@cli.command()
def status():
    """Show system status and information."""
    console.print(Panel.fit(
        "[bold green]Multi-Agent Collaboration System[/bold green]\n"
        "Version: 0.1.0\n"
        "Status: Ready",
        title="System Status"
    ))

    # Show features
    table = Table(title="Features")
    table.add_column("Feature", style="cyan")
    table.add_column("Status", style="green")

    table.add_row("Voice Net Protocol", "✓ Enabled")
    table.add_row("Squad Leader", "✓ Enabled")
    table.add_row("MCP Integration", "○ Coming Soon")
    table.add_row("State Persistence", "○ Coming Soon")

    console.print(table)


if __name__ == "__main__":
    cli()
