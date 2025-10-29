"""Squad leader agent for coordinating multi-agent collaboration."""

from typing import Optional

from .base_agent import BaseAgent
from .speaking_criteria import SquadLeaderCriteria, CompositeCriteria, DirectAddressCriteria


class SquadLeaderAgent(BaseAgent):
    """Squad leader agent with enhanced coordination capabilities.

    The squad leader has special responsibilities:
    - Coordinate team activities and task assignments
    - Respond to general questions and coordination requests
    - Monitor team progress and provide guidance
    - Handle situations where no other agent responds
    """

    def __init__(
        self,
        agent_id: str,
        callsign: str,
        system_prompt: Optional[str] = None,
        model: str = "claude-3-opus-20240229",
        temperature: float = 1.0,
        max_tokens: int = 1024
    ):
        """Initialize the squad leader agent.

        Args:
            agent_id: Unique identifier for the agent
            callsign: Radio callsign (typically includes "Lead")
            system_prompt: Optional custom system prompt
            model: Claude model to use
            temperature: Temperature for response generation
            max_tokens: Maximum tokens in response
        """
        # Use default squad leader prompt if not provided
        if system_prompt is None:
            system_prompt = self._default_squad_leader_prompt()

        # Squad leader uses composite criteria
        speaking_criteria = CompositeCriteria([
            DirectAddressCriteria(),
            SquadLeaderCriteria()
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

    def _default_squad_leader_prompt(self) -> str:
        """Get the default system prompt for squad leaders.

        Returns:
            Default squad leader system prompt
        """
        return """You are the SQUAD LEADER for this multi-agent team.

RESPONSIBILITIES:
- Coordinate team activities and assign tasks to team members
- Respond to general questions and provide guidance
- Monitor progress and ensure team objectives are met
- Step in when other agents need assistance or clarification
- Maintain situational awareness of all team activities

LEADERSHIP STYLE:
- Be decisive but collaborative
- Delegate to specialists when appropriate
- Provide clear, actionable guidance
- Acknowledge good work and contributions
- Keep communications efficient and professional

COORDINATION KEYWORDS:
When you see these keywords, take the lead:
- "help", "stuck", "unclear", "confused"
- "coordinate", "organize", "plan", "strategy"
- General questions without specific addressee
- Situations requiring team-level decisions

Remember: You're not just another agent - you're responsible for mission success.
Lead with confidence but respect your team's expertise."""

    def get_agent_type(self) -> str:
        """Get the agent type.

        Returns:
            "squad_leader"
        """
        return "squad_leader"

    def assign_task(
        self,
        target_callsign: str,
        task_description: str
    ) -> str:
        """Format a task assignment message.

        Args:
            target_callsign: Callsign of agent to assign task to
            task_description: Description of the task

        Returns:
            Formatted assignment message
        """
        return self.protocol.format(
            content=f"assigning you the following task: {task_description}",
            sender=self.callsign,
            recipient=target_callsign,
            add_over=True
        )

    def broadcast_to_team(
        self,
        message: str
    ) -> str:
        """Format a broadcast message to all team members.

        Args:
            message: Message content

        Returns:
            Formatted broadcast message
        """
        return self.protocol.format(
            content=message,
            sender=self.callsign,
            recipient="All units",
            add_over=True
        )

    def request_status(
        self,
        target_callsign: Optional[str] = None
    ) -> str:
        """Format a status request message.

        Args:
            target_callsign: Specific agent to request from, or None for all

        Returns:
            Formatted status request
        """
        recipient = target_callsign or "All units"
        return self.protocol.format(
            content="requesting status update",
            sender=self.callsign,
            recipient=recipient,
            add_over=True
        )
