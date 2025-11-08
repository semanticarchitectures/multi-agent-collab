"""
Unit tests for Orchestrator class.

Tests orchestrator functionality including:
- Agent management
- Message routing
- Directed communication
- Turn processing
- Status tracking
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.orchestration.orchestrator import Orchestrator
from src.channel.shared_channel import SharedChannel
from src.channel.message import Message, MessageType
from src.agents.base_agent import BaseAgent
from src.agents.squad_leader import SquadLeaderAgent


# Mock agents for testing
class MockAgent:
    """Mock agent for testing."""

    def __init__(self, agent_id: str, callsign: str, should_respond_value: bool = False):
        self.agent_id = agent_id
        self.callsign = callsign
        self._should_respond = should_respond_value
        self.respond_called = False
        self.respond_message = None

    def should_respond(self, channel, context_window=10):
        """Mock should_respond."""
        return self._should_respond

    async def respond(self, channel, context_window=20):
        """Mock respond."""
        self.respond_called = True
        # Create a mock message response
        message = channel.add_message(
            sender_id=self.agent_id,
            content=f"Response from {self.callsign}",
            sender_callsign=self.callsign,
            message_type=MessageType.AGENT
        )
        self.respond_message = message
        return message

    def get_agent_type(self):
        """Mock get_agent_type."""
        return "base"


class MockSquadLeader(MockAgent):
    """Mock squad leader for testing."""

    def get_agent_type(self):
        """Mock get_agent_type."""
        return "squad_leader"


class TestOrchestratorInitialization:
    """Test orchestrator initialization."""

    def test_orchestrator_initialization_basic(self):
        """Test basic orchestrator initialization."""
        orch = Orchestrator()

        assert orch.channel is not None
        assert isinstance(orch.channel, SharedChannel)
        assert len(orch.agents) == 0
        assert orch.squad_leader is None
        assert orch.max_agents == 6
        assert orch.context_window == 20
        assert orch.is_running is False

    def test_orchestrator_initialization_with_channel(self):
        """Test orchestrator initialization with existing channel."""
        channel = SharedChannel()
        channel.add_message(
            sender_id="test",
            content="Test message",
            message_type=MessageType.SYSTEM
        )

        orch = Orchestrator(channel=channel)

        assert orch.channel is channel
        assert orch.channel.get_message_count() == 1

    def test_orchestrator_initialization_custom_params(self):
        """Test orchestrator initialization with custom parameters."""
        orch = Orchestrator(max_agents=4, context_window=15)

        assert orch.max_agents == 4
        assert orch.context_window == 15


class TestAgentManagement:
    """Test agent management operations."""

    def test_add_agent(self):
        """Test adding an agent."""
        orch = Orchestrator()
        agent = MockAgent("agent-1", "ALPHA-ONE")

        result = orch.add_agent(agent)

        assert result is True
        assert len(orch.agents) == 1
        assert orch.agents["agent-1"] is agent

        # Check system message was added
        messages = orch.channel.get_recent_messages(1)
        assert len(messages) == 1
        assert "ALPHA-ONE has joined" in messages[0].content

    def test_add_multiple_agents(self):
        """Test adding multiple agents."""
        orch = Orchestrator()
        agent1 = MockAgent("agent-1", "ALPHA-ONE")
        agent2 = MockAgent("agent-2", "ALPHA-TWO")
        agent3 = MockAgent("agent-3", "BRAVO-ONE")

        orch.add_agent(agent1)
        orch.add_agent(agent2)
        orch.add_agent(agent3)

        assert len(orch.agents) == 3
        assert orch.get_agent_count() == 3

    def test_add_agent_max_capacity(self):
        """Test adding agents beyond max capacity."""
        orch = Orchestrator(max_agents=2)
        agent1 = MockAgent("agent-1", "ALPHA-ONE")
        agent2 = MockAgent("agent-2", "ALPHA-TWO")
        agent3 = MockAgent("agent-3", "BRAVO-ONE")

        result1 = orch.add_agent(agent1)
        result2 = orch.add_agent(agent2)
        result3 = orch.add_agent(agent3)

        assert result1 is True
        assert result2 is True
        assert result3 is False  # Should reject third agent
        assert len(orch.agents) == 2

    def test_add_squad_leader(self):
        """Test adding a squad leader agent."""
        orch = Orchestrator()
        leader = MockSquadLeader("leader-1", "ALPHA-LEAD")

        # Mock isinstance check
        with patch('src.orchestration.orchestrator.isinstance') as mock_isinstance:
            mock_isinstance.side_effect = lambda obj, cls: (
                cls == SquadLeaderAgent if obj is leader else False
            )
            orch.add_agent(leader)

        assert orch.squad_leader is leader

    def test_remove_agent(self):
        """Test removing an agent."""
        orch = Orchestrator()
        agent = MockAgent("agent-1", "ALPHA-ONE")
        orch.add_agent(agent)

        result = orch.remove_agent("agent-1")

        assert result is True
        assert len(orch.agents) == 0
        assert "agent-1" not in orch.agents

        # Check system message
        messages = orch.channel.get_recent_messages(1)
        assert "ALPHA-ONE has left" in messages[0].content

    def test_remove_nonexistent_agent(self):
        """Test removing an agent that doesn't exist."""
        orch = Orchestrator()

        result = orch.remove_agent("nonexistent")

        assert result is False

    def test_remove_squad_leader(self):
        """Test removing squad leader clears squad_leader reference."""
        orch = Orchestrator()
        leader = MockSquadLeader("leader-1", "ALPHA-LEAD")

        with patch('src.orchestration.orchestrator.isinstance') as mock_isinstance:
            mock_isinstance.side_effect = lambda obj, cls: (
                cls == SquadLeaderAgent if obj is leader else False
            )
            orch.add_agent(leader)

        assert orch.squad_leader is leader

        orch.remove_agent("leader-1")

        assert orch.squad_leader is None

    def test_get_agent(self):
        """Test getting an agent by ID."""
        orch = Orchestrator()
        agent = MockAgent("agent-1", "ALPHA-ONE")
        orch.add_agent(agent)

        retrieved = orch.get_agent("agent-1")

        assert retrieved is agent

    def test_get_nonexistent_agent(self):
        """Test getting an agent that doesn't exist."""
        orch = Orchestrator()

        result = orch.get_agent("nonexistent")

        assert result is None

    def test_get_active_agents(self):
        """Test getting all active agents."""
        orch = Orchestrator()
        agent1 = MockAgent("agent-1", "ALPHA-ONE")
        agent2 = MockAgent("agent-2", "ALPHA-TWO")
        orch.add_agent(agent1)
        orch.add_agent(agent2)

        agents = orch.get_active_agents()

        assert len(agents) == 2
        assert agent1 in agents
        assert agent2 in agents


