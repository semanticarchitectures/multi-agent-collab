# Usage Guide

## Installation

1. Clone the repository and navigate to the project directory:
```bash
cd multi-agent-collab
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set your Anthropic API key:
```bash
export ANTHROPIC_API_KEY='your-key-here'
```

## Quick Start

### Run the Demo

The demo shows 2 agents (squad leader + specialist) communicating:

```bash
python demo.py
```

Or use the CLI:
```bash
python -m src.cli.main demo
```

### Interactive Mode

Start an interactive session where you can chat with the agents:

```bash
python -m src.cli.main interactive
```

Options:
- `--agents N`: Number of agents to create (default: 2)
- `--config PATH`: Load configuration from YAML file

Example with config:
```bash
python -m src.cli.main interactive --config configs/demo.yaml
```

### Check Status

View system information:
```bash
python -m src.cli.main status
```

## Using Voice Net Protocol

When communicating with agents, you can use voice net protocol format:

**Direct Address:**
```
Alpha One, analyze this data pattern.
```

**Formal Protocol:**
```
Alpha Two, this is User, requesting status update, over.
```

**Broadcast:**
```
All units, prepare for new mission.
```

Agents will respond using proper protocol:
```
User, this is Alpha Lead, roger, standing by, over.
```

## Configuration

### Create a Custom Configuration

Create a YAML file (e.g., `my-squad.yaml`):

```yaml
agents:
  - agent_id: leader
    callsign: "Hawk Lead"
    agent_type: squad_leader

  - agent_id: analyst
    callsign: "Hawk One"
    agent_type: base
    system_prompt: |
      You are a data analyst specializing in pattern recognition.
    speaking_criteria:
      - type: direct_address
      - type: keywords
        keywords: [analyze, data, pattern]

channel:
  max_history: 1000

orchestration:
  max_agents: 6
  context_window: 20
  max_responses_per_turn: 3
```

Use it:
```bash
python -m src.cli.main interactive --config my-squad.yaml
```

## Python API

### Basic Usage

```python
from src.agents.squad_leader import SquadLeaderAgent
from src.agents.base_agent import BaseAgent
from src.agents.speaking_criteria import KeywordCriteria
from src.channel.shared_channel import SharedChannel
from src.orchestration.orchestrator import Orchestrator

# Create channel and orchestrator
channel = SharedChannel()
orchestrator = Orchestrator(channel=channel)

# Create squad leader
leader = SquadLeaderAgent(
    agent_id="leader",
    callsign="Alpha Lead"
)
orchestrator.add_agent(leader)

# Create specialist
specialist = BaseAgent(
    agent_id="specialist",
    callsign="Alpha One",
    system_prompt="You are a data specialist.",
    speaking_criteria=KeywordCriteria(["data", "analyze"])
)
orchestrator.add_agent(specialist)

# Start session
orchestrator.start()

# Send user message and process responses
orchestrator.run_turn(user_message="What's our status?")

# Get conversation history
print(orchestrator.get_channel_history())

# Stop session
orchestrator.stop()
```

### Custom Speaking Criteria

```python
from src.agents.speaking_criteria import (
    CompositeCriteria,
    DirectAddressCriteria,
    KeywordCriteria,
    QuestionCriteria
)

# Combine multiple criteria
criteria = CompositeCriteria([
    DirectAddressCriteria(),
    KeywordCriteria(["urgent", "critical"]),
    QuestionCriteria()
])

agent = BaseAgent(
    agent_id="agent1",
    callsign="Alpha One",
    system_prompt="...",
    speaking_criteria=criteria
)
```

### Access Messages

```python
# Get recent messages
recent = channel.get_recent_messages(count=10)

# Get messages for specific agent
messages = channel.get_messages_for_agent(
    agent_callsign="Alpha One",
    count=10
)

# Get context window
context = channel.get_context_window(
    agent_callsign="Alpha One",
    window_size=20
)
```

## Running Tests

Run the full test suite:
```bash
pytest
```

With coverage:
```bash
pytest --cov=src --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_message.py
```

## Tips and Best Practices

1. **Callsign Naming**: Use clear, military-style callsigns (e.g., "Alpha Lead", "Hawk One")

2. **System Prompts**: Be specific about agent roles and expertise areas

3. **Speaking Criteria**: Combine criteria for more natural agent responses

4. **Context Window**: Larger windows provide more context but increase API costs

5. **Max Responses**: Limit simultaneous responses to avoid chaos (default: 3)

6. **Squad Leader**: Always include one squad leader for coordination

## Troubleshooting

**Agents not responding:**
- Check speaking criteria configuration
- Verify agent callsigns match addressing
- Check recent messages to ensure agent should respond

**API errors:**
- Verify ANTHROPIC_API_KEY is set
- Check API rate limits
- Ensure model name is correct

**Import errors:**
- Make sure you're running from project root
- Check Python path includes src directory
- Verify all dependencies are installed

## Examples

See the `configs/` directory for example configurations:
- `default.yaml`: Basic 2-agent setup
- `demo.yaml`: 4-agent specialized squad

See `demo.py` for a complete working example with multiple scenarios.
