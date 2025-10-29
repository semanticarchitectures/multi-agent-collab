"""Tests for speaking criteria."""

import pytest

from src.agents.speaking_criteria import (
    DirectAddressCriteria,
    KeywordCriteria,
    QuestionCriteria,
    SquadLeaderCriteria,
    CompositeCriteria
)
from src.channel.message import Message


def create_test_message(content, sender_id="user", recipient_callsign=None):
    """Helper to create test messages."""
    return Message(
        sender_id=sender_id,
        content=content,
        recipient_callsign=recipient_callsign
    )


def test_direct_address_criteria():
    """Test direct address criteria."""
    criteria = DirectAddressCriteria()

    # Message addressed to agent
    msg = create_test_message(
        "Alpha One, this is Alpha Lead, respond, over.",
        recipient_callsign="Alpha One"
    )

    assert criteria.should_respond("agent1", "Alpha One", [msg])

    # Message not addressed to agent
    msg2 = create_test_message(
        "Alpha Two, this is Alpha Lead, respond, over.",
        recipient_callsign="Alpha Two"
    )

    assert not criteria.should_respond("agent1", "Alpha One", [msg2])


def test_keyword_criteria():
    """Test keyword criteria."""
    criteria = KeywordCriteria(keywords=["analyze", "data"])

    # Message with keyword
    msg = create_test_message("We need to analyze this data.")

    assert criteria.should_respond("agent1", "Alpha One", [msg])

    # Message without keyword
    msg2 = create_test_message("Just checking in.")

    assert not criteria.should_respond("agent1", "Alpha One", [msg2])


def test_keyword_criteria_case_sensitive():
    """Test case-sensitive keyword matching."""
    criteria = KeywordCriteria(keywords=["URGENT"], case_sensitive=True)

    msg1 = create_test_message("This is URGENT!")
    msg2 = create_test_message("This is urgent!")

    assert criteria.should_respond("agent1", "Alpha One", [msg1])
    assert not criteria.should_respond("agent1", "Alpha One", [msg2])


def test_question_criteria():
    """Test question criteria."""
    criteria = QuestionCriteria()

    # Message with question
    msg = create_test_message("What is our status?")

    assert criteria.should_respond("agent1", "Alpha One", [msg])

    # Message without question
    msg2 = create_test_message("All systems normal.")

    assert not criteria.should_respond("agent1", "Alpha One", [msg2])


def test_squad_leader_criteria():
    """Test squad leader criteria."""
    criteria = SquadLeaderCriteria()

    # Message with coordination keyword
    msg = create_test_message("We need help coordinating this task.")

    assert criteria.should_respond("leader", "Alpha Lead", [msg])

    # Question without addressee
    msg2 = create_test_message("What should we do?")

    assert criteria.should_respond("leader", "Alpha Lead", [msg2])

    # Regular message
    msg3 = create_test_message("Everything is fine.")

    assert not criteria.should_respond("leader", "Alpha Lead", [msg3])


def test_composite_criteria():
    """Test composite criteria with multiple conditions."""
    criteria = CompositeCriteria([
        DirectAddressCriteria(),
        KeywordCriteria(keywords=["urgent"])
    ])

    # Direct address
    msg1 = create_test_message(
        "Alpha One, respond.",
        recipient_callsign="Alpha One"
    )

    assert criteria.should_respond("agent1", "Alpha One", [msg1])

    # Keyword match
    msg2 = create_test_message("This is urgent!")

    assert criteria.should_respond("agent1", "Alpha One", [msg2])

    # Neither condition
    msg3 = create_test_message("Regular message.")

    assert not criteria.should_respond("agent1", "Alpha One", [msg3])


def test_dont_respond_to_own_messages():
    """Test that agents don't respond to their own messages."""
    criteria = DirectAddressCriteria()

    msg = create_test_message(
        "Alpha Two, respond.",
        sender_id="agent1",
        recipient_callsign="Alpha Two"
    )

    # Agent1 should not respond to its own message
    assert not criteria.should_respond("agent1", "Alpha One", [msg])
