"""Tests for shared channel."""

import pytest
from datetime import datetime, timedelta

from src.channel.shared_channel import SharedChannel
from src.channel.message import MessageType


def test_channel_creation():
    """Test channel creation."""
    channel = SharedChannel()

    assert channel.get_message_count() == 0
    assert len(channel.messages) == 0


def test_add_message():
    """Test adding messages to channel."""
    channel = SharedChannel()

    msg = channel.add_message(
        sender_id="agent1",
        content="Test message",
        sender_callsign="Alpha One"
    )

    assert msg.sender_id == "agent1"
    assert msg.content == "Test message"
    assert channel.get_message_count() == 1


def test_get_recent_messages():
    """Test retrieving recent messages."""
    channel = SharedChannel()

    # Add multiple messages
    for i in range(5):
        channel.add_message(
            sender_id=f"agent{i}",
            content=f"Message {i}",
            sender_callsign=f"Alpha {i}"
        )

    recent = channel.get_recent_messages(3)

    assert len(recent) == 3
    assert recent[-1].content == "Message 4"


def test_get_messages_for_agent():
    """Test retrieving messages for specific agent."""
    channel = SharedChannel()

    # Add messages
    channel.add_message(
        sender_id="agent1",
        content="Alpha Two, this is Alpha One, respond, over.",
        sender_callsign="Alpha One"
    )

    channel.add_message(
        sender_id="agent2",
        content="Alpha One, this is Alpha Two, roger, over.",
        sender_callsign="Alpha Two"
    )

    channel.add_message(
        sender_id="agent3",
        content="Unrelated message",
        sender_callsign="Alpha Three"
    )

    # Get messages for Alpha Two
    messages = channel.get_messages_for_agent("Alpha Two", count=10)

    # Should include messages to/from Alpha Two
    assert len(messages) >= 2


def test_channel_clear():
    """Test clearing channel."""
    channel = SharedChannel()

    channel.add_message(
        sender_id="agent1",
        content="Test message"
    )

    assert channel.get_message_count() == 1

    channel.clear()

    assert channel.get_message_count() == 0


def test_max_history():
    """Test max history enforcement."""
    channel = SharedChannel(max_history=5)

    # Add more messages than max
    for i in range(10):
        channel.add_message(
            sender_id=f"agent{i}",
            content=f"Message {i}"
        )

    assert channel.get_message_count() == 5


def test_format_history():
    """Test formatting channel history."""
    channel = SharedChannel()

    channel.add_message(
        sender_id="agent1",
        content="Test message",
        sender_callsign="Alpha One"
    )

    history = channel.format_history(10)

    assert "Alpha One" in history
    assert "Test message" in history
