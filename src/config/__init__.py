"""Configuration module for multi-agent collaboration system."""

from .schema import (
    AgentConfig,
    ChannelConfig,
    OrchestrationConfig,
    SystemConfig,
    SpeakingCriteriaConfig
)
from .loader import ConfigLoader, load_config

__all__ = [
    'AgentConfig',
    'ChannelConfig',
    'OrchestrationConfig',
    'SystemConfig',
    'SpeakingCriteriaConfig',
    'ConfigLoader',
    'load_config'
]
