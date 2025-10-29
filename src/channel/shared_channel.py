"""Shared communication channel for multi-agent collaboration."""

from typing import List, Optional
from datetime import datetime, timedelta

from .message import Message, MessageType
from .voice_net_protocol import VoiceNetProtocol


class SharedChannel:
    """Central communication hub for agents and users.

    Manages message history, broadcasting, and context retrieval
    for agent decision-making.
    """

    def __init__(self, max_history: int = 1000):
        """Initialize the shared channel.

        Args:
            max_history: Maximum number of messages to keep in history
        """
        self.messages: List[Message] = []
        self.max_history = max_history
        self._protocol = VoiceNetProtocol()

    def add_message(
        self,
        sender_id: str,
        content: str,
        sender_callsign: Optional[str] = None,
        message_type: MessageType = MessageType.AGENT,
        metadata: Optional[dict] = None
    ) -> Message:
        """Add a message to the channel.

        Args:
            sender_id: ID of the sender
            content: Message content
            sender_callsign: Radio callsign of sender
            message_type: Type of message
            metadata: Additional metadata

        Returns:
            The created Message object
        """
        # Parse voice net protocol to extract recipient
        parsed = self._protocol.parse(content)
        recipient_callsign = parsed.recipient

        message = Message(
            sender_id=sender_id,
            sender_callsign=sender_callsign,
            recipient_callsign=recipient_callsign,
            content=content,
            message_type=message_type,
            metadata=metadata or {}
        )

        self.messages.append(message)

        # Trim history if needed
        if len(self.messages) > self.max_history:
            self.messages = self.messages[-self.max_history:]

        return message

    def get_recent_messages(self, count: int = 10) -> List[Message]:
        """Get the most recent messages.

        Args:
            count: Number of messages to retrieve

        Returns:
            List of recent messages
        """
        return self.messages[-count:] if self.messages else []

    def get_messages_since(self, timestamp: datetime) -> List[Message]:
        """Get all messages since a specific timestamp.

        Args:
            timestamp: Cutoff timestamp

        Returns:
            List of messages after timestamp
        """
        return [msg for msg in self.messages if msg.timestamp > timestamp]

    def get_messages_for_agent(
        self,
        agent_callsign: str,
        count: int = 10,
        include_broadcasts: bool = True
    ) -> List[Message]:
        """Get recent messages relevant to a specific agent.

        Args:
            agent_callsign: Callsign of the agent
            count: Number of messages to retrieve
            include_broadcasts: Whether to include broadcast messages

        Returns:
            List of relevant messages
        """
        relevant_messages = []

        # Look through recent messages
        for msg in reversed(self.messages):
            # Include messages addressed to this agent
            if msg.is_addressed_to(agent_callsign):
                relevant_messages.append(msg)

            # Include messages from this agent
            elif msg.sender_callsign == agent_callsign:
                relevant_messages.append(msg)

            # Include broadcasts if requested
            elif include_broadcasts and msg.recipient_callsign in ["all", "all units", "everyone"]:
                relevant_messages.append(msg)

            # Include system messages
            elif msg.message_type == MessageType.SYSTEM:
                relevant_messages.append(msg)

            if len(relevant_messages) >= count:
                break

        return list(reversed(relevant_messages))

    def get_context_window(
        self,
        agent_callsign: str,
        window_size: int = 20,
        time_window: Optional[timedelta] = None
    ) -> List[Message]:
        """Get context window for an agent to make decisions.

        Args:
            agent_callsign: Callsign of the agent
            window_size: Maximum number of messages to include
            time_window: Optional time window to limit messages

        Returns:
            List of contextually relevant messages
        """
        messages = self.messages

        # Filter by time window if provided
        if time_window:
            cutoff = datetime.now() - time_window
            messages = [msg for msg in messages if msg.timestamp > cutoff]

        # Get the most recent messages up to window_size
        context = messages[-window_size:] if len(messages) > window_size else messages

        return context

    def clear(self):
        """Clear all messages from the channel."""
        self.messages.clear()

    def get_message_count(self) -> int:
        """Get total number of messages in the channel.

        Returns:
            Message count
        """
        return len(self.messages)

    def format_history(self, count: int = 10) -> str:
        """Format recent message history for display.

        Args:
            count: Number of recent messages to format

        Returns:
            Formatted message history string
        """
        recent = self.get_recent_messages(count)

        if not recent:
            return "No messages in channel."

        lines = []
        for msg in recent:
            lines.append(msg.format_for_display())

        return "\n".join(lines)
