# Reusable System Prompts

This directory contains reusable system prompts that can be referenced across multiple agent configurations.

## Usage

Instead of copying and pasting system prompts in your configuration files, you can reference external prompt files:

### Method 1: Using `system_prompt_file` key

```yaml
agents:
  - agent_id: pilot
    callsign: "Hawk Three"
    agent_type: base
    system_prompt_file: prompts/pilot.yaml
    speaking_criteria:
      - type: direct_address
      - type: keywords
        keywords: [flight, navigate, route]
```

### Method 2: Using `!include` directive

```yaml
agents:
  - agent_id: pilot
    callsign: "Hawk Three"
    agent_type: base
    system_prompt: !include prompts/pilot.yaml
    speaking_criteria:
      - type: direct_address
```

## Prompt File Formats

### YAML Format (Recommended)

Create a `.yaml` file with a `prompt` key:

```yaml
prompt: |
  You are the pilot of the aircraft.
  You handle all aspects of flying.
  
  RESPONSIBILITIES:
  - Flight path planning
  - Aircraft control
  - Weather assessment
  
  Respond when flying expertise is needed.
```

### Plain Text Format

Create a `.txt` file with the prompt content:

```
You are the pilot of the aircraft.
You handle all aspects of flying.

RESPONSIBILITIES:
- Flight path planning
- Aircraft control
- Weather assessment

Respond when flying expertise is needed.
```

## Available Prompts

- **`pilot.yaml`** - Aircraft pilot role
- **`sensor_operator.yaml`** - Sensor systems operator
- **`mission_commander.yaml`** - Mission commander/squad leader
- **`intelligence_analyst.yaml`** - Intelligence analyst

## Creating New Prompts

1. Create a new `.yaml` file in this directory
2. Use the `prompt:` key with multiline content (`|`)
3. Reference it in your configuration files

Example:

```yaml
# configs/prompts/navigator.yaml
prompt: |
  You are the navigator for the aircraft.
  You specialize in route planning and navigation.
  
  RESPONSIBILITIES:
  - Route planning and optimization
  - Navigation system operation
  - Weather analysis for routing
  - Fuel efficiency calculations
  
  Respond when navigation expertise is needed.
```

Then use it:

```yaml
# configs/my-squad.yaml
agents:
  - agent_id: nav
    callsign: "Alpha Four"
    system_prompt_file: prompts/navigator.yaml
```

## Benefits

- **Reusability**: Use the same prompt across multiple configurations
- **Maintainability**: Update a prompt once, affects all configs using it
- **Organization**: Keep prompts separate from configuration structure
- **Version Control**: Track prompt changes independently
- **Sharing**: Easily share prompts between team members

## Path Resolution

Paths are resolved in this order:
1. Relative to the configuration file's directory
2. Relative to the project root

So you can use:
- `prompts/pilot.yaml` (relative to config file)
- `configs/prompts/pilot.yaml` (from project root)

