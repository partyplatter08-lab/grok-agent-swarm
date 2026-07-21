# Agent Swarm for Grok Build

Kimi-style **Agent Swarm** as a Grok Build plugin — including **Agent Swarm** in the **effort selector**.

## Install

```bash
grok plugin install partyplatter08-lab/grok-agent-swarm --trust
grok plugin enable agent-swarm
```

Start a **new session** once (or run the ensure script). SessionStart registers the effort option and installs the `swarm` agent.

```bash
# optional explicit setup
python3 ~/.grok/installed-plugins/*/scripts/ensure_swarm_effort.py
```

### Verify

```bash
# Effort menu accepts swarm:
grok -p "ping" --effort swarm

# Full orchestrator agent:
grok -p "Are you the swarm orchestrator?" --agent swarm
```

In the TUI effort picker you should see:

| Option | Role |
|--------|------|
| High Effort | Normal single-agent, high reasoning |
| Medium Effort | Balanced |
| Low Effort | Fast |
| **Agent Swarm** | Swarm-oriented effort (wire: `xhigh`) |

## Seamless usage

### 1. Effort selector (what you asked for)

Open the model/effort picker and choose **Agent Swarm**, or:

```text
/effort swarm
```

That registers the swarm effort level on the session (high-capacity reasoning via wire value `xhigh`).

### 2. Full orchestrator protocol (recommended companion)

Grok does not let plugins rewrite the system prompt when you change effort, so the **orchestrator instructions** live on the **`swarm` agent**:

| Action | Result |
|--------|--------|
| `/agents` → select **swarm** | Session becomes the orchestrator |
| `grok --agent swarm ...` | Same headless |
| `GROK_AGENT=swarm` | Default agent for the process |
| `/swarm <task>` | Skill entry with the same protocol |

**Most seamless daily setup:** set the default agent to `swarm` once in `/agents` (or keep using `/effort swarm` + `/swarm` for individual tasks).

### 3. Just give it work

With the `swarm` agent active (or after `/swarm`):

```text
Survey 12 competitor pricing pages into a comparison table.
Scaffold apps/web, apps/api, packages/ui with disjoint paths.
Security + performance + DX audit in parallel, then ranked fixes.
```

## How the effort option is installed

`scripts/ensure_swarm_effort.py` writes a managed block into `~/.grok/config.toml`:

```toml
# --- agent-swarm effort (managed) ---
[model."grok-4.5"]
supports_reasoning_effort = true

[[model."grok-4.5".reasoning_efforts]]
id = "high"
...
[[model."grok-4.5".reasoning_efforts]]
id = "swarm"
value = "xhigh"
label = "Agent Swarm"
description = "Parallel multi-agent orchestration..."
# --- agent-swarm effort end ---
```

Wire value is **`xhigh`** so swarm is distinct from ordinary **High Effort** (`high`). Stock low/medium/high stay available.

It also copies `agents/swarm.md` → `~/.grok/agents/swarm.md`.

## What’s in the plugin

```
skills/swarm/          Orchestrator protocol
commands/swarm.md      /swarm
agents/swarm.md        Primary orchestrator agent
agents/swarm-*.md      Worker specializations
scripts/ensure_swarm_effort.py
hooks/hooks.json       SessionStart → ensure
```

## Uninstall

```bash
grok plugin disable agent-swarm
grok plugin uninstall agent-swarm --confirm
rm -f ~/.grok/hooks/agent-swarm.json ~/.grok/agents/swarm.md
# optional: delete the managed block in ~/.grok/config.toml
```

## License

MIT
