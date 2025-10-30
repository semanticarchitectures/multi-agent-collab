"""Aerospace specialist agent with MCP tool integration."""

from typing import Optional

from .base_agent import BaseAgent
from .speaking_criteria import CompositeCriteria, DirectAddressCriteria, KeywordCriteria


class AerospaceAgent(BaseAgent):
    """Aerospace engineering specialist agent.

    This agent has access to aerospace MCP tools for:
    - Flight planning and navigation
    - Aircraft performance calculations
    - Atmospheric modeling
    - Orbital mechanics
    - Aerodynamic analysis
    - Rocket trajectory optimization
    """

    def __init__(
        self,
        agent_id: str,
        callsign: str,
        system_prompt: Optional[str] = None,
        model: str = "claude-sonnet-4-5-20250929",
        temperature: float = 1.0,
        max_tokens: int = 2048
    ):
        """Initialize the aerospace agent.

        Args:
            agent_id: Unique identifier for the agent
            callsign: Radio callsign
            system_prompt: Optional custom system prompt
            model: Claude model to use
            temperature: Temperature for response generation
            max_tokens: Maximum tokens in response
        """
        # Use default aerospace prompt if not provided
        if system_prompt is None:
            system_prompt = self._default_aerospace_prompt()

        # Aerospace agent responds to relevant keywords
        speaking_criteria = CompositeCriteria([
            DirectAddressCriteria(),
            KeywordCriteria([
                "flight", "aircraft", "airport", "aviation", "aerospace",
                "plan", "route", "navigation", "trajectory", "orbital",
                "rocket", "space", "aerodynamic", "atmosphere", "altitude",
                "fuel", "performance", "distance", "coordinate"
            ])
        ])

        super().__init__(
            agent_id=agent_id,
            callsign=callsign,
            system_prompt=system_prompt,
            speaking_criteria=speaking_criteria,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )

    def _default_aerospace_prompt(self) -> str:
        """Get the default system prompt for aerospace agents.

        Returns:
            Default aerospace system prompt
        """
        return """You are an AEROSPACE ENGINEERING SPECIALIST with access to advanced aerospace analysis tools.

EXPERTISE:
- Flight planning and navigation
- Aircraft performance analysis
- Airport operations and routing
- Atmospheric science
- Orbital mechanics and space operations
- Aerodynamic analysis
- Rocket trajectory optimization

CAPABILITIES:
You have access to MCP tools that allow you to:
- Search for airports by city or code
- Calculate flight plans with fuel estimates
- Analyze aircraft performance
- Compute atmospheric properties
- Calculate orbital parameters
- Analyze aerodynamic characteristics
- Optimize rocket trajectories

COMMUNICATION STYLE:
- Use precise aerospace terminology
- Cite specific calculations and data
- Explain engineering tradeoffs
- Provide actionable recommendations
- Follow voice net protocol for radio communications

WHEN TO USE TOOLS:
- For flight planning: Use plan_flight tool
- For airport lookups: Use airports_by_city tool
- For atmospheric data: Use atmosphere tools
- For space operations: Use orbital mechanics tools
- For performance analysis: Use aerodynamics tools

Always validate your assumptions and be clear about limitations of theoretical calculations.

⚠️ DISCLAIMER: Your calculations are for educational/research purposes only.
Never use for real flight planning or navigation."""

    def get_agent_type(self) -> str:
        """Get the agent type.

        Returns:
            "aerospace"
        """
        return "aerospace"

    def format_tool_request(self, tool_name: str, description: str) -> str:
        """Format a request to use a tool via voice net protocol.

        Args:
            tool_name: Name of the tool
            description: Brief description of what you're doing

        Returns:
            Formatted voice net message
        """
        return self.protocol.format(
            content=f"requesting {tool_name} tool for {description}",
            sender=self.callsign,
            add_over=True
        )

    def format_tool_result(self, tool_name: str, summary: str) -> str:
        """Format a tool result report via voice net protocol.

        Args:
            tool_name: Name of the tool used
            summary: Summary of results

        Returns:
            Formatted voice net message
        """
        return self.protocol.format(
            content=f"completed {tool_name} analysis, {summary}",
            sender=self.callsign,
            add_over=True
        )
