"""CLI commands for multi-agent collaboration system."""

import os
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown

from ..agents.base_agent import BaseAgent
from ..agents.squad_leader import SquadLeaderAgent
from ..agents.speaking_criteria import KeywordCriteria, CompositeCriteria, DirectAddressCriteria
from ..channel.shared_channel import SharedChannel
from ..orchestration.orchestrator import Orchestrator


console = Console()


def demo_command():
    """Run a simple demo with 2 agents exchanging messages."""
    console.print(Panel.fit(
        "[bold cyan]Multi-Agent Demo[/bold cyan]\n"
        "Demonstrating 2 agents communicating via voice net protocol",
        title="Demo Mode"
    ))

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        console.print("[red]Error: ANTHROPIC_API_KEY environment variable not set[/red]")
        return

    try:
        # Create shared channel
        channel = SharedChannel()

        # Create orchestrator
        orchestrator = Orchestrator(channel=channel)

        # Create squad leader
        leader = SquadLeaderAgent(
            agent_id="leader_1",
            callsign="Alpha Lead"
        )

        # Create specialist agent
        specialist_prompt = """You are a specialist agent focusing on data analysis and problem-solving.

ROLE:
- Analyze data and provide insights
- Respond when your expertise is needed
- Support the squad leader's mission
- Collaborate with other team members

EXPERTISE AREAS:
- Data analysis and interpretation
- Problem decomposition
- Pattern recognition
- Strategic recommendations"""

        specialist = BaseAgent(
            agent_id="specialist_1",
            callsign="Alpha One",
            system_prompt=specialist_prompt,
            speaking_criteria=CompositeCriteria([
                DirectAddressCriteria(),
                KeywordCriteria(["data", "analyze", "analysis", "problem"])
            ])
        )

        # Add agents to orchestrator
        orchestrator.add_agent(leader)
        orchestrator.add_agent(specialist)
        orchestrator.start()

        console.print("\n[green]Agents initialized successfully![/green]\n")

        # Display agent info
        console.print("[bold]Squad Roster:[/bold]")
        console.print(f"  • {leader.callsign} (Squad Leader)")
        console.print(f"  • {specialist.callsign} (Data Specialist)\n")

        # Scenario 1: User asks a general question
        console.print("[bold yellow]--- Scenario 1: General Question ---[/bold yellow]\n")

        user_msg = "What's our current status?"
        console.print(f"[bold blue]User:[/bold blue] {user_msg}\n")

        orchestrator.run_turn(user_message=user_msg)

        # Show responses
        recent = channel.get_recent_messages(5)
        for msg in recent:
            if msg.sender_id != "user":
                console.print(f"[green]{msg.format_for_display()}[/green]")

        console.print("\n")

        # Scenario 2: Direct address to specialist
        console.print("[bold yellow]--- Scenario 2: Direct Address ---[/bold yellow]\n")

        user_msg = "Alpha One, I need you to analyze this data pattern."
        console.print(f"[bold blue]User:[/bold blue] {user_msg}\n")

        orchestrator.run_turn(user_message=user_msg)

        # Show responses
        recent = channel.get_recent_messages(5)
        for msg in recent[-3:]:
            if msg.sender_id not in ["user", "system"]:
                console.print(f"[green]{msg.format_for_display()}[/green]")

        console.print("\n")

        # Scenario 3: Keyword trigger
        console.print("[bold yellow]--- Scenario 3: Keyword Trigger ---[/bold yellow]\n")

        user_msg = "We need to analyze the problem and find a solution."
        console.print(f"[bold blue]User:[/bold blue] {user_msg}\n")

        orchestrator.run_turn(user_message=user_msg)

        # Show responses
        recent = channel.get_recent_messages(5)
        for msg in recent[-3:]:
            if msg.sender_id not in ["user", "system"]:
                console.print(f"[green]{msg.format_for_display()}[/green]")

        console.print("\n[bold green]Demo completed successfully![/bold green]")

        # Show full history
        console.print("\n[bold]Full Channel History:[/bold]")
        console.print(Panel(channel.format_history(20)))

    except Exception as e:
        console.print(f"[red]Error running demo: {e}[/red]")
        import traceback
        traceback.print_exc()


def interactive_command(config_path=None, num_agents=2):
    """Run an interactive collaboration session."""
    console.print(Panel.fit(
        "[bold cyan]Interactive Mode[/bold cyan]\n"
        "Type messages to communicate with agents. Type 'quit' to exit.",
        title="Multi-Agent Collaboration"
    ))

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        console.print("[red]Error: ANTHROPIC_API_KEY environment variable not set[/red]")
        return

    try:
        # Create shared channel and orchestrator
        channel = SharedChannel()
        orchestrator = Orchestrator(channel=channel)

        # Create squad leader
        leader = SquadLeaderAgent(
            agent_id="leader",
            callsign="Alpha Lead"
        )
        orchestrator.add_agent(leader)

        # Create additional agents
        if num_agents > 1:
            specialist = BaseAgent(
                agent_id="specialist",
                callsign="Alpha One",
                system_prompt="You are a specialist agent. Respond when addressed or when your expertise is needed.",
                speaking_criteria=CompositeCriteria([
                    DirectAddressCriteria(),
                    KeywordCriteria(["help", "analyze", "data"])
                ])
            )
            orchestrator.add_agent(specialist)

        orchestrator.start()

        console.print(f"\n[green]Session started with {orchestrator.get_agent_count()} agents[/green]\n")

        # Show roster
        for agent in orchestrator.get_active_agents():
            console.print(f"  • {agent.callsign} ({agent.get_agent_type()})")

        console.print("\n[dim]Type your messages below (or 'quit' to exit):[/dim]\n")

        # Interactive loop
        while True:
            try:
                user_input = Prompt.ask("[bold blue]You[/bold blue]")

                if user_input.lower() in ["quit", "exit", "q"]:
                    break

                if not user_input.strip():
                    continue

                # Send user message and get responses
                orchestrator.run_turn(user_message=user_input)

                # Display agent responses
                recent = channel.get_recent_messages(5)
                for msg in recent[-3:]:
                    if msg.sender_id not in ["user", "system"]:
                        console.print(f"\n[green]{msg.format_for_display()}[/green]\n")

            except KeyboardInterrupt:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

        orchestrator.stop()
        console.print("\n[yellow]Session ended.[/yellow]")

    except Exception as e:
        console.print(f"[red]Error in interactive mode: {e}[/red]")
        import traceback
        traceback.print_exc()
