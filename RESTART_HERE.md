# 🔄 Quick Restart Guide

## After Terminal Restart

### 1. Navigate and Activate
```bash
cd /Users/kevinkelly/Documents/claude-projects/agentDemo/multi-agent-collab
# If using venv:
source venv/bin/activate
```

### 2. Verify Environment
```bash
# Check API key is set
echo $ANTHROPIC_API_KEY

# Should see: sk-ant-api03-...
# If not set:
export ANTHROPIC_API_KEY='your-key-here'
```

### 3. Quick Verification (30 seconds)
```bash
# Quick test to verify everything still works
python test_directed_communication.py
```

Expected output:
```
✅ PASS: Parsing
✅ PASS: Directed
✅ PASS: Types (or 4/5 - both fine)
```

---

## 🎮 Try the Interactive Demo

```bash
python demo_interactive.py
```

This is the **production-ready demo** - great for showing stakeholders!

---

## 📊 Current Status

**Completed:**
- ✅ Week 1: Autonomous tool use, memory, persistence
- ✅ Week 2: Directed communication + Visual dashboard
- ✅ Polish Phase 1: Production logging system

**In Progress:**
- 🚧 Polish Phase 2: Error handling & retry logic

See **[CHECKPOINT_POLISH.md](CHECKPOINT_POLISH.md)** for latest status.

---

## 🚀 Common Commands

```bash
# Run all tests
python test_autonomous_tool_use.py
python test_memory_and_persistence.py
python test_directed_communication.py

# Interactive demo
python demo_interactive.py

# Simple airport demo
python demo_agent_airport_search.py

# View all documentation
ls -la *.md
```

---

## 📁 Key Files

- `CHECKPOINT.md` - Full checkpoint summary
- `DEMO_GUIDE.md` - How to demonstrate the system
- `WEEK1_COMPLETE.md` - Week 1 feature summary
- `README.md` - Updated project overview

---

## 💡 Quick Tips

1. **Always run from project root:** `/multi-agent-collab/`
2. **API key required:** Set `ANTHROPIC_API_KEY` environment variable
3. **MCP warnings okay:** aerospace-mcp works, others have issues (non-blocking)
4. **Test first:** Run quick test before demo to warm up connections

---

Ready to continue! 🎯
