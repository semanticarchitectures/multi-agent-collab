"""Configuration schema using Pydantic."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class SpeakingCriteriaConfig(BaseModel):
    """Configuration for agent speaking criteria."""

    type: str = Field(..., description="Type of criteria (direct_address, keywords, squad_leader, etc.)")
    keywords: Optional[List[str]] = Field(None, description="Keywords for keyword-based criteria")
    case_sensitive: bool = Field(False, description="Whether keyword matching is case-sensitive")


class AgentConfig(BaseModel):
    """Configuration for a single agent."""

    agent_id: str = Field(..., description="Unique agent identifier")
    callsign: str = Field(..., description="Radio callsign")
    agent_type: str = Field("base", description="Type of agent (base, squad_leader)")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    model: str = Field("claude-sonnet-4-5-20250929", description="Claude model to use")
    temperature: float = Field(1.0, ge=0.0, le=2.0, description="Temperature for generation")
    max_tokens: int = Field(1024, gt=0, description="Maximum tokens in response")
    speaking_criteria: Optional[List[SpeakingCriteriaConfig]] = Field(
        None,
        description="Speaking criteria configurations"
    )

    @validator("agent_type")
    def validate_agent_type(cls, v):
        """Validate agent type."""
        allowed = ["base", "squad_leader"]
        if v not in allowed:
            raise ValueError(f"agent_type must be one of {allowed}")
        return v


class ChannelConfig(BaseModel):
    """Configuration for the shared channel."""

    max_history: int = Field(1000, gt=0, description="Maximum messages to keep in history")


class OrchestrationConfig(BaseModel):
    """Configuration for orchestration."""

    max_agents: int = Field(6, gt=0, le=10, description="Maximum number of agents")
    context_window: int = Field(20, gt=0, description="Number of messages for context")
    max_responses_per_turn: int = Field(3, gt=0, description="Max agent responses per turn")


class SystemConfig(BaseModel):
    """Complete system configuration."""

    agents: List[AgentConfig] = Field(..., description="List of agent configurations")
    channel: ChannelConfig = Field(default_factory=ChannelConfig, description="Channel configuration")
    orchestration: OrchestrationConfig = Field(
        default_factory=OrchestrationConfig,
        description="Orchestration configuration"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @validator("agents")
    def validate_agents(cls, v):
        """Validate agent configurations."""
        if len(v) == 0:
            raise ValueError("At least one agent must be configured")

        # Check for duplicate agent IDs
        agent_ids = [agent.agent_id for agent in v]
        if len(agent_ids) != len(set(agent_ids)):
            raise ValueError("Duplicate agent IDs found")

        # Check for duplicate callsigns
        callsigns = [agent.callsign for agent in v]
        if len(callsigns) != len(set(callsigns)):
            raise ValueError("Duplicate callsigns found")

        return v
