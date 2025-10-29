# Architecture

## Overview

The multi-agent collaboration system is built around a shared communication channel where agents communicate using voice net protocol (similar to pilot-ATC radio communication).

## Core Components

### 1. Agents (`src/agents/`)

**BaseAgent**
- Abstract base class for all agents
- Manages agent identity (ID and callsign)
- Integrates with Claude API for response generation
- Implements speaking criteria logic
- Handles message generation and posting

**SquadLeaderAgent**
- Specialized agent for team coordination
- Enhanced speaking criteria (responds to coordination needs)
- Additional helper methods for team management
- Higher priority in response selection

**Speaking Criteria**
- `DirectAddressCriteria`: Respond when directly addressed
- `KeywordCriteria`: Respond when keywords are mentioned
- `QuestionCriteria`: Respond to questions
- `SquadLeaderCriteria`: Leader-specific response logic
- `CompositeCriteria`: Combine multiple criteria with OR logic

### 2. Channel (`src/channel/`)

**Message**
- Data model for individual messages
- Contains sender/recipient info, content, timestamp
- Supports addressing and broadcast detection
- Formats messages for display

**VoiceNetProtocol**
- Parses voice net protocol messages
- Formats messages according to protocol
- Extracts sender/recipient callsigns
- Supports Roger/Copy acknowledgments

**SharedChannel**
- Central communication hub
- Maintains message history
- Provides context retrieval for agents
- Enforces history limits
- Supports message filtering and querying

### 3. Orchestration (`src/orchestration/`)

**Orchestrator**
- Manages the agent roster
- Coordinates message flow
- Determines which agents should respond
- Enforces turn-taking
- Handles user messages
- Manages session lifecycle

### 4. Configuration (`src/config/`)

**Schema (Pydantic)**
- Validates configuration files
- Type-safe configuration
- Supports YAML loading
- Defines agent, channel, and orchestration settings

### 5. CLI (`src/cli/`)

**Main CLI**
- Built with Click
- Commands: demo, interactive, status
- Rich formatting for output

**Commands**
- Demo command: Automated scenarios
- Interactive command: User chat session
- Status command: System information

## Communication Flow

```
User Message
    ↓
Orchestrator.run_turn()
    ↓
SharedChannel.add_message()
    ↓
For each agent:
    agent.should_respond(channel)
        ↓
    agent.generate_response(channel)
        ↓
    SharedChannel.add_message()
```

## Voice Net Protocol

Messages follow this format:
```
[Recipient], this is [Sender], [message content], over.
```

Examples:
- "Alpha Two, this is Alpha Lead, requesting status, over."
- "Roger, all systems operational."
- "Copy, proceeding with analysis."

## Speaking Criteria Logic

Each agent evaluates recent messages to determine if it should respond:

1. Check if agent is directly addressed
2. Check if keywords match agent's expertise
3. Check special conditions (questions, coordination needs, etc.)
4. Don't respond to own messages
5. Squad leader responds as fallback

## Context Management

Agents receive a context window of recent messages when generating responses:
- Default: 20 messages
- Includes messages to/from the agent
- Includes broadcast messages
- Includes system messages
- Provides conversation continuity

## Future Extensions

### Phase 2: MCP Integration
- Tool discovery and registration
- Tool execution framework
- Tool result handling
- Shared tool context

### Phase 3: State Management
- SQLite persistence
- Session save/restore
- Message history export
- Agent state snapshots

### Phase 4: Advanced Features
- Dynamic agent creation
- Agent-to-agent direct messaging
- Subteams and hierarchies
- Multi-channel support
- Web UI interface
