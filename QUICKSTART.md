# Quick Start Guide

Get up and running with the multi-agent collaboration system in 5 minutes!

## Prerequisites

- Python 3.11 or higher
- Anthropic API key ([get one here](https://console.anthropic.com/))

## Installation

1. **Install dependencies:**
   ```bash
   cd multi-agent-collab
   pip install -r requirements.txt
   ```

2. **Set your API key:**
   ```bash
   export ANTHROPIC_API_KEY='your-api-key-here'
   ```

## Run Your First Demo

```bash
python demo.py
```

This will show you 2 agents (a squad leader and a data specialist) communicating using voice net protocol through several scenarios.

## Try Interactive Mode

```bash
python -m src.cli.main interactive
```

Now you can chat with the agents! Try these messages:

- `"What's our status?"` - Squad leader responds
- `"Alpha One, analyze this data"` - Data specialist responds
- `"I need help with a problem"` - Multiple agents may respond

Type `quit` to exit.

## What Just Happened?

You created a multi-agent system where:

1. **Alpha Lead** (Squad Leader) - Coordinates the team
2. **Alpha One** (Data Specialist) - Handles analysis tasks

They communicate using **voice net protocol** (like pilot-ATC radio):
- `"Alpha One, this is Alpha Lead, requesting status, over."`

Each agent decides when to speak based on **speaking criteria**:
- Being directly addressed
- Keyword mentions (e.g., "analyze", "data")
- Questions requiring their expertise

## Next Steps

### Customize Your Squad

Edit `configs/default.yaml` to:
- Change agent callsigns
- Modify system prompts
- Add more agents (up to 6)
- Adjust speaking criteria keywords

Then run:
```bash
python -m src.cli.main interactive --config configs/default.yaml
```

### See More Examples

Check out `configs/demo.yaml` for a 4-agent squad with specialized roles:
- Intelligence Analyst
- Technical Engineer
- Logistics Coordinator
- Squad Leader

### Explore the Code

Key files to understand:
- `src/agents/base_agent.py` - Agent base class
- `src/agents/squad_leader.py` - Squad leader specialization
- `src/channel/voice_net_protocol.py` - Protocol parser
- `src/orchestration/orchestrator.py` - Coordination logic

### Run Tests

```bash
pytest
```

### Read the Docs

- `docs/ARCHITECTURE.md` - System design and components
- `docs/USAGE.md` - Detailed usage guide with examples
- `README.md` - Project overview

## Common Commands

| Command | Description |
|---------|-------------|
| `python demo.py` | Run automated demo |
| `python -m src.cli.main demo` | CLI demo command |
| `python -m src.cli.main interactive` | Start chat session |
| `python -m src.cli.main status` | Show system info |
| `pytest` | Run tests |

## Voice Net Protocol Cheat Sheet

| Format | Example |
|--------|---------|
| Direct address | `Alpha One, analyze this data` |
| Formal protocol | `Alpha Two, this is Alpha Lead, status update, over.` |
| Broadcast | `All units, new mission incoming` |
| Acknowledgment | `Roger, understood.` |
| Confirmation | `Copy, proceeding with task.` |

## Troubleshooting

**"ANTHROPIC_API_KEY not set"**
```bash
export ANTHROPIC_API_KEY='your-key'
```

**Import errors**
- Make sure you're in the `multi-agent-collab` directory
- Check that dependencies are installed: `pip install -r requirements.txt`

**Agents not responding**
- Check that keywords match your message
- Try directly addressing an agent by callsign
- Verify the agent's speaking criteria in config

## What's Next?

**Phase 2 Coming Soon:**
- MCP tool integration for real capabilities
- State persistence to save/restore sessions
- More agent types and behaviors

**Want to Contribute?**
- Add custom speaking criteria
- Create new agent specializations
- Build configuration templates
- Write additional tests

## Need Help?

- Check `docs/USAGE.md` for detailed examples
- Review example configs in `configs/`
- Look at test files in `tests/` for code examples

---

**You're all set! Start collaborating with your AI squad!** 🚀
