#!/usr/bin/env python3
"""Quick test script for the config loader with external prompts."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.config import load_config


def main():
    """Test loading a config with external prompt files."""
    print("=" * 80)
    print("Testing Config Loader with External Prompts")
    print("=" * 80)
    
    config_file = "configs/U-28-with-prompts.yaml"
    
    print(f"\nLoading configuration: {config_file}")
    
    try:
        config = load_config(config_file)
        
        print(f"\n✓ Configuration loaded successfully!")
        print(f"\nMetadata:")
        print(f"  Name: {config.metadata.get('name', 'N/A')}")
        print(f"  Description: {config.metadata.get('description', 'N/A')}")
        
        print(f"\nAgents ({len(config.agents)}):")
        for agent in config.agents:
            print(f"\n  • {agent.callsign} ({agent.agent_id})")
            print(f"    Type: {agent.agent_type}")
            print(f"    Model: {agent.model}")
            
            if agent.system_prompt:
                # Show first 100 chars of prompt
                prompt_preview = agent.system_prompt[:100].replace('\n', ' ')
                print(f"    Prompt: {prompt_preview}...")
            else:
                print(f"    Prompt: [None - will use default]")
                
            if agent.speaking_criteria:
                print(f"    Speaking Criteria: {len(agent.speaking_criteria)} rules")
        
        print(f"\nChannel Settings:")
        print(f"  Max History: {config.channel.max_history}")
        
        print(f"\nOrchestration Settings:")
        print(f"  Max Agents: {config.orchestration.max_agents}")
        print(f"  Context Window: {config.orchestration.context_window}")
        print(f"  Max Responses/Turn: {config.orchestration.max_responses_per_turn}")
        
        print("\n" + "=" * 80)
        print("✓ All tests passed!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n✗ Error loading configuration: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

