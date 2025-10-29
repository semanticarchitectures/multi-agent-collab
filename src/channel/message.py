"""Message data model for agent communication."""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Types of messages in the system."""

    AGENT = "agent"
    USER = "user"
    SYSTEM = "system"


class Message(BaseModel):
    """Represents a single message in the shared channel.

    Attributes:
        id: Unique message identifier
        timestamp: When the message was created
        sender_id: ID of the agent or user who sent the message
        sender_callsign: Radio callsign of the sender (e.g., "Alpha Lead")
        recipient_callsign: Radio callsign of the intended recipient (e.g., "Alpha One")
        content: The actual message content
        message_type: Type of message (agent, user, or system)
        metadata: Additional message metadata
    """

    id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    timestamp: datetime = Field(default_factory=datetime.now)
    sender_id: str
    sender_callsign: Optional[str] = None
    recipient_callsign: Optional[str] = None
    content: str
    message_type: MessageType = MessageType.AGENT
    metadata: dict = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    def is_addressed_to(self, callsign: str) -> bool:
        """Check if this message is addressed to a specific callsign.

        Args:
            callsign: The callsign to check

        Returns:
            True if the message is addressed to the callsign or is a broadcast
        """
        if not self.recipient_callsign:
            return False

        # Handle broadcasts ("All units" or similar)
        if self.recipient_callsign.lower() in ["all", "all units", "everyone"]:
            return True

        return self.recipient_callsign.lower() == callsign.lower()

    def format_for_display(self) -> str:
        """Format the message for display in the channel.

        Returns:
            Formatted message string
        """
        timestamp_str = self.timestamp.strftime("%H:%M:%S")

        if self.message_type == MessageType.SYSTEM:
            return f"[{timestamp_str}] [SYSTEM] {self.content}"

        callsign = self.sender_callsign or self.sender_id
        return f"[{timestamp_str}] {callsign}: {self.content}"
