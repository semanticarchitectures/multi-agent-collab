# External System Prompts - Implementation Summary

## What Was Added

A new configuration loading system that allows you to store system prompts in separate files and reference them across multiple agent configurations.

## New Files Created

### Core Implementation
- **`src/config/loader.py`** - Configuration loader with external prompt support
- **`src/config/__init__.py`** - Updated to export loader functions

### Prompt Templates (configs/prompts/)
- **`captain.yaml`** - Pilot in Command role
- **`first_officer.yaml`** - First Officer/safety monitor role
- **`flight_engineer.yaml`** - Systems engineer role
- **`navigator.yaml`** - Navigation specialist role
- **`mission_commander.yaml`** - Mission commander/squad leader
- **`intelligence_analyst.yaml`** - Intelligence analyst role
- **`sensor_operator.yaml`** - Sensor systems operator
- **`pilot.yaml`** - General pilot role

### Example Configurations
- **`configs/U-28-with-prompts.yaml`** - U-28 squadron using external prompts
- **`configs/LargeAircraft-v2.yaml`** - Large aircraft crew configuration

### Documentation
- **`configs/prompts/README.md`** - Guide for the prompts directory
- **`EXTERNAL_PROMPTS_GUIDE.md`** - Complete usage guide
- **`test_config_loader.py`** - Test script for config loader

## Modified Files
- **`src/cli/commands.py`** - Updated to use config loader when --config is provided

## How to Use

### 1. Basic Usage

Instead of this (inline prompt):
```yaml
agents:
  - agent_id: pilot
    callsign: "Alpha One"
    system_prompt: |
      You are the pilot...
      [100 lines of prompt]
```

Do this (external prompt):
```yaml
agents:
  - agent_id: pilot
    callsign: "Alpha One"
    system_prompt_file: prompts/pilot.yaml
```

### 2. Run a Configuration

```bash
# Run with external prompts
python -m src.cli.main interactive --config configs/LargeAircraft-v2.yaml

# Or the U-28 example
python -m src.cli.main interactive --config configs/U-28-with-prompts.yaml
```

### 3. Create Your Own Prompts

```yaml
# configs/prompts/my_role.yaml
prompt: |
  You are a specialized agent...
  
  RESPONSIBILITIES:
  - Task 1
  - Task 2
```

Then reference it:
```yaml
# configs/my-squad.yaml
agents:
  - agent_id: specialist
    system_prompt_file: prompts/my_role.yaml
```

## Benefits

1. **Reusability** - Use the same prompt in multiple configurations
2. **Maintainability** - Update a prompt once, affects all configs using it
3. **Organization** - Separate prompts from configuration structure
4. **Version Control** - Track prompt changes independently
5. **Sharing** - Easily share prompts between team members

## Examples

### Example 1: Reuse Across Configs

```yaml
# configs/training.yaml
agents:
  - agent_id: instructor
    system_prompt_file: prompts/captain.yaml  # Reuse

# configs/mission.yaml
agents:
  - agent_id: commander
    system_prompt_file: prompts/captain.yaml  # Same prompt
```

### Example 2: Mix Inline and External

```yaml
agents:
  # External (reusable)
  - agent_id: pilot
    system_prompt_file: prompts/pilot.yaml
    
  # Inline (one-off)
  - agent_id: special
    system_prompt: |
      You are a unique agent for this specific mission.
```

## Testing

```bash
# Test the config loader
python test_config_loader.py

# Test a specific config
python -c "from src.config import load_config; config = load_config('configs/LargeAircraft-v2.yaml'); print(f'Loaded {len(config.agents)} agents')"
```

## Path Resolution

Paths are resolved in this order:
1. Relative to the config file's directory
2. Relative to the project root

So from `configs/my-squad.yaml`, you can use:
- `prompts/pilot.yaml` (relative to configs/)
- `configs/prompts/pilot.yaml` (from project root)

## File Formats Supported

### YAML (Recommended)
```yaml
prompt: |
  Your prompt content here
```

### Plain Text
```
Your prompt content here
```

## Next Steps

1. **Create your own prompts** in `configs/prompts/`
2. **Update existing configs** to use external prompts
3. **Share prompts** with your team
4. **Version control** your prompt library

## Quick Reference

```yaml
# Reference external prompt
system_prompt_file: prompts/my_role.yaml

# Or use inline (old way still works)
system_prompt: |
  Inline prompt content
```

## Available Prompt Templates

Run this to see all available prompts:
```bash
ls -1 configs/prompts/*.yaml
```

Current templates:
- Aviation: captain, first_officer, flight_engineer, navigator
- Mission: mission_commander, intelligence_analyst, sensor_operator, pilot

## Documentation

- **Full Guide**: `EXTERNAL_PROMPTS_GUIDE.md`
- **Prompts README**: `configs/prompts/README.md`
- **Example Configs**: `configs/U-28-with-prompts.yaml`, `configs/LargeAircraft-v2.yaml`

