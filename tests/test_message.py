"""Tests for message data model."""

import pytest
from datetime import datetime

from src.channel.message import Message, MessageType


def test_message_creation():
    """Test basic message creation."""
    msg = Message(
        sender_id="agent1",
        sender_callsign="Alpha One",
        content="Test message",
        message_type=MessageType.AGENT
    )

    assert msg.sender_id == "agent1"
    assert msg.sender_callsign == "Alpha One"
    assert msg.content == "Test message"
    assert msg.message_type == MessageType.AGENT
    assert isinstance(msg.timestamp, datetime)


def test_message_is_addressed_to():
    """Test message addressing logic."""
    msg = Message(
        sender_id="agent1",
        sender_callsign="Alpha One",
        recipient_callsign="Alpha Two",
        content="Test message"
    )

    assert msg.is_addressed_to("Alpha Two")
    assert msg.is_addressed_to("alpha two")  # Case insensitive
    assert not msg.is_addressed_to("Alpha Three")


def test_message_broadcast():
    """Test broadcast message detection."""
    msg = Message(
        sender_id="agent1",
        sender_callsign="Alpha One",
        recipient_callsign="All units",
        content="Broadcast message"
    )

    assert msg.is_addressed_to("Alpha Two")
    assert msg.is_addressed_to("Alpha Three")
    assert msg.is_addressed_to("anyone")


def test_message_format_for_display():
    """Test message formatting."""
    msg = Message(
        sender_id="agent1",
        sender_callsign="Alpha One",
        content="Test message",
        message_type=MessageType.AGENT
    )

    formatted = msg.format_for_display()
    assert "Alpha One" in formatted
    assert "Test message" in formatted


def test_system_message_format():
    """Test system message formatting."""
    msg = Message(
        sender_id="system",
        content="System notification",
        message_type=MessageType.SYSTEM
    )

    formatted = msg.format_for_display()
    assert "[SYSTEM]" in formatted
    assert "System notification" in formatted
