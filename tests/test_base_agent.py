"""
Unit tests for BaseAgent class.

Tests core agent functionality including:
- Initialization
- Memory operations
- Message history building
- System prompt construction
- Tool execution
- Response criteria
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from src.agents.base_agent import BaseAgent
from src.channel.shared_channel import SharedChannel
from src.channel.message import Message, MessageType
from .mocks.mock_mcp_manager import create_mock_mcp_manager


class TestBaseAgentInitialization:
    """Test agent initialization."""

    def test_agent_initialization_basic(self):
        """Test basic agent initialization."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        assert agent.agent_id == "test-1"
        assert agent.callsign == "TEST-ONE"
        assert agent.system_prompt == "You are a test agent."
        assert agent.model == "claude-sonnet-4-5-20250929"
        assert agent.temperature == 1.0
        assert agent.max_tokens == 1024

    def test_agent_initialization_with_mcp(self):
        """Test agent initialization with MCP manager."""
        mock_mcp = create_mock_mcp_manager()
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent.",
            mcp_manager=mock_mcp
        )

        assert agent.mcp_manager is not None
        assert agent.mcp_manager == mock_mcp

    def test_agent_initialization_custom_params(self):
        """Test agent initialization with custom parameters."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent.",
            model="claude-3-5-sonnet-20241022",
            temperature=0.5,
            max_tokens=2048
        )

        assert agent.model == "claude-3-5-sonnet-20241022"
        assert agent.temperature == 0.5
        assert agent.max_tokens == 2048

    def test_agent_memory_initialized_empty(self):
        """Test that agent memory is initialized empty."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        assert agent.memory["task_list"] == []
        assert agent.memory["key_facts"] == {}
        assert agent.memory["decisions_made"] == []
        assert agent.memory["concerns"] == []
        assert agent.memory["notes"] == []


class TestMemoryOperations:
    """Test agent memory operations."""

    def test_update_memory_task_list(self):
        """Test updating task list memory."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        agent.update_memory("task_list", "Task 1")
        agent.update_memory("task_list", "Task 2")

        assert agent.memory["task_list"] == ["Task 1", "Task 2"]

    def test_update_memory_key_facts(self):
        """Test updating key facts memory."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        agent.update_memory("key_facts", "location=Boston")
        agent.update_memory("key_facts", "weather=Clear")

        assert agent.memory["key_facts"]["location"] == "Boston"
        assert agent.memory["key_facts"]["weather"] == "Clear"

    def test_update_memory_decisions(self):
        """Test updating decisions memory."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        agent.update_memory("decisions_made", "Decision 1")

        assert "Decision 1" in agent.memory["decisions_made"]

    def test_build_memory_context_empty(self):
        """Test building memory context when memory is empty."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        context = agent._build_memory_context()

        assert context == ""

    def test_build_memory_context_with_tasks(self):
        """Test building memory context with tasks."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        agent.update_memory("task_list", "Task 1")
        agent.update_memory("task_list", "Task 2")
        context = agent._build_memory_context()

        assert "Active Tasks:" in context
        assert "1. Task 1" in context
        assert "2. Task 2" in context

    def test_build_memory_context_with_facts(self):
        """Test building memory context with key facts."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        agent.update_memory("key_facts", "airport=KBOS")
        agent.update_memory("key_facts", "runway=04R")
        context = agent._build_memory_context()

        assert "Key Facts:" in context
        assert "airport: KBOS" in context
        assert "runway: 04R" in context

    def test_build_memory_context_comprehensive(self):
        """Test building memory context with all categories."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        agent.update_memory("task_list", "Search airports")
        agent.update_memory("key_facts", "location=Boston")
        agent.update_memory("decisions_made", "Use KBOS")
        agent.update_memory("concerns", "Weather deteriorating")
        agent.update_memory("notes", "Fuel check needed")

        context = agent._build_memory_context()

        assert "Active Tasks:" in context
        assert "Key Facts:" in context
        assert "Recent Decisions:" in context
        assert "Active Concerns:" in context
        assert "Notes:" in context


class TestMessageHistory:
    """Test message history building."""

    def test_build_message_history_empty(self):
        """Test building message history with no messages."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        context_messages = []
        history = agent._build_message_history(context_messages)

        # Should have at least one default message
        assert len(history) == 1
        assert "Channel is active" in history[0]["content"]

    def test_build_message_history_single_message(self):
        """Test building message history with one message."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        channel = SharedChannel()
        channel.add_message(
            sender_id="user",
            content="Hello",
            sender_callsign="USER",
            message_type=MessageType.USER
        )

        context_messages = channel.get_recent_messages(10)
        history = agent._build_message_history(context_messages)

        assert len(history) == 1
        assert history[0]["role"] == "user"
        assert "Hello" in history[0]["content"]

    def test_build_message_history_multiple_messages(self):
        """Test building message history with multiple messages."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        channel = SharedChannel()
        channel.add_message(sender_id="user", content="Message 1", sender_callsign="USER", message_type=MessageType.USER)
        channel.add_message(sender_id="test-1", content="Response 1", sender_callsign="TEST-ONE", message_type=MessageType.AGENT)
        channel.add_message(sender_id="user", content="Message 2", sender_callsign="USER", message_type=MessageType.USER)

        context_messages = channel.get_recent_messages(10)
        history = agent._build_message_history(context_messages)

        # Should only include messages not from this agent
        assert len(history) == 2
        assert history[0]["role"] == "user"
        assert history[1]["role"] == "user"

    def test_build_message_history_respects_context_window(self):
        """Test that message history respects context window."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        channel = SharedChannel()
        for i in range(20):
            channel.add_message(
                sender_id="user",
                content=f"Message {i}",
                sender_callsign="USER",
                message_type=MessageType.USER
            )

        # Get only last 5 messages
        context_messages = channel.get_recent_messages(5)
        history = agent._build_message_history(context_messages)

        # Should only include last 5 messages
        assert len(history) == 5


class TestSystemPrompt:
    """Test system prompt construction."""

    def test_build_system_prompt_basic(self):
        """Test building basic system prompt without memory."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        prompt = agent._build_system_prompt()

        assert "You are a test agent." in prompt
        assert "YOUR CURRENT MEMORY" not in prompt

    def test_build_system_prompt_with_memory(self):
        """Test building system prompt with memory."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        agent.update_memory("task_list", ["Task 1"])
        prompt = agent._build_system_prompt()

        assert "You are a test agent." in prompt
        assert "YOUR CURRENT MEMORY" in prompt
        assert "Active Tasks:" in prompt


class TestToolOperations:
    """Test tool-related operations."""

    def test_format_tools_no_mcp(self):
        """Test formatting tools when no MCP manager."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        tools = agent._format_tools_for_claude()

        assert tools == []

    def test_format_tools_with_mcp(self):
        """Test formatting tools with MCP manager."""
        mock_mcp = create_mock_mcp_manager()
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent.",
            mcp_manager=mock_mcp
        )

        tools = agent._format_tools_for_claude()

        assert len(tools) > 0
        assert "name" in tools[0]
        assert "description" in tools[0]
        assert "input_schema" in tools[0]

    @pytest.mark.asyncio
    async def test_execute_tool_success(self):
        """Test successful tool execution."""
        mock_mcp = create_mock_mcp_manager()
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent.",
            mcp_manager=mock_mcp
        )

        result = await agent._execute_tool(
            "search_airports",
            {"query": "Boston"}
        )

        assert "airports" in result.lower() or "KBOS" in result
        assert mock_mcp.get_call_count("search_airports") == 1

    @pytest.mark.asyncio
    async def test_execute_tool_no_mcp(self):
        """Test tool execution without MCP manager."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        result = await agent._execute_tool(
            "search_airports",
            {"query": "Boston"}
        )

        assert "Error" in result or "No MCP manager" in result

    @pytest.mark.asyncio
    async def test_execute_tool_failure(self):
        """Test tool execution failure."""
        mock_mcp = create_mock_mcp_manager(should_fail=True)
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent.",
            mcp_manager=mock_mcp
        )

        result = await agent._execute_tool(
            "search_airports",
            {"query": "Boston"}
        )

        assert "Error" in result


class TestShouldRespond:
    """Test response decision logic."""

    def test_should_respond_direct_address(self):
        """Test that agent responds to direct address."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        channel = SharedChannel()
        # Using voice net protocol format for direct address
        channel.add_message(
            sender_id="user",
            content="TEST-ONE, search for airports",
            sender_callsign="USER",
            message_type=MessageType.USER
        )

        # Should respond to direct address
        assert agent.should_respond(channel) is True

    def test_should_respond_not_addressed(self):
        """Test that agent doesn't respond when not addressed."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        channel = SharedChannel()
        # Message addressed to a different agent
        channel.add_message(
            sender_id="user",
            content="TEST-TWO, search for airports",
            sender_callsign="USER",
            message_type=MessageType.USER
        )

        # Should not respond to different callsign
        assert agent.should_respond(channel) is False

    def test_should_respond_broadcast(self):
        """Test that agent responds to broadcast."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        channel = SharedChannel()
        # Broadcast message using proper voice net protocol format
        channel.add_message(
            sender_id="user",
            content="All stations, this is USER, prepare for briefing, over.",
            sender_callsign="USER",
            message_type=MessageType.USER
        )

        # Should respond to broadcast
        assert agent.should_respond(channel) is True


