# Quick Start: External System Prompts

## TL;DR

Store system prompts in separate files and reuse them across configurations.

## 3-Step Setup

### 1. Create a Prompt File

```bash
# Create: configs/prompts/my_role.yaml
```

```yaml
prompt: |
  You are a specialized agent.
  Respond when your expertise is needed.
```

### 2. Reference It

```yaml
# In your config: configs/my-squad.yaml
agents:
  - agent_id: specialist
    callsign: "Alpha One"
    system_prompt_file: prompts/my_role.yaml
```

### 3. Run It

```bash
python -m src.cli.main interactive --config configs/my-squad.yaml
```

## Try the Examples

```bash
# Large aircraft crew (4 agents)
python -m src.cli.main interactive --config configs/LargeAircraft-v2.yaml

# U-28 squadron (4 agents)
python -m src.cli.main interactive --config configs/U-28-with-prompts.yaml
```

## Available Prompts

```
configs/prompts/
├── captain.yaml              # Pilot in Command
├── first_officer.yaml        # Safety monitor
├── flight_engineer.yaml      # Systems engineer
├── navigator.yaml            # Navigation specialist
├── mission_commander.yaml    # Squad leader
├── intelligence_analyst.yaml # Intel analyst
├── sensor_operator.yaml      # Sensor operator
└── pilot.yaml               # General pilot
```

## Syntax

```yaml
# Method 1: system_prompt_file (recommended)
system_prompt_file: prompts/my_role.yaml

# Method 2: inline (old way, still works)
system_prompt: |
  Your prompt here
```

## Full Example

```yaml
# configs/my-aircraft.yaml
agents:
  - agent_id: captain
    callsign: "Alpha Lead"
    agent_type: squad_leader
    system_prompt_file: prompts/captain.yaml
    model: claude-3-5-sonnet-20240620
    
  - agent_id: first_officer
    callsign: "Alpha One"
    agent_type: base
    system_prompt_file: prompts/first_officer.yaml
    speaking_criteria:
      - type: direct_address
      - type: keywords
        keywords: [error, safety, concern]

channel:
  max_history: 2000

orchestration:
  max_agents: 6
  context_window: 25
  max_responses_per_turn: 3
```

Run it:
```bash
python -m src.cli.main interactive --config configs/my-aircraft.yaml
```

## Benefits

✓ Reuse prompts across configs  
✓ Update once, affects all  
✓ Better organization  
✓ Easy to share  
✓ Version control friendly  

## More Info

- **Full Guide**: `EXTERNAL_PROMPTS_GUIDE.md`
- **Summary**: `SUMMARY_EXTERNAL_PROMPTS.md`
- **Prompts README**: `configs/prompts/README.md`

