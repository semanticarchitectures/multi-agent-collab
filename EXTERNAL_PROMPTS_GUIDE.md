# External System Prompts Guide

## Overview

Instead of copying and pasting system prompts across multiple configuration files, you can now store them in separate files and reference them. This makes your prompts:

- **Reusable** across different squad configurations
- **Maintainable** - update once, affects all configs
- **Organized** - keep prompts separate from config structure
- **Shareable** - easily share prompts between team members

## Quick Start

### 1. Create a Prompt File

Create a YAML file in `configs/prompts/`:

```yaml
# configs/prompts/my_role.yaml
prompt: |
  You are a specialized agent with expertise in [domain].
  
  RESPONSIBILITIES:
  - Task 1
  - Task 2
  
  EXPERTISE AREAS:
  - Area 1
  - Area 2
  
  Respond when your expertise is needed.
```

### 2. Reference It in Your Config

Use the `system_prompt_file` key in your agent configuration:

```yaml
# configs/my-squad.yaml
agents:
  - agent_id: specialist
    callsign: "Alpha One"
    agent_type: base
    system_prompt_file: prompts/my_role.yaml
    speaking_criteria:
      - type: direct_address
      - type: keywords
        keywords: [keyword1, keyword2]
```

### 3. Run Your Configuration

```bash
python -m src.cli.main interactive --config configs/my-squad.yaml
```

## Available Prompt Templates

The following prompt templates are available in `configs/prompts/`:

### Aviation Roles
- **`captain.yaml`** - Pilot in Command, overall authority
- **`first_officer.yaml`** - Safety monitor and backup pilot
- **`flight_engineer.yaml`** - Systems monitoring and management
- **`navigator.yaml`** - Route planning and navigation

### Mission Roles
- **`mission_commander.yaml`** - Squad leader and coordinator
- **`intelligence_analyst.yaml`** - Intelligence gathering and analysis
- **`sensor_operator.yaml`** - Sensor systems operation
- **`pilot.yaml`** - Aircraft pilot operations

## Example Configurations

### Example 1: Large Aircraft Crew

```yaml
# configs/my-aircraft.yaml
agents:
  - agent_id: captain
    callsign: "Alpha Lead"
    agent_type: squad_leader
    system_prompt_file: prompts/captain.yaml
    
  - agent_id: first_officer
    callsign: "Alpha One"
    system_prompt_file: prompts/first_officer.yaml
    speaking_criteria:
      - type: direct_address
      - type: keywords
        keywords: [error, safety, concern]
```

Run it:
```bash
python -m src.cli.main interactive --config configs/my-aircraft.yaml
```

### Example 2: Reusing Prompts Across Configs

You can use the same prompt in multiple configurations:

```yaml
# configs/training-mission.yaml
agents:
  - agent_id: instructor
    callsign: "Instructor"
    agent_type: squad_leader
    system_prompt_file: prompts/captain.yaml  # Reuse captain prompt
```

```yaml
# configs/operational-mission.yaml
agents:
  - agent_id: mission_lead
    callsign: "Mission Lead"
    agent_type: squad_leader
    system_prompt_file: prompts/captain.yaml  # Same prompt, different context
```

## Creating Custom Prompts

### Step 1: Create the File

```bash
# Create a new prompt file
touch configs/prompts/my_custom_role.yaml
```

### Step 2: Define the Prompt

```yaml
# configs/prompts/my_custom_role.yaml
prompt: |
  You are [role description].
  
  RESPONSIBILITIES:
  - [List key responsibilities]
  
  EXPERTISE AREAS:
  - [List areas of expertise]
  
  COMMUNICATION STYLE:
  - [How this agent should communicate]
  
  SPEAKING TRIGGERS:
  - [When this agent should speak up]
  
  [Additional context and instructions]
```

### Step 3: Use It

```yaml
# configs/my-config.yaml
agents:
  - agent_id: custom
    callsign: "Custom One"
    system_prompt_file: prompts/my_custom_role.yaml
```

## Advanced Usage

### Plain Text Prompts

You can also use `.txt` files:

```
# configs/prompts/simple_role.txt
You are a simple agent.
Respond when addressed.
```

Reference it the same way:
```yaml
system_prompt_file: prompts/simple_role.txt
```

### Inline vs External

You can mix inline and external prompts:

```yaml
agents:
  # External prompt
  - agent_id: specialist1
    callsign: "Alpha One"
    system_prompt_file: prompts/pilot.yaml
    
  # Inline prompt
  - agent_id: specialist2
    callsign: "Alpha Two"
    system_prompt: |
      You are a unique agent with a one-off role.
      This prompt is only used here.
```

## Testing Your Configuration

Use the test script to verify your config loads correctly:

```bash
python test_config_loader.py
```

Or modify it to test your specific config:

```python
config = load_config("configs/my-config.yaml")
```

## Best Practices

1. **Use External Prompts for Reusable Roles**
   - If a role might be used in multiple configs, make it external
   
2. **Use Inline Prompts for One-Off Roles**
   - If a role is unique to one config, inline is fine
   
3. **Organize by Domain**
   - Group related prompts (aviation/, mission/, technical/)
   
4. **Version Your Prompts**
   - Use git to track changes to prompt files
   
5. **Document Your Prompts**
   - Add comments explaining the role and use cases

## Troubleshooting

### "Prompt file not found"

Make sure the path is correct relative to your config file:
```yaml
# If your config is in configs/
# And prompt is in configs/prompts/
system_prompt_file: prompts/my_role.yaml  # ✓ Correct

# Not this:
system_prompt_file: configs/prompts/my_role.yaml  # ✗ Wrong
```

### Prompt Not Loading

Check that your YAML file has the `prompt:` key:
```yaml
# ✓ Correct
prompt: |
  Your prompt here

# ✗ Wrong (missing prompt key)
Your prompt here
```

### Testing Individual Prompts

You can test loading a prompt file directly:

```python
from src.config.loader import ConfigLoader

loader = ConfigLoader()
prompt = loader._load_prompt_file("prompts/pilot.yaml", Path("configs"))
print(prompt)
```

## Examples in This Repository

- **`configs/U-28-with-prompts.yaml`** - U-28 squadron using external prompts
- **`configs/LargeAircraft-v2.yaml`** - Large aircraft crew using external prompts

Try them:
```bash
python -m src.cli.main interactive --config configs/LargeAircraft-v2.yaml
```

