"""
Unit tests for StateManager class.

Tests state management functionality including:
- Database initialization
- Session save/load
- Session listing and deletion
- Channel restoration
- Agent memory restoration
- Session export
"""

import pytest
import asyncio
import os
import json
import tempfile
from pathlib import Path
from datetime import datetime

from src.state.state_manager import StateManager
from src.channel.shared_channel import SharedChannel
from src.channel.message import Message, MessageType
from src.agents.base_agent import BaseAgent


# Mock agent for testing
class MockAgent:
    """Mock agent for testing."""

    def __init__(self, agent_id: str, callsign: str):
        self.agent_id = agent_id
        self.callsign = callsign
        self.system_prompt = f"You are {callsign}"
        self.model = "claude-sonnet-4-5-20250929"
        self.memory = {
            "task_list": [],
            "key_facts": {},
            "decisions_made": [],
            "concerns": [],
            "notes": []
        }

    def get_agent_type(self):
        return "base"


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_sessions.db")

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    os.rmdir(temp_dir)


@pytest.fixture
async def state_manager(temp_db):
    """Create a StateManager with temp database."""
    sm = StateManager(db_path=temp_db)
    await sm.initialize_db()
    return sm


@pytest.fixture
def sample_channel():
    """Create a sample channel with messages."""
    channel = SharedChannel()
    channel.add_message(
        sender_id="user",
        content="Hello agents",
        sender_callsign="USER",
        message_type=MessageType.USER
    )
    channel.add_message(
        sender_id="agent-1",
        content="Roger, received.",
        sender_callsign="ALPHA-ONE",
        message_type=MessageType.AGENT
    )
    return channel


@pytest.fixture
def sample_agents():
    """Create sample agents."""
    agent1 = MockAgent("agent-1", "ALPHA-ONE")
    agent1.memory["task_list"] = ["Task 1", "Task 2"]
    agent1.memory["key_facts"] = {"location": "Boston"}

    agent2 = MockAgent("agent-2", "ALPHA-TWO")
    agent2.memory["notes"] = ["Note 1"]

    return [agent1, agent2]


class TestStateManagerInitialization:
    """Test StateManager initialization."""

    def test_state_manager_initialization(self, temp_db):
        """Test StateManager initialization."""
        sm = StateManager(db_path=temp_db)

        assert sm.db_path == temp_db
        assert Path(temp_db).parent.exists()

    def test_ensure_db_directory_creates_nested_dirs(self):
        """Test that directory creation works for nested paths."""
        temp_dir = tempfile.mkdtemp()
        nested_path = os.path.join(temp_dir, "subdir", "test.db")

        sm = StateManager(db_path=nested_path)

        assert Path(nested_path).parent.exists()

        # Cleanup
        os.rmdir(os.path.join(temp_dir, "subdir"))
        os.rmdir(temp_dir)

    @pytest.mark.asyncio
    async def test_initialize_db_creates_tables(self, temp_db):
        """Test database initialization creates tables."""
        sm = StateManager(db_path=temp_db)
        await sm.initialize_db()

        # Verify database file exists
        assert os.path.exists(temp_db)

        # Verify tables exist (would fail if not)
        import aiosqlite
        async with aiosqlite.connect(temp_db) as db:
            cursor = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'"
            )
            result = await cursor.fetchone()
            assert result is not None


