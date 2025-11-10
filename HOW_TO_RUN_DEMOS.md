# How to Run the Multi-Agent Demos

Complete guide for running interactive and automated demos with full MCP tool access.

---

## Prerequisites

### 1. **Required**
- Python 3.9+
- Virtual environment activated
- Anthropic API key

### 2. **Optional (for aviation tools)**
- `uv` package manager
- aerospace-mcp server (in parent directory)

---

## Quick Start (Without MCP Tools)

The demos work without MCP tools - agents will still demonstrate communication and coordination:

```bash
# Automated demo (no interaction needed)
python demo_automated.py

# Interactive demo (requires user input)
python demo_interactive.py
```

---

## Full Setup (With Aviation Tools)

For the complete experience with real aviation data, follow these steps:

### Step 1: Check MCP Server Location

```bash
# Check if aerospace-mcp exists
ls -la ../aerospace-mcp

# Should show:
# drwxr-xr-x aerospace-mcp/
```

If not found, clone it:
```bash
cd ..
git clone https://github.com/chrishayuk/aerospace-mcp.git
cd multi-agent-collab
```

### Step 2: Install UV Package Manager

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

### Step 3: Install MCP Server Dependencies

```bash
cd ../aerospace-mcp
uv sync
cd ../multi-agent-collab
```

### Step 4: Verify MCP Connection

```bash
# This test doesn't need API key
python verify_mcp_connection.py
```

Expected output:
```
✅ aerospace-mcp server found
✅ uv command available
✅ MCP connection successful
✅ 34 aerospace tools discovered
✅ Tool execution test passed
```

### Step 5: Set API Key

```bash
export ANTHROPIC_API_KEY='your-key-here'
```

Or add to your shell profile:
```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export ANTHROPIC_API_KEY="your-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### Step 6: Run Demos

```bash
# Automated demo (recommended for first time)
python demo_automated.py

# Interactive demo (full experience)
python demo_interactive.py
```

---

## Demo Options

### Automated Demo

**Best for:** Testing, recordings, CI/CD, quick validation

```bash
# Default (2 second delays between turns)
python demo_automated.py

# Fast mode (no delays)
python demo_automated.py --fast

# Custom delay
python demo_automated.py --delay 5.0

# Skip metrics display
python demo_automated.py --no-metrics
```

**What it does:**
- Runs 6 pre-scripted turns automatically
- No user input required
- Shows agent responses
- Displays team memory
- Saves session to database
- Shows performance metrics

**Sample output:**
```
🚁 AUTOMATED MULTI-AGENT DEMO 🚁
Mode: Automated (no user input required)

────────────────────────────────────────────────────────────────
  Initializing Aviation Systems
────────────────────────────────────────────────────────────────
✅ Connected! 34 aviation tools available

────────────────────────────────────────────────────────────────
  Assembling Team
────────────────────────────────────────────────────────────────
👥 Team Roster:
   • RESCUE-LEAD - Mission Commander
   • ALPHA-ONE - Flight Planning
   • ALPHA-TWO - Navigation
   • ALPHA-THREE - Weather

────────────────────────────────────────────────────────────────
  Act 1 of 6
────────────────────────────────────────────────────────────────
💭 Turn 1: Mission activation and squad leader tasking
[COMMAND]: All stations, this is Mission Command...

[RESCUE-LEAD]: Roger, Mission Command. This is Rescue Lead...
⏱️  Response time: 2.34s
```

---

### Interactive Demo

**Best for:** Presentations, user evaluation, demonstrations

```bash
python demo_interactive.py
```

**What it does:**
- 3-act guided scenario
- User types commands to agents
- Squad leader can delegate
- Agents use real aviation tools
- View team memory at any time
- Save/resume sessions

**Interactive commands:**
```
# Directed communication
"Alpha One, search for airports near San Francisco, over."
"Alpha Two, calculate distance from KBOS to KJFK, over."
"Rescue Lead, coordinate the team, over."

# Broadcast
"All stations, provide status update, over."

# Special commands during menu
1 - Send a message
2 - View team memory
3 - Continue to next act
4 - Save session and exit
```

**Sample session:**
```
═══════════════════════════════════════════════════════════════
                🚁 MULTI-AGENT AVIATION DEMO 🚁
═══════════════════════════════════════════════════════════════

Scenario: Coast Guard Search and Rescue Mission Planning
You are the Mission Commander...

Press Enter to begin the mission...

