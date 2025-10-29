"""Speaking criteria for determining when agents should respond."""

from abc import ABC, abstractmethod
from typing import List
from enum import Enum

from ..channel.message import Message


class CriteriaType(str, Enum):
    """Types of speaking criteria."""

    DIRECT_ADDRESS = "direct_address"  # Agent is directly addressed
    KEYWORDS = "keywords"  # Message contains specific keywords
    ALWAYS = "always"  # Always respond
    SQUAD_LEADER = "squad_leader"  # Squad leader specific criteria
    QUESTION = "question"  # Message contains a question
    CUSTOM = "custom"  # Custom criteria logic


class SpeakingCriteria(ABC):
    """Base class for speaking criteria."""

    @abstractmethod
    def should_respond(
        self,
        agent_id: str,
        agent_callsign: str,
        recent_messages: List[Message]
    ) -> bool:
        """Determine if the agent should respond based on recent messages.

        Args:
            agent_id: The agent's ID
            agent_callsign: The agent's callsign
            recent_messages: Recent messages from the channel

        Returns:
            True if the agent should respond
        """
        pass


class DirectAddressCriteria(SpeakingCriteria):
    """Respond when directly addressed by callsign."""

    def should_respond(
        self,
        agent_id: str,
        agent_callsign: str,
        recent_messages: List[Message]
    ) -> bool:
        """Check if agent is directly addressed in recent messages.

        Args:
            agent_id: The agent's ID
            agent_callsign: The agent's callsign
            recent_messages: Recent messages from the channel

        Returns:
            True if directly addressed
        """
        if not recent_messages:
            return False

        # Check the most recent message
        latest = recent_messages[-1]

        # Don't respond to own messages
        if latest.sender_id == agent_id:
            return False

        # Check if addressed to this agent
        return latest.is_addressed_to(agent_callsign)


class KeywordCriteria(SpeakingCriteria):
    """Respond when specific keywords are mentioned."""

    def __init__(self, keywords: List[str], case_sensitive: bool = False):
        """Initialize keyword criteria.

        Args:
            keywords: List of keywords to trigger on
            case_sensitive: Whether keyword matching is case-sensitive
        """
        self.keywords = keywords
        self.case_sensitive = case_sensitive

    def should_respond(
        self,
        agent_id: str,
        agent_callsign: str,
        recent_messages: List[Message]
    ) -> bool:
        """Check if keywords appear in recent messages.

        Args:
            agent_id: The agent's ID
            agent_callsign: The agent's callsign
            recent_messages: Recent messages from the channel

        Returns:
            True if keywords found
        """
        if not recent_messages:
            return False

        # Check the most recent message
        latest = recent_messages[-1]

        # Don't respond to own messages
        if latest.sender_id == agent_id:
            return False

        content = latest.content
        if not self.case_sensitive:
            content = content.lower()

        for keyword in self.keywords:
            check_keyword = keyword if self.case_sensitive else keyword.lower()
            if check_keyword in content:
                return True

        return False


class QuestionCriteria(SpeakingCriteria):
    """Respond when a question is asked."""

    def should_respond(
        self,
        agent_id: str,
        agent_callsign: str,
        recent_messages: List[Message]
    ) -> bool:
        """Check if recent message contains a question.

        Args:
            agent_id: The agent's ID
            agent_callsign: The agent's callsign
            recent_messages: Recent messages from the channel

        Returns:
            True if question detected
        """
        if not recent_messages:
            return False

        latest = recent_messages[-1]

        # Don't respond to own messages
        if latest.sender_id == agent_id:
            return False

        # Simple question detection
        return "?" in latest.content


class SquadLeaderCriteria(SpeakingCriteria):
    """Squad leader responds to coordination needs and unaddressed messages."""

    def __init__(self, coordination_keywords: List[str] = None):
        """Initialize squad leader criteria.

        Args:
            coordination_keywords: Keywords that trigger leader coordination
        """
        self.coordination_keywords = coordination_keywords or [
            "help", "stuck", "unclear", "coordinate", "organize", "plan"
        ]

    def should_respond(
        self,
        agent_id: str,
        agent_callsign: str,
        recent_messages: List[Message]
    ) -> bool:
        """Determine if squad leader should respond.

        Args:
            agent_id: The agent's ID
            agent_callsign: The agent's callsign
            recent_messages: Recent messages from the channel

        Returns:
            True if leader should respond
        """
        if not recent_messages:
            return False

        latest = recent_messages[-1]

        # Don't respond to own messages
        if latest.sender_id == agent_id:
            return False

        # Respond if directly addressed
        if latest.is_addressed_to(agent_callsign):
            return True

        # Respond to coordination keywords
        content_lower = latest.content.lower()
        for keyword in self.coordination_keywords:
            if keyword in content_lower:
                return True

        # Respond to questions without specific addressee
        if "?" in latest.content and not latest.recipient_callsign:
            return True

        return False


class CompositeCriteria(SpeakingCriteria):
    """Combine multiple criteria with OR logic."""

    def __init__(self, criteria_list: List[SpeakingCriteria]):
        """Initialize composite criteria.

        Args:
            criteria_list: List of criteria to evaluate
        """
        self.criteria_list = criteria_list

    def should_respond(
        self,
        agent_id: str,
        agent_callsign: str,
        recent_messages: List[Message]
    ) -> bool:
        """Check if any criteria are met.

        Args:
            agent_id: The agent's ID
            agent_callsign: The agent's callsign
            recent_messages: Recent messages from the channel

        Returns:
            True if any criteria met
        """
        for criteria in self.criteria_list:
            if criteria.should_respond(agent_id, agent_callsign, recent_messages):
                return True
        return False
