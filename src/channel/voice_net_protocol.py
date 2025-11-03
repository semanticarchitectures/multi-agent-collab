"""Voice net protocol parser and formatter for agent communication.

Implements pilot-ATC style communication protocol:
- "[Recipient], this is [Sender], [message], over."
- "Roger, [acknowledgment]"
- "Copy, [confirmation]"
- "Say again, [request for repeat]"
"""

import re
from typing import Optional, Tuple
from enum import Enum
from pydantic import BaseModel


class MessageType(Enum):
    """Type of voice net message."""
    REQUEST = "request"  # Asking for information or action
    REPORT = "report"  # Reporting information
    COMMAND = "command"  # Giving an order/assignment
    ACKNOWLEDGMENT = "acknowledgment"  # Roger/Copy response
    QUERY = "query"  # Question
    UNKNOWN = "unknown"


class VoiceNetMessage(BaseModel):
    """Parsed voice net protocol message."""

    sender: Optional[str] = None
    recipient: Optional[str] = None
    content: str
    is_over: bool = False  # Message ends with "over"
    is_roger: bool = False  # Acknowledgment
    is_copy: bool = False  # Confirmation
    is_broadcast: bool = False  # Broadcast to all stations
    message_type: MessageType = MessageType.UNKNOWN


class VoiceNetProtocol:
    """Parser and formatter for voice net protocol messages."""

    # Pattern: "[Recipient], this is [Sender], [content], over."
    FULL_PATTERN = re.compile(
        r"^(?P<recipient>[\w\s-]+),\s+this\s+is\s+(?P<sender>[\w\s-]+),\s+(?P<content>.+?)(?:,\s*over)?\.?$",
        re.IGNORECASE
    )

    # Pattern: "All stations/All units, this is [Sender], [content]"
    BROADCAST_PATTERN = re.compile(
        r"^(?:all\s+(?:stations|units|agents)),\s+this\s+is\s+(?P<sender>[\w\s-]+),\s+(?P<content>.+?)(?:,\s*over)?\.?$",
        re.IGNORECASE
    )

    # Pattern: "Roger, [content]" or "Copy, [content]"
    ACKNOWLEDGMENT_PATTERN = re.compile(
        r"^(?P<ack>roger|copy),\s+(?P<content>.+)\.?$",
        re.IGNORECASE
    )

    # Pattern: "[Recipient], [content]" (shortened form)
    DIRECT_PATTERN = re.compile(
        r"^(?P<recipient>[\w\s-]+),\s+(?P<content>.+?)(?:,\s*over)?\.?$",
        re.IGNORECASE
    )

    # Broadcast keywords
    BROADCAST_KEYWORDS = ["all stations", "all units", "all agents", "everyone"]

    # Command keywords
    COMMAND_KEYWORDS = ["calculate", "search", "find", "plan", "execute", "perform", "check"]

    # Request keywords
    REQUEST_KEYWORDS = ["please", "need", "require", "request", "can you", "could you"]

    # Query keywords
    QUERY_KEYWORDS = ["what", "when", "where", "how", "why", "which", "who"]

    @classmethod
    def parse(cls, message: str) -> VoiceNetMessage:
        """Parse a voice net protocol message with enhanced detection.

        Args:
            message: Raw message string

        Returns:
            Parsed VoiceNetMessage with type and broadcast detection
        """
        message = message.strip()
        message_lower = message.lower()

        # Try broadcast pattern first
        match = cls.BROADCAST_PATTERN.match(message)
        if match:
            content = match.group("content").strip()
            return VoiceNetMessage(
                sender=match.group("sender").strip(),
                recipient="ALL",
                content=content,
                is_over="over" in message_lower,
                is_broadcast=True,
                message_type=cls._detect_message_type(content)
            )

        # Try full pattern
        match = cls.FULL_PATTERN.match(message)
        if match:
            recipient = match.group("recipient").strip()
            content = match.group("content").strip()
            is_broadcast = recipient.lower() in cls.BROADCAST_KEYWORDS or recipient.lower() == "all"

            return VoiceNetMessage(
                recipient=recipient,
                sender=match.group("sender").strip(),
                content=content,
                is_over="over" in message_lower,
                is_broadcast=is_broadcast,
                message_type=cls._detect_message_type(content)
            )

        # Try acknowledgment pattern
        match = cls.ACKNOWLEDGMENT_PATTERN.match(message)
        if match:
            ack = match.group("ack").lower()
            return VoiceNetMessage(
                content=match.group("content").strip(),
                is_roger=(ack == "roger"),
                is_copy=(ack == "copy"),
                message_type=MessageType.ACKNOWLEDGMENT
            )

        # Try direct pattern
        match = cls.DIRECT_PATTERN.match(message)
        if match:
            recipient = match.group("recipient").strip()
            content = match.group("content").strip()
            is_broadcast = recipient.lower() in cls.BROADCAST_KEYWORDS or recipient.lower() == "all"

            return VoiceNetMessage(
                recipient=recipient,
                content=content,
                is_over="over" in message_lower,
                is_broadcast=is_broadcast,
                message_type=cls._detect_message_type(content)
            )

        # Return unparsed message
        return VoiceNetMessage(
            content=message,
            message_type=cls._detect_message_type(message)
        )

    @classmethod
    def _detect_message_type(cls, content: str) -> MessageType:
        """Detect the type of message from content.

        Args:
            content: Message content

        Returns:
            Detected MessageType
        """
        content_lower = content.lower()

        # Check for query (questions typically start with question words)
        if any(content_lower.startswith(keyword) for keyword in cls.QUERY_KEYWORDS):
            return MessageType.QUERY

        # Check for command keywords
        if any(keyword in content_lower for keyword in cls.COMMAND_KEYWORDS):
            return MessageType.COMMAND

        # Check for request keywords
        if any(keyword in content_lower for keyword in cls.REQUEST_KEYWORDS):
            return MessageType.REQUEST

        # Check for reporting indicators
        if any(word in content_lower for word in ["report", "reporting", "status", "completed", "found"]):
            return MessageType.REPORT

        # Default to unknown
        return MessageType.UNKNOWN

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
