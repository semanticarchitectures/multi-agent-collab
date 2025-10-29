"""Tests for voice net protocol parser."""

import pytest

from src.channel.voice_net_protocol import VoiceNetProtocol, VoiceNetMessage


def test_parse_full_protocol():
    """Test parsing full voice net protocol message."""
    msg = "Alpha Two, this is Alpha One, found relevant data, over."

    parsed = VoiceNetProtocol.parse(msg)

    assert parsed.sender == "Alpha One"
    assert parsed.recipient == "Alpha Two"
    assert parsed.content == "found relevant data"
    assert parsed.is_over is True


def test_parse_without_over():
    """Test parsing message without 'over'."""
    msg = "Alpha Two, this is Alpha One, found relevant data."

    parsed = VoiceNetProtocol.parse(msg)

    assert parsed.sender == "Alpha One"
    assert parsed.recipient == "Alpha Two"
    assert parsed.content == "found relevant data"
    assert parsed.is_over is False


def test_parse_roger():
    """Test parsing Roger acknowledgment."""
    msg = "Roger, will comply."

    parsed = VoiceNetProtocol.parse(msg)

    assert parsed.is_roger is True
    assert parsed.content == "will comply"


def test_parse_copy():
    """Test parsing Copy confirmation."""
    msg = "Copy, understood."

    parsed = VoiceNetProtocol.parse(msg)

    assert parsed.is_copy is True
    assert parsed.content == "understood"


def test_parse_direct():
    """Test parsing direct address format."""
    msg = "Alpha Two, check your status."

    parsed = VoiceNetProtocol.parse(msg)

    assert parsed.recipient == "Alpha Two"
    assert parsed.content == "check your status"


def test_format_with_recipient():
    """Test formatting with recipient."""
    msg = VoiceNetProtocol.format(
        content="found relevant data",
        sender="Alpha One",
        recipient="Alpha Two",
        add_over=True
    )

    assert "Alpha Two" in msg
    assert "Alpha One" in msg
    assert "found relevant data" in msg
    assert "over" in msg.lower()


def test_format_without_recipient():
    """Test formatting without recipient."""
    msg = VoiceNetProtocol.format(
        content="standing by",
        sender="Alpha One",
        recipient=None,
        add_over=False
    )

    assert "Alpha One" in msg
    assert "standing by" in msg
    assert "over" not in msg.lower()


def test_format_roger():
    """Test formatting Roger message."""
    msg = VoiceNetProtocol.format_roger("understood")

    assert "Roger" in msg
    assert "understood" in msg


def test_format_copy():
    """Test formatting Copy message."""
    msg = VoiceNetProtocol.format_copy("will comply")

    assert "Copy" in msg
    assert "will comply" in msg


def test_extract_callsigns():
    """Test extracting callsigns from message."""
    msg = "Alpha Two, this is Alpha One, reporting status, over."

    sender, recipient = VoiceNetProtocol.extract_callsigns(msg)

    assert sender == "Alpha One"
    assert recipient == "Alpha Two"