class TestMessageHandling:
    """Test message handling operations."""

    def test_send_user_message(self):
        """Test sending a user message."""
        orch = Orchestrator()

        msg = orch.send_user_message("Hello agents")

        assert msg is not None
        assert msg.sender_id == "user"
        assert msg.content == "Hello agents"
        assert msg.message_type == MessageType.USER

    def test_send_user_message_custom_user_id(self):
        """Test sending a user message with custom user ID."""
        orch = Orchestrator()

        msg = orch.send_user_message("Hello", user_id="custom-user")

        assert msg.sender_id == "custom-user"

    def test_clear_channel(self):
        """Test clearing the channel."""
        orch = Orchestrator()
        orch.send_user_message("Message 1")
        orch.send_user_message("Message 2")

        assert orch.channel.get_message_count() == 2

        orch.clear_channel()

        assert orch.channel.get_message_count() == 0

    def test_get_channel_history(self):
        """Test getting channel history."""
        orch = Orchestrator()
        orch.send_user_message("Message 1")
        orch.send_user_message("Message 2")

        history = orch.get_channel_history(count=2)

        assert "Message 1" in history
        assert "Message 2" in history


class TestAgentLookup:
    """Test agent lookup by callsign."""

    def test_find_agent_by_callsign_exact(self):
        """Test finding agent by exact callsign."""
        orch = Orchestrator()
        agent = MockAgent("agent-1", "ALPHA-ONE")
        orch.add_agent(agent)

        found = orch._find_agent_by_callsign("ALPHA-ONE")

        assert found is agent

    def test_find_agent_by_callsign_case_insensitive(self):
        """Test finding agent by callsign (case insensitive)."""
        orch = Orchestrator()
        agent = MockAgent("agent-1", "ALPHA-ONE")
        orch.add_agent(agent)

        found = orch._find_agent_by_callsign("alpha-one")

        assert found is agent

    def test_find_agent_by_callsign_with_separators(self):
        """Test finding agent with different separators."""
        orch = Orchestrator()
        agent = MockAgent("agent-1", "ALPHA-ONE")
        orch.add_agent(agent)

        # Should match with underscores or spaces
        found1 = orch._find_agent_by_callsign("ALPHA_ONE")
        found2 = orch._find_agent_by_callsign("ALPHA ONE")

        assert found1 is agent
        assert found2 is agent

    def test_find_agent_by_callsign_not_found(self):
        """Test finding agent that doesn't exist."""
        orch = Orchestrator()
        agent = MockAgent("agent-1", "ALPHA-ONE")
        orch.add_agent(agent)

        found = orch._find_agent_by_callsign("BRAVO-ONE")

        assert found is None