class TestSessionSaveLoad:
    """Test session save and load operations."""

    @pytest.mark.asyncio
    async def test_save_session(self, state_manager, sample_channel, sample_agents):
        """Test saving a session."""
        result = await state_manager.save_session(
            session_id="test-session-1",
            channel=sample_channel,
            agents=sample_agents,
            metadata={"description": "Test session"}
        )

        assert result is True

    @pytest.mark.asyncio
    async def test_save_and_load_session(self, state_manager, sample_channel, sample_agents):
        """Test saving and loading a session."""
        # Save session
        await state_manager.save_session(
            session_id="test-session-2",
            channel=sample_channel,
            agents=sample_agents,
            metadata={"description": "Test session"}
        )

        # Load session
        loaded = await state_manager.load_session("test-session-2")

        assert loaded is not None
        assert loaded["session_id"] == "test-session-2"
        assert len(loaded["messages"]) == 2
        assert len(loaded["agent_states"]) == 2
        assert loaded["metadata"]["description"] == "Test session"

    @pytest.mark.asyncio
    async def test_load_nonexistent_session(self, state_manager):
        """Test loading a session that doesn't exist."""
        loaded = await state_manager.load_session("nonexistent")

        assert loaded is None

    @pytest.mark.asyncio
    async def test_save_session_upsert(self, state_manager, sample_channel, sample_agents):
        """Test that saving updates existing session."""
        # Save initial
        await state_manager.save_session(
            session_id="test-session-3",
            channel=sample_channel,
            agents=sample_agents,
            metadata={"version": 1}
        )

        # Update channel
        sample_channel.add_message(
            sender_id="user",
            content="Another message",
            message_type=MessageType.USER
        )

        # Save again (should update)
        await state_manager.save_session(
            session_id="test-session-3",
            channel=sample_channel,
            agents=sample_agents,
            metadata={"version": 2}
        )

        # Load
        loaded = await state_manager.load_session("test-session-3")

        assert len(loaded["messages"]) == 3
        assert loaded["metadata"]["version"] == 2

    @pytest.mark.asyncio
    async def test_save_session_preserves_agent_memory(self, state_manager, sample_channel, sample_agents):
        """Test that agent memory is preserved in save."""
        await state_manager.save_session(
            session_id="test-memory",
            channel=sample_channel,
            agents=sample_agents
        )

        loaded = await state_manager.load_session("test-memory")

        # Check agent 1 memory
        agent1_state = loaded["agent_states"][0]
        assert agent1_state["memory"]["task_list"] == ["Task 1", "Task 2"]
        assert agent1_state["memory"]["key_facts"] == {"location": "Boston"}

        # Check agent 2 memory
        agent2_state = loaded["agent_states"][1]
        assert agent2_state["memory"]["notes"] == ["Note 1"]


class TestSessionListing:
    """Test session listing operations."""

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, state_manager):
        """Test listing when no sessions exist."""
        sessions = await state_manager.list_sessions()

        assert sessions == []

    @pytest.mark.asyncio
    async def test_list_sessions(self, state_manager, sample_channel, sample_agents):
        """Test listing sessions."""
        # Create multiple sessions
        for i in range(3):
            await state_manager.save_session(
                session_id=f"session-{i}",
                channel=sample_channel,
                agents=sample_agents,
                metadata={"index": i}
            )

        # List sessions
        sessions = await state_manager.list_sessions()

        assert len(sessions) == 3
        assert all("session_id" in s for s in sessions)
        assert all("created_at" in s for s in sessions)
        assert all("message_count" in s for s in sessions)
        assert all("agent_count" in s for s in sessions)

    @pytest.mark.asyncio
    async def test_list_sessions_with_limit(self, state_manager, sample_channel, sample_agents):
        """Test listing sessions with limit."""
        # Create 5 sessions
        for i in range(5):
            await state_manager.save_session(
                session_id=f"session-{i}",
                channel=sample_channel,
                agents=sample_agents
            )

        # List with limit
        sessions = await state_manager.list_sessions(limit=3)

        assert len(sessions) == 3

    @pytest.mark.asyncio
    async def test_list_sessions_with_offset(self, state_manager, sample_channel, sample_agents):
        """Test listing sessions with offset."""
        # Create 5 sessions
        for i in range(5):
            await state_manager.save_session(
                session_id=f"session-{i}",
                channel=sample_channel,
                agents=sample_agents
            )

        # List with offset
        sessions = await state_manager.list_sessions(limit=10, offset=2)

        assert len(sessions) == 3

    @pytest.mark.asyncio
    async def test_list_sessions_order(self, state_manager, sample_channel, sample_agents):
        """Test that sessions are ordered by updated_at DESC."""
        # Create sessions with delay
        for i in range(3):
            await state_manager.save_session(
                session_id=f"session-{i}",
                channel=sample_channel,
                agents=sample_agents
            )
            await asyncio.sleep(0.01)  # Small delay to ensure different timestamps

        sessions = await state_manager.list_sessions()

        # First should be most recent (session-2)
        assert "session-2" in sessions[0]["session_id"]


