# Before & After: External System Prompts

## The Problem (Before)

You had to copy and paste the same system prompts across multiple configuration files:

### configs/training-mission.yaml
```yaml
agents:
  - agent_id: instructor
    callsign: "Instructor Lead"
    system_prompt: |
      You are the Captain and Pilot in Command of the aircraft.
      You have ultimate authority and responsibility for the safe operation of the flight.
      
      RESPONSIBILITIES:
      - Overall command and decision-making authority
      - Flight safety and regulatory compliance
      - Crew coordination and resource management
      [... 50 more lines ...]
```

### configs/operational-mission.yaml
```yaml
agents:
  - agent_id: mission_commander
    callsign: "Mission Lead"
    system_prompt: |
      You are the Captain and Pilot in Command of the aircraft.
      You have ultimate authority and responsibility for the safe operation of the flight.
      
      RESPONSIBILITIES:
      - Overall command and decision-making authority
      - Flight safety and regulatory compliance
      - Crew coordination and resource management
      [... 50 more lines ...]  # SAME CONTENT, DUPLICATED!
```

### configs/emergency-drill.yaml
```yaml
agents:
  - agent_id: drill_leader
    callsign: "Drill Lead"
    system_prompt: |
      You are the Captain and Pilot in Command of the aircraft.
      You have ultimate authority and responsibility for the safe operation of the flight.
      
      RESPONSIBILITIES:
      - Overall command and decision-making authority
      - Flight safety and regulatory compliance
      - Crew coordination and resource management
      [... 50 more lines ...]  # DUPLICATED AGAIN!
```

**Problems:**
- ❌ Duplicated content across files
- ❌ Hard to maintain (update in 3 places)
- ❌ Easy to make mistakes
- ❌ Configs become very long
- ❌ Hard to see the structure

---

## The Solution (After)

### Step 1: Create the Prompt Once

```yaml
# configs/prompts/captain.yaml
prompt: |
  You are the Captain and Pilot in Command of the aircraft.
  You have ultimate authority and responsibility for the safe operation of the flight.
  
  RESPONSIBILITIES:
  - Overall command and decision-making authority
  - Flight safety and regulatory compliance
  - Crew coordination and resource management
  [... 50 more lines ...]
```

### Step 2: Reference It Everywhere

```yaml
# configs/training-mission.yaml
agents:
  - agent_id: instructor
    callsign: "Instructor Lead"
    system_prompt_file: prompts/captain.yaml  # ✓ Reference
```

```yaml
# configs/operational-mission.yaml
agents:
  - agent_id: mission_commander
    callsign: "Mission Lead"
    system_prompt_file: prompts/captain.yaml  # ✓ Same reference
```

```yaml
# configs/emergency-drill.yaml
agents:
  - agent_id: drill_leader
    callsign: "Drill Lead"
    system_prompt_file: prompts/captain.yaml  # ✓ Same reference
```

**Benefits:**
- ✅ Single source of truth
- ✅ Update once, affects all configs
- ✅ Configs are clean and readable
- ✅ Easy to maintain
- ✅ No duplication

---

## Real Example: Large Aircraft Configuration

### Before (LargeAircraft.yaml)

```yaml
agents:
  - id: "CAPTAIN"
    callsign: "Alpha Lead"
    system_prompt: |
      [Use Captain prompt from above]  # ← Placeholder, not actual content!
    
  - id: "FIRST-OFFICER"
    callsign: "Alpha One"
    system_prompt: |
      [Use First Officer prompt from above]  # ← Placeholder!
    
  - id: "FLIGHT-ENGINEER"
    callsign: "Alpha Two"
    system_prompt: |
      [Use Flight Engineer prompt from above]  # ← Placeholder!
    
  - id: "NAVIGATOR"
    callsign: "Alpha Three"
    system_prompt: |
      [Use Navigator prompt from above]  # ← Placeholder!
```

### After (LargeAircraft-v2.yaml)

```yaml
agents:
  - agent_id: captain
    callsign: "Alpha Lead"
    agent_type: squad_leader
    system_prompt_file: prompts/captain.yaml  # ✓ Actual content loaded
    
  - agent_id: first_officer
    callsign: "Alpha One"
    system_prompt_file: prompts/first_officer.yaml  # ✓ Actual content loaded
    
  - agent_id: flight_engineer
    callsign: "Alpha Two"
    system_prompt_file: prompts/flight_engineer.yaml  # ✓ Actual content loaded
    
  - agent_id: navigator
    callsign: "Alpha Three"
    system_prompt_file: prompts/navigator.yaml  # ✓ Actual content loaded
```

**Run it:**
```bash
python -m src.cli.main interactive --config configs/LargeAircraft-v2.yaml
```

---

## Comparison Table

| Aspect | Before (Inline) | After (External) |
|--------|----------------|------------------|
| **Reusability** | Copy & paste | Reference once |
| **Maintenance** | Update in N places | Update in 1 place |
| **Config Size** | 100+ lines per agent | 1 line per agent |
| **Readability** | Hard to see structure | Clear structure |
| **Errors** | Easy to have inconsistencies | Single source of truth |
| **Sharing** | Share entire config | Share prompt library |
| **Version Control** | Large diffs | Small, focused diffs |

---

## Migration Guide

### Step 1: Identify Reusable Prompts

Look for prompts that are:
- Used in multiple configs
- Represent standard roles
- Likely to be updated together

### Step 2: Extract to Files

```bash
# Create the prompt file
cat > configs/prompts/my_role.yaml << 'EOF'
prompt: |
  [Your prompt content here]
EOF
```

### Step 3: Update Configs

Replace:
```yaml
system_prompt: |
  [Long prompt content]
```

With:
```yaml
system_prompt_file: prompts/my_role.yaml
```

### Step 4: Test

```bash
python test_config_loader.py
# or
python -m src.cli.main interactive --config configs/your-config.yaml
```

---

## When to Use Each Approach

### Use External Prompts When:
- ✅ Prompt is used in multiple configs
- ✅ Prompt represents a standard role
- ✅ Prompt is long (>20 lines)
- ✅ Prompt needs to be shared with team
- ✅ Prompt will be updated frequently

### Use Inline Prompts When:
- ✅ Prompt is unique to one config
- ✅ Prompt is very short (<10 lines)
- ✅ Prompt is experimental/temporary
- ✅ Config is a one-off test

---

## Summary

**Before:** Copy and paste prompts everywhere  
**After:** Create once, reference everywhere

**Result:** Cleaner configs, easier maintenance, better organization

