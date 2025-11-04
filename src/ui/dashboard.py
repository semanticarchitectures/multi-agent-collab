"""Real-time dashboard for multi-agent collaboration monitoring.

Provides live visual display of:
- Agent status and activity
- Message flow and conversations
- Agent memory and context
- Mission statistics
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import deque

from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.console import Console, Group
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn

from ..agents.base_agent import BaseAgent
from ..channel.message import Message, MessageType


class Dashboard:
    """Real-time dashboard for multi-agent system monitoring."""

    def __init__(self, max_messages: int = 20):
        """Initialize the dashboard.

        Args:
            max_messages: Maximum messages to display in message panel
        """
        self.console = Console()
        self.layout = Layout()
        self.messages = deque(maxlen=max_messages)
        self.mission_data = {}
        self.agents = []
        self.start_time = datetime.now()

        # Create layout structure
        self._create_layout()

    def _create_layout(self):
        """Create the dashboard layout structure."""
        # Main layout: header, body, footer
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )

        # Body split into three columns
        self.layout["body"].split_row(
            Layout(name="agents", ratio=1),
            Layout(name="messages", ratio=2),
            Layout(name="memory", ratio=1)
        )

    def render_header(self) -> Panel:
        """Render the header panel.

        Returns:
            Rich Panel with header content
        """
        elapsed = datetime.now() - self.start_time
        elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds

        header_text = Text()
        header_text.append("🚁 ", style="bold")
        header_text.append("MULTI-AGENT COLLABORATION SYSTEM", style="bold cyan")
        header_text.append(f"  |  Mission Time: {elapsed_str}", style="dim")
        header_text.append(f"  |  Agents: {len(self.agents)}", style="dim")
        header_text.append(f"  |  Messages: {len(self.messages)}", style="dim")

        return Panel(header_text, style="bold white on blue")

    def render_agents(self) -> Panel:
        """Render the agent status panel.

        Returns:
            Rich Panel with agent information
        """
        if not self.agents:
            return Panel(
                "[dim]No agents active[/dim]",
                title="[bold cyan]Agent Status[/bold cyan]",
                border_style="cyan"
            )

        table = Table(show_header=True, header_style="bold cyan", box=None, padding=(0, 1))
        table.add_column("Callsign", style="cyan", no_wrap=True)
        table.add_column("Type", style="yellow")
        table.add_column("Memory", justify="right", style="magenta")

        for agent in self.agents:
            # Get agent type
            agent_type = agent.get_agent_type()
            type_display = "🎖️ LEAD" if agent_type == "squad_leader" else f"👤 {agent_type.upper()}"

            # Get memory summary
            memory_summary = agent.get_memory_summary()
            total_items = sum(memory_summary.values())
            memory_display = f"{total_items} items"

            # Style based on activity (could track last response time)
            style = "green" if total_items > 0 else "dim"

            table.add_row(
                agent.callsign,
                type_display,
                memory_display,
                style=style
            )

        return Panel(
            table,
            title="[bold cyan]Agent Status[/bold cyan]",
            border_style="cyan"
        )

    def render_messages(self) -> Panel:
        """Render the message panel with scrolling conversation.

        Returns:
            Rich Panel with message history
        """
        if not self.messages:
            return Panel(
                "[dim]Waiting for communications...[/dim]",
                title="[bold green]Communications[/bold green]",
                border_style="green"
            )

        # Build message display
        message_lines = []
        for msg in self.messages:
            # Format timestamp
            time_str = msg.timestamp.strftime("%H:%M:%S")

            # Color code by type
            if msg.message_type == MessageType.USER:
                sender_style = "bold yellow"
                prefix = "🎯"
            elif msg.message_type == MessageType.SYSTEM:
                sender_style = "bold blue"
                prefix = "ℹ️"
            else:
                sender_style = "bold green"
                prefix = "📡"

            # Format message
            sender = msg.sender_callsign or msg.sender_id
            content = msg.content

            # Truncate long messages
            if len(content) > 150:
                content = content[:147] + "..."

            # Create line
            line = Text()
            line.append(f"{prefix} ", style="dim")
            line.append(f"[{time_str}] ", style="dim")
            line.append(f"{sender}: ", style=sender_style)
            line.append(content)

            message_lines.append(line)

        return Panel(
            Group(*message_lines),
            title="[bold green]Communications[/bold green]",
            border_style="green"
        )

    def render_memory(self) -> Panel:
        """Render the memory/context panel.

        Returns:
            Rich Panel with agent memory information
        """
        if not self.agents:
            return Panel(
                "[dim]No memory data[/dim]",
                title="[bold magenta]Agent Memory[/bold magenta]",
                border_style="magenta"
            )

        # Show memory for most active agent or first agent
        active_agent = self.agents[0]
        if len(self.agents) > 1:
            # Find agent with most memory
            max_items = 0
            for agent in self.agents:
                items = sum(agent.get_memory_summary().values())
                if items > max_items:
                    max_items = items
                    active_agent = agent

        # Build memory display
        memory_text = []
        memory_text.append(Text(f"Agent: {active_agent.callsign}", style="bold cyan"))
        memory_text.append(Text())

        # Tasks
        if active_agent.memory.get('task_list'):
            memory_text.append(Text("📋 Active Tasks:", style="bold yellow"))
            for task in active_agent.memory['task_list'][-5:]:  # Last 5
                task_text = Text()
                task_text.append("  • ", style="dim")
                task_text.append(task[:60] if len(task) > 60 else task)
                memory_text.append(task_text)
            memory_text.append(Text())

        # Facts
        if active_agent.memory.get('key_facts'):
            memory_text.append(Text("💡 Key Facts:", style="bold blue"))
            for key, value in list(active_agent.memory['key_facts'].items())[-3:]:  # Last 3
                fact_text = Text()
                fact_text.append("  • ", style="dim")
                fact_text.append(f"{key}: ", style="cyan")
                fact_text.append(value[:40] if len(value) > 40 else value)
                memory_text.append(fact_text)
            memory_text.append(Text())

        # Concerns
        if active_agent.memory.get('concerns'):
            memory_text.append(Text("⚠️  Concerns:", style="bold red"))
            for concern in active_agent.memory['concerns'][-3:]:  # Last 3
                concern_text = Text()
                concern_text.append("  • ", style="dim")
                concern_text.append(concern[:60] if len(concern) > 60 else concern)
                memory_text.append(concern_text)

        if not any([active_agent.memory.get('task_list'),
                    active_agent.memory.get('key_facts'),
                    active_agent.memory.get('concerns')]):
            memory_text.append(Text("(No memory stored yet)", style="dim"))

        return Panel(
            Group(*memory_text),
            title="[bold magenta]Agent Memory[/bold magenta]",
            border_style="magenta"
        )

    def render_footer(self) -> Panel:
        """Render the footer panel.

        Returns:
            Rich Panel with footer content
        """
        footer_text = Text()
        footer_text.append("Press ", style="dim")
        footer_text.append("Ctrl+C", style="bold red")
        footer_text.append(" to exit  |  ", style="dim")
        footer_text.append("Rich Dashboard v1.0", style="dim italic")

        return Panel(footer_text, style="dim white on black")

    def update(self):
        """Update all panels with current data."""
        self.layout["header"].update(self.render_header())
        self.layout["agents"].update(self.render_agents())
        self.layout["messages"].update(self.render_messages())
        self.layout["memory"].update(self.render_memory())
        self.layout["footer"].update(self.render_footer())

    def add_message(self, message: Message):
        """Add a message to the display.

        Args:
            message: Message to add
        """
        self.messages.append(message)

    def set_agents(self, agents: List[BaseAgent]):
        """Set the list of agents to monitor.

        Args:
            agents: List of agent instances
        """
        self.agents = agents

    def set_mission_data(self, data: Dict[str, Any]):
        """Set mission-specific data.

        Args:
            data: Mission data dictionary
        """
        self.mission_data = data

    def clear_messages(self):
        """Clear the message history."""
        self.messages.clear()


def create_dashboard(agents: Optional[List[BaseAgent]] = None) -> Dashboard:
    """Factory function to create a configured dashboard.

    Args:
        agents: Optional list of agents to monitor

    Returns:
        Configured Dashboard instance
    """
    dashboard = Dashboard()
    if agents:
        dashboard.set_agents(agents)
    return dashboard