class TestResponseProcessing:
    """Test response processing logic."""

    @pytest.mark.asyncio
    async def test_process_responses_no_messages(self):
        """Test processing responses with no messages."""
        orch = Orchestrator()
        agent = MockAgent("agent-1", "ALPHA-ONE", should_respond_value=True)
        orch.add_agent(agent)

        # Clear the join message
        orch.clear_channel()

        responses = await orch.process_responses()

        # Should handle gracefully with no messages
        assert responses == []

    @pytest.mark.asyncio
    async def test_process_responses_broadcast(self):
        """Test processing responses for broadcast message."""
        orch = Orchestrator()
        agent1 = MockAgent("agent-1", "ALPHA-ONE", should_respond_value=True)
        agent2 = MockAgent("agent-2", "ALPHA-TWO", should_respond_value=True)
        orch.add_agent(agent1)
        orch.add_agent(agent2)

        # Use proper voice net protocol format for broadcast
        orch.send_user_message("All stations, this is USER, report status, over.")

        responses = await orch.process_responses(max_responses=2)

        # Both agents should respond
        assert len(responses) == 2
        assert agent1.respond_called
        assert agent2.respond_called

    @pytest.mark.asyncio
    async def test_process_responses_directed(self):
        """Test processing responses for directed message."""
        orch = Orchestrator()
        agent1 = MockAgent("agent-1", "ALPHA-ONE", should_respond_value=True)
        agent2 = MockAgent("agent-2", "ALPHA-TWO", should_respond_value=True)
        orch.add_agent(agent1)
        orch.add_agent(agent2)

        # Send directed message to ALPHA-ONE
        orch.send_user_message("ALPHA-ONE, report your status")

        responses = await orch.process_responses()

        # Only ALPHA-ONE should respond
        assert len(responses) == 1
        assert agent1.respond_called
        assert not agent2.respond_called

    @pytest.mark.asyncio
    async def test_process_responses_max_responses(self):
        """Test max_responses limit."""
        orch = Orchestrator()
        agent1 = MockAgent("agent-1", "ALPHA-ONE", should_respond_value=True)
        agent2 = MockAgent("agent-2", "ALPHA-TWO", should_respond_value=True)
        agent3 = MockAgent("agent-3", "BRAVO-ONE", should_respond_value=True)
        orch.add_agent(agent1)
        orch.add_agent(agent2)
        orch.add_agent(agent3)

        # Use proper voice net protocol format for broadcast
        orch.send_user_message("All stations, this is USER, report, over.")

        responses = await orch.process_responses(max_responses=2)

        # Should limit to 2 responses
        assert len(responses) == 2

    @pytest.mark.asyncio
    async def test_process_responses_squad_leader_fallback(self):
        """Test squad leader responds when no one else does."""
        orch = Orchestrator()
        agent = MockAgent("agent-1", "ALPHA-ONE", should_respond_value=False)
        leader = MockSquadLeader("leader-1", "ALPHA-LEAD", should_respond_value=False)

        with patch('src.orchestration.orchestrator.isinstance') as mock_isinstance:
            mock_isinstance.side_effect = lambda obj, cls: (
                cls == SquadLeaderAgent if obj is leader else False
            )
            orch.add_agent(agent)
            orch.add_agent(leader)

        orch.send_user_message("Status report")

        responses = await orch.process_responses()

        # Squad leader should respond as fallback
        assert len(responses) == 1
        assert leader.respond_called
        assert not agent.respond_called

    @pytest.mark.asyncio
    async def test_process_responses_directed_not_found_uses_leader(self):
        """Test squad leader responds when directed agent not found."""
        orch = Orchestrator()
        leader = MockSquadLeader("leader-1", "ALPHA-LEAD", should_respond_value=False)

        with patch('src.orchestration.orchestrator.isinstance') as mock_isinstance:
            mock_isinstance.side_effect = lambda obj, cls: (
                cls == SquadLeaderAgent if obj is leader else False
            )
            orch.add_agent(leader)

        # Message directed to non-existent agent
        orch.send_user_message("NONEXISTENT, report status")

        responses = await orch.process_responses()

        # Squad leader should handle it
        assert len(responses) == 1
        assert leader.respond_called

    @pytest.mark.asyncio
    async def test_process_responses_error_handling(self):
        """Test error handling during response generation."""
        orch = Orchestrator()
        agent = MockAgent("agent-1", "ALPHA-ONE", should_respond_value=True)

        # Make respond raise an exception
        async def failing_respond(channel, context_window):
            raise Exception("Test error")

        agent.respond = failing_respond
        orch.add_agent(agent)

        orch.send_user_message("Test message")

        # Should handle error gracefully
        responses = await orch.process_responses()

        assert responses == []