class TestMemoryExtraction:
    """Test memory extraction from responses."""

    def test_extract_memory_updates_empty(self):
        """Test extracting memory from response with no MEMORIZE commands."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        response = "This is a normal response without memory updates."
        agent._extract_memory_updates(response)

        # Memory should remain empty
        assert agent.memory["task_list"] == []
        assert agent.memory["key_facts"] == {}
        assert agent.memory["decisions_made"] == []

    def test_extract_memory_updates_task_list(self):
        """Test extracting task list memory updates."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        # Using the correct pattern: MEMORIZE[category]: content
        response = """
        Some response text.
        MEMORIZE[task_list]: Task 1
        MEMORIZE[task_list]: Task 2
        More text.
        """
        agent._extract_memory_updates(response)

        assert "Task 1" in agent.memory["task_list"]
        assert "Task 2" in agent.memory["task_list"]

    def test_extract_memory_updates_key_facts(self):
        """Test extracting key facts memory updates."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        # Using the correct pattern and key=value format
        response = """
        MEMORIZE[key_facts]: airport=KBOS
        MEMORIZE[key_facts]: runway=04R
        """
        agent._extract_memory_updates(response)

        assert agent.memory["key_facts"]["airport"] == "KBOS"
        assert agent.memory["key_facts"]["runway"] == "04R"

    def test_extract_memory_updates_multiple(self):
        """Test extracting multiple memory updates."""
        agent = BaseAgent(
            agent_id="test-1",
            callsign="TEST-ONE",
            system_prompt="You are a test agent."
        )

        response = """
        MEMORIZE[task_list]: Task 1
        MEMORIZE[key_facts]: location=Boston
        MEMORIZE[decisions_made]: Use KBOS
        """
        agent._extract_memory_updates(response)

        assert "Task 1" in agent.memory["task_list"]
        assert agent.memory["key_facts"]["location"] == "Boston"
        assert "Use KBOS" in agent.memory["decisions_made"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
