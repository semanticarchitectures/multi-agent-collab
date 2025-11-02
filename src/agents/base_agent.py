"""Base agent class for multi-agent collaboration."""

import os
from typing import List, Optional, Dict, Any
from anthropic import Anthropic

from ..channel.message import Message, MessageType
from ..channel.shared_channel import SharedChannel
from ..channel.voice_net_protocol import VoiceNetProtocol
from .speaking_criteria import SpeakingCriteria, DirectAddressCriteria
from ..mcp.mcp_manager import MCPManager


class BaseAgent:
    """Base class for all agents in the system.

    Agents communicate via a shared channel using voice net protocol.
    Each agent has a unique ID, callsign, system prompt, and speaking criteria.
    """

    def __init__(
        self,
        agent_id: str,
        callsign: str,
        system_prompt: str,
        speaking_criteria: Optional[SpeakingCriteria] = None,
        mcp_manager: Optional[MCPManager] = None,
        model: str = "claude-sonnet-4-5-20250929",
        temperature: float = 1.0,
        max_tokens: int = 1024
    ):
        """Initialize the agent.

        Args:
            agent_id: Unique identifier for the agent
            callsign: Radio callsign for voice net protocol
            system_prompt: System prompt defining agent behavior
            speaking_criteria: Criteria for when to respond
            mcp_manager: Optional MCP manager for tool access
            model: Claude model to use
            temperature: Temperature for response generation
            max_tokens: Maximum tokens in response
        """
        self.agent_id = agent_id
        self.callsign = callsign
        self.system_prompt = system_prompt
        self.speaking_criteria = speaking_criteria or DirectAddressCriteria()
        self.mcp_manager = mcp_manager
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = Anthropic(api_key=api_key)
        self.protocol = VoiceNetProtocol()

    def should_respond(
        self,
        channel: SharedChannel,
        context_window: int = 10
    ) -> bool:
        """Determine if the agent should respond based on recent messages.

        Args:
            channel: Shared communication channel
            context_window: Number of recent messages to consider

        Returns:
            True if agent should respond
        """
        recent_messages = channel.get_recent_messages(context_window)
        return self.speaking_criteria.should_respond(
            self.agent_id,
            self.callsign,
            recent_messages
        )

    async def generate_response(
        self,
        channel: SharedChannel,
        context_window: int = 20
    ) -> str:
        """Generate a response based on channel context with autonomous tool use.

        Args:
            channel: Shared communication channel
            context_window: Number of messages to include in context

        Returns:
            Generated response text
        """
        # Get context messages
        context_messages = channel.get_context_window(
            self.callsign,
            window_size=context_window
        )

        # Build conversation history
        messages = self._build_message_history(context_messages)

        # Get available MCP tools if manager is available
        tools = None
        if self.mcp_manager and self.mcp_manager.is_initialized():
            tools = self._format_tools_for_claude()

        # Generate initial response using Claude
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=self._build_system_prompt(),
            messages=messages,
            tools=tools if tools else None
        )

        # Tool use loop - continue until we get a text response
        while response.stop_reason == "tool_use":
            # Extract tool calls from response
            tool_uses = [block for block in response.content if block.type == "tool_use"]

            # Execute each tool
            tool_results = []
            for tool_use in tool_uses:
                result = await self._execute_tool(tool_use.name, tool_use.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": str(result)
                })

            # Add assistant's tool use to message history
            messages.append({
                "role": "assistant",
                "content": response.content
            })

            # Add tool results as user message
            messages.append({
                "role": "user",
                "content": tool_results
            })

            # Continue conversation with tool results
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=self._build_system_prompt(),
                messages=messages,
                tools=tools if tools else None
            )

        # Extract final text from response
        response_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                response_text += block.text

        return response_text.strip()

    async def respond(
        self,
        channel: SharedChannel,
        context_window: int = 20
    ) -> Optional[Message]:
        """Generate and send a response to the channel.

        Args:
            channel: Shared communication channel
            context_window: Number of messages to include in context

        Returns:
            The sent message, or None if generation failed
        """
        try:
            response_text = await self.generate_response(channel, context_window)

            if not response_text:
                return None

            # Post message to channel
            message = channel.add_message(
                sender_id=self.agent_id,
                content=response_text,
                sender_callsign=self.callsign,
                message_type=MessageType.AGENT
            )

            return message

        except Exception as e:
            print(f"Error generating response for {self.callsign}: {e}")
            return None

    def _build_system_prompt(self) -> str:
        """Build the full system prompt for the agent with dynamic tool injection.

        Returns:
            Complete system prompt
        """
        base_prompt = f"""You are {self.callsign}, an AI agent in a multi-agent collaboration system.

{self.system_prompt}

COMMUNICATION PROTOCOL:
You communicate using voice net protocol (like pilot-ATC radio communication):
- Format: "[Recipient], this is {self.callsign}, [message], over."
- Use "Roger" to acknowledge: "Roger, [acknowledgment]."
- Use "Copy" to confirm: "Copy, [confirmation]."
- Address other agents by their callsigns
- Keep messages clear and concise
- End transmissions with "over" when expecting a response

Your callsign is: {self.callsign}"""

        # Add tool information if MCP manager is available
        if self.mcp_manager and self.mcp_manager.is_initialized():
            tools = self.mcp_manager.get_available_tools()
            if tools:
                tool_descriptions = "\n\nAVAILABLE MCP TOOLS:\n"
                tool_descriptions += "You have access to the following tools. Use them when appropriate to complete tasks:\n"
                for tool in tools:
                    tool_descriptions += f"\n- {tool['name']}: {tool['description']}"
                base_prompt += tool_descriptions

        base_prompt += "\n\nRemember to stay in character and follow the voice net protocol for all communications."

        return base_prompt

    def _build_message_history(
        self,
        context_messages: List[Message]
    ) -> List[Dict[str, Any]]:
        """Build message history for Claude API.

        Args:
            context_messages: Messages to include in history

        Returns:
            List of message dicts for Claude API
        """
        messages = []

        for msg in context_messages:
            # Skip our own messages in the input
            if msg.sender_id == self.agent_id:
                continue

            role = "user"  # All other messages are treated as user input
            content = f"[{msg.sender_callsign or msg.sender_id}]: {msg.content}"

            messages.append({
                "role": role,
                "content": content
            })

        # Ensure we have at least one message
        if not messages:
            messages.append({
                "role": "user",
                "content": "Channel is active. Monitoring communications."
            })

        return messages

    def _format_tools_for_claude(self) -> List[Dict[str, Any]]:
        """Format MCP tools for Claude API.

        Returns:
            List of tool definitions in Anthropic format
        """
        if not self.mcp_manager:
            return []

        mcp_tools = self.mcp_manager.get_available_tools()
        claude_tools = []

        for tool in mcp_tools:
            claude_tool = {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["input_schema"]
            }
            claude_tools.append(claude_tool)

        return claude_tools

    async def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute an MCP tool and return the result.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments

        Returns:
            Tool result as string
        """
        if not self.mcp_manager:
            return "Error: No MCP manager available"

        try:
            result = await self.mcp_manager.call_tool(tool_name, arguments)

            # Extract text from MCP result
            if result and hasattr(result, 'content') and result.content:
                # MCP results typically have a content array
                if isinstance(result.content, list) and len(result.content) > 0:
                    return result.content[0].text
                return str(result.content)

            return str(result)

        except Exception as e:
            error_msg = f"Error executing tool {tool_name}: {str(e)}"
            print(error_msg)
            return error_msg

    def get_agent_type(self) -> str:
        """Get the type of agent.

        Returns:
            Agent type string
        """
        return "base"

    def __repr__(self) -> str:
        """String representation of the agent."""
        return f"{self.__class__.__name__}(id={self.agent_id}, callsign={self.callsign})"