class TestTurnProcessing:
    """Test turn processing."""

    @pytest.mark.asyncio
    async def test_run_turn_with_user_message(self):
        """Test running a turn with user message."""
        orch = Orchestrator()
        agent = MockAgent("agent-1", "ALPHA-ONE", should_respond_value=True)
        orch.add_agent(agent)

        turn_data = await orch.run_turn(user_message="Test message", max_agent_responses=1)

        assert turn_data["user_message"] is not None
        assert turn_data["user_message"].content == "Test message"
        assert len(turn_data["agent_responses"]) == 1
        assert isinstance(turn_data["timestamp"], datetime)

    @pytest.mark.asyncio
    async def test_run_turn_without_user_message(self):
        """Test running a turn without user message."""
        orch = Orchestrator()
        agent = MockAgent("agent-1", "ALPHA-ONE", should_respond_value=True)
        orch.add_agent(agent)

        # Add a message first
        orch.send_user_message("Previous message")

        turn_data = await orch.run_turn(max_agent_responses=1)

        assert turn_data["user_message"] is None
        assert len(turn_data["agent_responses"]) >= 0


class TestOrchestratorStatus:
    """Test orchestrator status and control."""

    def test_start(self):
        """Test starting orchestrator."""
        orch = Orchestrator()

        orch.start()

        assert orch.is_running is True

        messages = orch.channel.get_recent_messages(1)
        assert "session started" in messages[0].content.lower()

    def test_stop(self):
        """Test stopping orchestrator."""
        orch = Orchestrator()
        orch.start()

        orch.stop()

        assert orch.is_running is False

        messages = orch.channel.get_recent_messages(1)
        assert "session ended" in messages[0].content.lower()

    def test_get_status(self):
        """Test getting orchestrator status."""
        orch = Orchestrator()
        agent1 = MockAgent("agent-1", "ALPHA-ONE")
        agent2 = MockAgent("agent-2", "ALPHA-TWO")
        leader = MockSquadLeader("leader-1", "ALPHA-LEAD")

        with patch('src.orchestration.orchestrator.isinstance') as mock_isinstance:
            mock_isinstance.side_effect = lambda obj, cls: (
                cls == SquadLeaderAgent if obj is leader else False
            )
            orch.add_agent(agent1)
            orch.add_agent(agent2)
            orch.add_agent(leader)

        orch.start()

        status = orch.get_status()

        assert status["is_running"] is True
        assert status["agent_count"] == 3
        assert status["has_squad_leader"] is True
        assert status["message_count"] > 0
        assert len(status["agents"]) == 3

        # Check agent details
        agent_ids = [a["id"] for a in status["agents"]]
        assert "agent-1" in agent_ids
        assert "agent-2" in agent_ids
        assert "leader-1" in agent_ids

    def test_get_status_no_squad_leader(self):
        """Test status when no squad leader."""
        orch = Orchestrator()
        agent = MockAgent("agent-1", "ALPHA-ONE")
        orch.add_agent(agent)

        status = orch.get_status()

        assert status["has_squad_leader"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
