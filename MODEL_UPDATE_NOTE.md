# Model Name Update - January 2025

## Issue

The model name `claude-3-5-sonnet-20240620` is no longer valid and returns a 404 error:

```
Error code: 404 - {'type': 'error', 'error': {'type': 'not_found_error', 'message': 'model: claude-3-5-sonnet-20240620'}}
```

## Solution

All configuration files have been updated to use the current model name: **`claude-sonnet-4-5-20250929`**

## What Changed

### Updated Files

1. **`configs/LargeAircraft-v2.yaml`** - All 4 agents updated to new model
2. **`configs/U-28-with-prompts.yaml`** - Squad leader updated to new model
3. **`src/config/schema.py`** - Default model updated
4. **`src/agents/base_agent.py`** - Default model updated

### Current Valid Model Names (as of January 2025)

According to [Anthropic's documentation](https://docs.anthropic.com/en/docs/about-claude/models):

| Model | API ID | Description |
|-------|--------|-------------|
| **Claude Sonnet 4.5** | `claude-sonnet-4-5-20250929` | Smartest model for complex agents and coding |
| **Claude Haiku 4.5** | `claude-haiku-4-5-20251001` | Fastest model with near-frontier intelligence |
| **Claude Opus 4.1** | `claude-opus-4-1-20250805` | Exceptional model for specialized reasoning |

### Recommended Model

For most use cases, use **`claude-sonnet-4-5-20250929`** which offers:
- Best balance of intelligence, speed, and cost
- Exceptional performance in coding and agentic tasks
- 200K context window (1M with beta header)
- Extended thinking support

## Migration Guide

If you have custom configuration files using the old model name, update them:

### Before
```yaml
agents:
  - agent_id: my_agent
    model: claude-3-5-sonnet-20240620  # ❌ Old, deprecated
```

### After
```yaml
agents:
  - agent_id: my_agent
    model: claude-sonnet-4-5-20250929  # ✅ Current, valid
```

## Testing

After updating, test your configuration:

```bash
# Test config loading
python test_config_loader.py

# Or run interactive mode
python -m src.cli.main interactive --config configs/LargeAircraft-v2.yaml
```

## Legacy Models Still Available

These older models still work but are not recommended:

- `claude-sonnet-4-20250514` (Claude Sonnet 4)
- `claude-3-7-sonnet-20250219` (Claude Sonnet 3.7)
- `claude-opus-4-20250514` (Claude Opus 4)
- `claude-3-5-haiku-20241022` (Claude Haiku 3.5)
- `claude-3-haiku-20240307` (Claude Haiku 3)

## Pricing

Claude Sonnet 4.5 pricing:
- **Input**: $3 / million tokens
- **Output**: $15 / million tokens

See [Anthropic's pricing page](https://www.anthropic.com/pricing) for complete details.

## References

- [Anthropic Models Documentation](https://docs.anthropic.com/en/docs/about-claude/models)
- [Claude Sonnet 4.5 Announcement](https://www.anthropic.com/claude/sonnet)
- [API Reference](https://docs.anthropic.com/en/api/messages)