═══════════════════════════════════════════════════════════════
                    Act 1: Initial Assessment
═══════════════════════════════════════════════════════════════

[COMMAND]: All stations, this is Mission Command, we have a SAR mission...

[RESCUE-LEAD]: Roger, Mission Command. Team is standing by...

💡 Try: 'Alpha One, search for airports near San Francisco...'

Options:
  1. Send a message to the team
  2. View team memory/context
  3. Continue to next act
  4. Save session and exit

Your choice (1-4): 1

📡 Your message: Alpha One, search for airports near San Francisco

[ALPHA-ONE]: Roger. Searching airports in San Francisco area...
              Located KSFO (San Francisco International), KOAK (Oakland)...
```

---

## Troubleshooting

### Issue: "Connection to aerospace-mcp timed out"

**Symptoms:**
```
🔧 Connecting to aerospace-mcp server...
❌ Connection to aerospace-mcp timed out
✅ Connected! 0 aviation tools available
```

**Solutions:**

1. **Check server location:**
   ```bash
   ls -la ../aerospace-mcp
   # If missing, clone it:
   cd .. && git clone https://github.com/chrishayuk/aerospace-mcp.git
   ```

2. **Verify uv is installed:**
   ```bash
   uv --version
   # If missing:
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Install MCP dependencies:**
   ```bash
   cd ../aerospace-mcp
   uv sync
   cd ../multi-agent-collab
   ```

4. **Test MCP manually:**
   ```bash
   cd ../aerospace-mcp
   uv run aerospace-mcp
   # Should start without errors
   ```

5. **Check Python MCP package:**
   ```bash
   pip list | grep mcp
   # If missing:
   pip install mcp
   ```

---

### Issue: "EOFError: EOF when reading a line"

**Symptoms:**
```
Press Enter to begin the mission...
EOFError: EOF when reading a line
```

**Cause:** Running interactive demo in non-interactive environment (background, CI/CD, etc.)

**Solution:** Use automated demo instead:
```bash
python demo_automated.py
```

---

### Issue: "ANTHROPIC_API_KEY environment variable not set"

**Symptoms:**
```
Error: ANTHROPIC_API_KEY environment variable not set
```

**Solution:**
```bash
# For current session
export ANTHROPIC_API_KEY='your-key-here'

# Or permanent (add to ~/.zshrc or ~/.bashrc)
echo 'export ANTHROPIC_API_KEY="your-key-here"' >> ~/.zshrc
source ~/.zshrc
```

---

### Issue: Agents not responding or slow responses

**Possible causes:**
1. **API rate limits** - Wait a minute and try again
2. **Network issues** - Check internet connection
3. **Complex queries** - Some tool calls take 10-30 seconds

**Check:**
```bash
# Test API key
python -c "import anthropic; client = anthropic.Anthropic(); print('API key valid')"
```

---

## Understanding Demo Behavior

### With MCP Tools (34 tools available)

Agents can:
- ✅ Search real airport database
- ✅ Calculate actual distances
- ✅ Get aircraft performance data
- ✅ Access atmospheric models
- ✅ Use orbital mechanics tools

Example response:
```
[ALPHA-ONE]: Roger. Searching airports in San Francisco area...
             Located KSFO (San Francisco Intl), lat 37.62, lon -122.38
             Located KOAK (Oakland Intl), lat 37.72, lon -122.22
             Both suitable for SAR operations, over.
```

### Without MCP Tools (0 tools available)

Agents still:
- ✅ Communicate using voice net protocol
- ✅ Respond to directed messages
- ✅ Squad leader delegates tasks
- ✅ Remember information in memory
- ✅ Follow aviation procedures

Example response:
```
[ALPHA-ONE]: Roger. Based on my knowledge, San Francisco International (KSFO)
             is the primary airport. Oakland (KOAK) is also available.
             Both are suitable for SAR operations, over.
```

**Note:** Without tools, responses are based on agent knowledge rather than live data.

---

## Advanced Usage

### Saving and Resuming Sessions

Sessions are automatically saved to `data/sessions.db`.

**Save during demo:**
```
Options:
  4. Save session and exit

Your choice: 4

✅ Mission data saved as: sar-mission-20251110-144530
```

**Export session:**
```bash
python -c "
import asyncio
from src.state.state_manager import StateManager

async def export():
    sm = StateManager()
    await sm.export_session('sar-mission-20251110-144530', 'mission.txt', 'txt')

asyncio.run(export())
"
```