class TestSessionDeletion:
    """Test session deletion."""

    @pytest.mark.asyncio
    async def test_delete_session(self, state_manager, sample_channel, sample_agents):
        """Test deleting a session."""
        # Create session
        await state_manager.save_session(
            session_id="to-delete",
            channel=sample_channel,
            agents=sample_agents
        )

        # Verify it exists
        loaded = await state_manager.load_session("to-delete")
        assert loaded is not None

        # Delete
        result = await state_manager.delete_session("to-delete")
        assert result is True

        # Verify it's gone
        loaded = await state_manager.load_session("to-delete")
        assert loaded is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_session(self, state_manager):
        """Test deleting a session that doesn't exist."""
        result = await state_manager.delete_session("nonexistent")

        # Should still return True (no error)
        assert result is True


class TestChannelRestoration:
    """Test channel restoration from session data."""

    @pytest.mark.asyncio
    async def test_restore_channel(self, state_manager, sample_channel, sample_agents):
        """Test restoring a channel from session data."""
        # Save session
        await state_manager.save_session(
            session_id="test-restore",
            channel=sample_channel,
            agents=sample_agents
        )

        # Load session data
        session_data = await state_manager.load_session("test-restore")

        # Restore channel
        restored_channel = await state_manager.restore_channel(session_data)

        assert len(restored_channel.messages) == 2
        assert restored_channel.messages[0].content == "Hello agents"
        assert restored_channel.messages[1].content == "Roger, received."

    @pytest.mark.asyncio
    async def test_restore_channel_empty(self, state_manager):
        """Test restoring channel from empty session."""
        channel = await state_manager.restore_channel({"messages": []})

        assert len(channel.messages) == 0

    @pytest.mark.asyncio
    async def test_restore_channel_preserves_metadata(self, state_manager):
        """Test that message metadata is preserved."""
        channel = SharedChannel()
        channel.add_message(
            sender_id="test",
            content="Test",
            message_type=MessageType.USER,
            metadata={"custom_field": "value"}
        )

        agent = MockAgent("agent-1", "ALPHA-ONE")

        # Save and load
        await state_manager.save_session(
            session_id="test-metadata",
            channel=channel,
            agents=[agent]
        )

        session_data = await state_manager.load_session("test-metadata")
        restored_channel = await state_manager.restore_channel(session_data)

        assert restored_channel.messages[0].metadata["custom_field"] == "value"


class TestAgentMemoryRestoration:
    """Test agent memory restoration."""

    def test_restore_agent_memory(self, state_manager):
        """Test restoring agent memory from state."""
        agent = MockAgent("agent-1", "ALPHA-ONE")

        agent_state = {
            "memory": {
                "task_list": ["Task A", "Task B"],
                "key_facts": {"test": "value"},
                "decisions_made": ["Decision 1"],
                "concerns": [],
                "notes": ["Note"]
            }
        }

        state_manager.restore_agent_memory(agent, agent_state)

        assert agent.memory["task_list"] == ["Task A", "Task B"]
        assert agent.memory["key_facts"] == {"test": "value"}
        assert agent.memory["decisions_made"] == ["Decision 1"]
        assert agent.memory["notes"] == ["Note"]

    def test_restore_agent_memory_no_memory_field(self, state_manager):
        """Test restoring when state has no memory field."""
        agent = MockAgent("agent-1", "ALPHA-ONE")
        original_memory = agent.memory.copy()

        agent_state = {"other_field": "value"}

        state_manager.restore_agent_memory(agent, agent_state)

        # Memory should be unchanged
        assert agent.memory == original_memory


