"""Voice net protocol parser and formatter for agent communication.

Implements pilot-ATC style communication protocol:
- "[Recipient], this is [Sender], [message], over."
- "Roger, [acknowledgment]"
- "Copy, [confirmation]"
- "Say again, [request for repeat]"
"""

import re
from typing import Optional, Tuple
from pydantic import BaseModel


class VoiceNetMessage(BaseModel):
    """Parsed voice net protocol message."""

    sender: Optional[str] = None
    recipient: Optional[str] = None
    content: str
    is_over: bool = False  # Message ends with "over"
    is_roger: bool = False  # Acknowledgment
    is_copy: bool = False  # Confirmation


class VoiceNetProtocol:
    """Parser and formatter for voice net protocol messages."""

    # Pattern: "[Recipient], this is [Sender], [content], over."
    FULL_PATTERN = re.compile(
        r"^(?P<recipient>[\w\s]+),\s+this\s+is\s+(?P<sender>[\w\s]+),\s+(?P<content>.+?)(?:,\s*over)?\.?$",
        re.IGNORECASE
    )

    # Pattern: "Roger, [content]" or "Copy, [content]"
    ACKNOWLEDGMENT_PATTERN = re.compile(
        r"^(?P<ack>roger|copy),\s+(?P<content>.+)\.?$",
        re.IGNORECASE
    )

    # Pattern: "[Recipient], [content]" (shortened form)
    DIRECT_PATTERN = re.compile(
        r"^(?P<recipient>[\w\s]+),\s+(?P<content>.+?)(?:,\s*over)?\.?$",
        re.IGNORECASE
    )

    @classmethod
    def parse(cls, message: str) -> VoiceNetMessage:
        """Parse a voice net protocol message.

        Args:
            message: Raw message string

        Returns:
            Parsed VoiceNetMessage
        """
        message = message.strip()

        # Try full pattern first
        match = cls.FULL_PATTERN.match(message)
        if match:
            return VoiceNetMessage(
                recipient=match.group("recipient").strip(),
                sender=match.group("sender").strip(),
                content=match.group("content").strip(),
                is_over="over" in message.lower()
            )

        # Try acknowledgment pattern
        match = cls.ACKNOWLEDGMENT_PATTERN.match(message)
        if match:
            ack = match.group("ack").lower()
            return VoiceNetMessage(
                content=match.group("content").strip(),
                is_roger=(ack == "roger"),
                is_copy=(ack == "copy")
            )

        # Try direct pattern
        match = cls.DIRECT_PATTERN.match(message)
        if match:
            return VoiceNetMessage(
                recipient=match.group("recipient").strip(),
                content=match.group("content").strip(),
                is_over="over" in message.lower()
            )

        # Return unparsed message
        return VoiceNetMessage(content=message)

    @classmethod
    def format(
        cls,
        content: str,
        sender: str,
        recipient: Optional[str] = None,
        add_over: bool = True
    ) -> str:
        """Format a message using voice net protocol.

        Args:
            content: Message content
            sender: Sender callsign
            recipient: Recipient callsign (optional)
            add_over: Whether to add "over" at the end

        Returns:
            Formatted voice net protocol message
        """
        if recipient:
            msg = f"{recipient}, this is {sender}, {content}"
        else:
            msg = f"{sender}, {content}"

        if add_over and not msg.endswith("over"):
            msg += ", over"

        if not msg.endswith("."):
            msg += "."

        return msg

    @classmethod
    def format_roger(cls, content: str = "") -> str:
        """Format a Roger (acknowledgment) message.

        Args:
            content: Optional acknowledgment content

        Returns:
            Formatted Roger message
        """
        msg = "Roger"
        if content:
            msg += f", {content}"
        if not msg.endswith("."):
            msg += "."
        return msg

    @classmethod
    def format_copy(cls, content: str = "") -> str:
        """Format a Copy (confirmation) message.

        Args:
            content: Optional confirmation content

        Returns:
            Formatted Copy message
        """
        msg = "Copy"
        if content:
            msg += f", {content}"
        if not msg.endswith("."):
            msg += "."
        return msg

    @classmethod
    def extract_callsigns(cls, message: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract sender and recipient callsigns from a message.

        Args:
            message: Raw message string

        Returns:
            Tuple of (sender, recipient) callsigns
        """
        parsed = cls.parse(message)
        return parsed.sender, parsed.recipient