**List saved sessions:**
```bash
python -c "
import asyncio
from src.state.state_manager import StateManager

async def list_sessions():
    sm = StateManager()
    await sm.initialize_db()
    sessions = await sm.list_sessions(limit=10)
    for s in sessions:
        print(f\"{s['session_id']}: {s['message_count']} messages, {s['agent_count']} agents\")

asyncio.run(list_sessions())
"
```

---

## Performance Expectations

### With MCP Tools
- **Turn response time:** 5-15 seconds
  - 2-5s for API call
  - 3-10s for tool execution
- **Memory usage:** ~200-300 MB
- **Database size:** ~1-2 MB per session

### Without MCP Tools
- **Turn response time:** 2-5 seconds
  - 2-5s for API call only
- **Memory usage:** ~100-150 MB
- **Database size:** ~0.5-1 MB per session

### Network Requirements
- **Minimum:** 1 Mbps download, 0.5 Mbps upload
- **Recommended:** 5 Mbps+ for smooth operation
- **Data usage:** ~1-2 MB per agent response

---

## Tips for Best Experience

### 1. **Start with Automated Demo**
- See the full flow without interaction
- Understand the communication patterns
- Verify everything works

### 2. **Use Clear Commands**
- Start with agent callsign
- Be specific about what you want
- End with "over" for realism

### 3. **Try Different Message Types**
```bash
# Directed (specific agent)
"Alpha One, [task]"

# Broadcast (all agents)
"All stations, [message]"

# Squad leader delegation
"Rescue Lead, coordinate [task]"
```

### 4. **View Memory Often**
- Choose option 2 to see what agents remember
- Helps understand agent context
- Shows information persistence

### 5. **Save Interesting Sessions**
- Save sessions you want to review later
- Export to text for documentation
- Share with team members

---

## What to Expect

### First Run
```
🚁 AUTOMATED MULTI-AGENT DEMO 🚁

Mode: Automated (no user input required)
Scenario: Coast Guard Search and Rescue Mission Planning

────────────────────────────────────────────────────────────────
  Initializing Aviation Systems
────────────────────────────────────────────────────────────────

🔧 Connecting to aerospace-mcp server...
✅ Connected! 34 aviation tools available

────────────────────────────────────────────────────────────────
  Assembling Team
────────────────────────────────────────────────────────────────

👥 Team Roster:
   • RESCUE-LEAD - Mission Commander
   • ALPHA-ONE - Flight Planning
   • ALPHA-TWO - Navigation
   • ALPHA-THREE - Weather

✅ Demo initialized successfully

════════════════════════════════════════════════════════════════
                SCENARIO: Search and Rescue Mission
════════════════════════════════════════════════════════════════

A distress call has been received from a vessel 150nm west of San Francisco.
The team must plan and coordinate the SAR operation.

[6 turns follow with agent responses...]

────────────────────────────────────────────────────────────────
  Demo Metrics
────────────────────────────────────────────────────────────────

Total Duration: 67.23s
Turns Executed: 6
Agent Responses: 14
Average per Turn: 11.21s

════════════════════════════════════════════════════════════════
                      🎉 DEMO COMPLETE 🎉
════════════════════════════════════════════════════════════════

Key Features Demonstrated:
  ✅ Multi-agent coordination
  ✅ Directed communication
  ✅ Broadcast messages
  ✅ Squad leader delegation
  ✅ Agent memory and context
  ✅ Session persistence
  ✅ Autonomous tool use (MCP integration)
```

---

## Getting Help

### If demos won't run:
1. Check prerequisites above
2. Run `python verify_mcp_connection.py`
3. Check error messages carefully
4. Review troubleshooting section

### For feature questions:
- See `DEMO_GUIDE.md` for overview
- See `README.md` for architecture
- See `docs/` for detailed documentation

### For improvements:
- See `DEMO_IMPROVEMENTS.md` for suggested enhancements
- Submit issues or PRs to the repository

---

## Next Steps

1. ✅ Run automated demo: `python demo_automated.py`
2. 🎮 Try interactive demo: `python demo_interactive.py`
3. 🔧 Review `DEMO_IMPROVEMENTS.md` for enhancement ideas
4. 📚 Read `docs/ARCHITECTURE.md` to understand the system
5. 🛠️ Customize agents and scenarios for your use case

---

**Status:** Ready to run! Both demos work with or without MCP tools.