class TestMessageConversion:
    """Test message to/from dict conversion."""

    def test_message_to_dict(self, state_manager):
        """Test converting Message to dict."""
        msg = Message(
            sender_id="test-id",
            sender_callsign="TEST",
            recipient_callsign="ALPHA",
            content="Test message",
            message_type=MessageType.USER,
            metadata={"key": "value"}
        )

        msg_dict = state_manager._message_to_dict(msg)

        assert msg_dict["sender_id"] == "test-id"
        assert msg_dict["sender_callsign"] == "TEST"
        assert msg_dict["recipient_callsign"] == "ALPHA"
        assert msg_dict["content"] == "Test message"
        assert msg_dict["message_type"] == "user"
        assert msg_dict["metadata"] == {"key": "value"}
        assert "timestamp" in msg_dict

    def test_dict_to_message(self, state_manager):
        """Test converting dict to Message."""
        msg_dict = {
            "sender_id": "test-id",
            "sender_callsign": "TEST",
            "recipient_callsign": "ALPHA",
            "content": "Test message",
            "message_type": "user",
            "metadata": {"key": "value"}
        }

        msg = state_manager._dict_to_message(msg_dict)

        assert msg.sender_id == "test-id"
        assert msg.sender_callsign == "TEST"
        assert msg.recipient_callsign == "ALPHA"
        assert msg.content == "Test message"
        assert msg.message_type == MessageType.USER
        assert msg.metadata == {"key": "value"}

    def test_message_roundtrip(self, state_manager):
        """Test message conversion roundtrip."""
        original = Message(
            sender_id="test",
            content="Test",
            message_type=MessageType.SYSTEM
        )

        msg_dict = state_manager._message_to_dict(original)
        restored = state_manager._dict_to_message(msg_dict)

        assert restored.sender_id == original.sender_id
        assert restored.content == original.content
        assert restored.message_type == original.message_type


class TestSessionExport:
    """Test session export functionality."""

    @pytest.mark.asyncio
    async def test_export_session_json(self, state_manager, sample_channel, sample_agents):
        """Test exporting session as JSON."""
        # Save session
        await state_manager.save_session(
            session_id="test-export",
            channel=sample_channel,
            agents=sample_agents,
            metadata={"description": "Test"}
        )

        # Export to temp file
        temp_dir = tempfile.mkdtemp()
        export_path = os.path.join(temp_dir, "export.json")

        result = await state_manager.export_session(
            session_id="test-export",
            export_path=export_path,
            format="json"
        )

        assert result is True
        assert os.path.exists(export_path)

        # Verify JSON content
        with open(export_path, 'r') as f:
            data = json.load(f)
            assert data["session_id"] == "test-export"
            assert len(data["messages"]) == 2
            assert len(data["agent_states"]) == 2

        # Cleanup
        os.remove(export_path)
        os.rmdir(temp_dir)

    @pytest.mark.asyncio
    async def test_export_session_txt(self, state_manager, sample_channel, sample_agents):
        """Test exporting session as text."""
        # Save session
        await state_manager.save_session(
            session_id="test-export-txt",
            channel=sample_channel,
            agents=sample_agents
        )

        # Export to temp file
        temp_dir = tempfile.mkdtemp()
        export_path = os.path.join(temp_dir, "export.txt")

        result = await state_manager.export_session(
            session_id="test-export-txt",
            export_path=export_path,
            format="txt"
        )

        assert result is True
        assert os.path.exists(export_path)

        # Verify text content
        with open(export_path, 'r') as f:
            content = f.read()
            assert "test-export-txt" in content
            assert "Hello agents" in content
            assert "Roger, received" in content

        # Cleanup
        os.remove(export_path)
        os.rmdir(temp_dir)

    @pytest.mark.asyncio
    async def test_export_nonexistent_session(self, state_manager):
        """Test exporting a session that doesn't exist."""
        temp_dir = tempfile.mkdtemp()
        export_path = os.path.join(temp_dir, "export.json")

        result = await state_manager.export_session(
            session_id="nonexistent",
            export_path=export_path
        )

        assert result is False
        assert not os.path.exists(export_path)

        # Cleanup
        os.rmdir(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
