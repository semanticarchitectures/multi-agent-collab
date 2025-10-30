"""Configuration loader with support for external prompt files."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from .schema import SystemConfig


class ConfigLoader:
    """Load and process configuration files with external prompt support.
    
    Supports referencing external prompt files using the syntax:
    system_prompt: !include prompts/pilot.yaml
    
    Or using a special key:
    system_prompt_file: prompts/pilot.yaml
    """
    
    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize the config loader.
        
        Args:
            base_dir: Base directory for resolving relative paths (defaults to project root)
        """
        if base_dir is None:
            # Default to project root (3 levels up from this file)
            base_dir = Path(__file__).parent.parent.parent
        self.base_dir = Path(base_dir)
        
    def load_config(self, config_path: str) -> SystemConfig:
        """Load configuration from a YAML file.
        
        Args:
            config_path: Path to configuration file (relative to base_dir or absolute)
            
        Returns:
            Validated SystemConfig object
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        config_file = Path(config_path)
        if not config_file.is_absolute():
            config_file = self.base_dir / config_file
            
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
            
        # Load raw YAML
        with open(config_file, 'r') as f:
            raw_config = yaml.safe_load(f)
            
        # Process external prompt references
        if 'agents' in raw_config:
            for agent_config in raw_config['agents']:
                self._process_agent_prompts(agent_config, config_file.parent)
                
        # Validate and return
        return SystemConfig(**raw_config)
        
    def _process_agent_prompts(self, agent_config: Dict[str, Any], config_dir: Path):
        """Process system prompt references in agent configuration.
        
        Supports two formats:
        1. system_prompt_file: "prompts/pilot.yaml"
        2. system_prompt: "!include prompts/pilot.yaml"
        
        Args:
            agent_config: Agent configuration dictionary
            config_dir: Directory containing the config file (for relative paths)
        """
        # Check for system_prompt_file key
        if 'system_prompt_file' in agent_config:
            prompt_file = agent_config.pop('system_prompt_file')
            agent_config['system_prompt'] = self._load_prompt_file(prompt_file, config_dir)
            return
            
        # Check for !include directive in system_prompt
        if 'system_prompt' in agent_config:
            prompt = agent_config['system_prompt']
            if isinstance(prompt, str) and prompt.strip().startswith('!include '):
                prompt_file = prompt.replace('!include ', '').strip()
                agent_config['system_prompt'] = self._load_prompt_file(prompt_file, config_dir)
                
    def _load_prompt_file(self, prompt_path: str, config_dir: Path) -> str:
        """Load a system prompt from an external file.
        
        Args:
            prompt_path: Path to prompt file (relative to config_dir or absolute)
            config_dir: Directory to resolve relative paths from
            
        Returns:
            Prompt content as string
            
        Raises:
            FileNotFoundError: If prompt file doesn't exist
        """
        prompt_file = Path(prompt_path)
        
        # Try relative to config directory first
        if not prompt_file.is_absolute():
            prompt_file = config_dir / prompt_file
            
        # If still not found, try relative to base_dir
        if not prompt_file.exists():
            prompt_file = self.base_dir / prompt_path
            
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
            
        # Load the prompt file
        with open(prompt_file, 'r') as f:
            content = f.read()
            
        # If it's a YAML file, extract the 'prompt' or 'system_prompt' key
        if prompt_file.suffix in ['.yaml', '.yml']:
            try:
                prompt_data = yaml.safe_load(content)
                if isinstance(prompt_data, dict):
                    # Try common keys
                    for key in ['prompt', 'system_prompt', 'content']:
                        if key in prompt_data:
                            return prompt_data[key]
                    # If no known key, return the whole thing as YAML string
                    return content
                else:
                    # If it's just a string in YAML, return it
                    return str(prompt_data)
            except yaml.YAMLError:
                # If YAML parsing fails, return raw content
                return content
        else:
            # For .txt or other files, return raw content
            return content.strip()


def load_config(config_path: str, base_dir: Optional[Path] = None) -> SystemConfig:
    """Convenience function to load a configuration file.
    
    Args:
        config_path: Path to configuration file
        base_dir: Base directory for resolving paths (defaults to project root)
        
    Returns:
        Validated SystemConfig object
    """
    loader = ConfigLoader(base_dir=base_dir)
    return loader.load_config(config_path)

