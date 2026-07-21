# Agent Swarm for Grok Build

Kimi-style **Agent Swarm**, Grok **Heavy** collaborative multi-agent, and **Swarm Heavy** (both) — installable plugin with first-class **effort selector** modes.

## Effort selector (top → bottom)

| Menu label | Mode | What it is |
|------------|------|------------|
| **Swarm Heavy** | Council + fan-out | Heavy debate, then K3-style parallel swarm, then verify |
| **Agent Swarm** | Map / reduce | Decompose wide work → parallel subagents → synthesize |
| **Heavy** | Collaborative | Grok Heavy-style multi-agent debate on one hard problem |
| High Effort | Stock | Single-agent, high reasoning (default) |
| Medium Effort | Stock | Balanced |
| Low Effort | Stock | Fast |

Special modes sit **above** High.

## Install

```bash
grok plugin install partyplatter08-lab/grok-agent-swarm --trust
grok plugin enable agent-swarm
```

Start a **new session** once so SessionStart registers the menu and installs agents.

```bash
# or force setup now
export GROK_PLUGIN_ROOT="$(grok plugin details agent-swarm 2>/dev/null | sed -n 's/.*path: //p' | head -1)"
python3 "$GROK_PLUGIN_ROOT/scripts/ensure_swarm_effort.py"
```

### Verify

```bash
# Menu accepts special modes (wire value xhigh for all three specials):
grok -p "ping" --effort swarm-heavy
grok -p "ping" --effort swarm
grok -p "ping" --effort heavy

# Full protocols via agents:
grok -p "Are you Heavy leader?" --agent heavy
grok -p "Are you Swarm orchestrator?" --agent swarm
grok -p "Are you Swarm Heavy?" --agent swarm-heavy
```

## How to run each mode

Grok does not let plugins rewrite the system prompt when you only change **effort**. Effort options set maximum reasoning (`xhigh`) and label the intent. **Full protocols** activate via the matching **agent** or slash command:

| Want | Effort picker | Agent / command |
|------|---------------|-----------------|
| Collaborative debate | **Heavy** | `/agents` → `heavy` or `/heavy` or `--agent heavy` |
| Wide parallel fan-out | **Agent Swarm** | `/agents` → `swarm` or `/swarm` or `--agent swarm` |
| Both (max mode) | **Swarm Heavy** | `/agents` → `swarm-heavy` or `/swarm-heavy` or `--agent swarm-heavy` |

**Seamless daily setup:** set default agent in `/agents` to the mode you use most, and pick the matching effort option for reasoning headroom.

### Examples

```text
/heavy Is this API design sound? Attack it from security, DX, and scale.

/swarm Build a comparison table of 12 competitor pricing pages. --concurrency 12

/swarm-heavy Design the monorepo layout, then scaffold apps/web, apps/api,
  packages/ui in parallel, then adversarial review. --council 4 --concurrency 3
```

## Mode cheat sheet

### Heavy (Grok Heavy-style)

- **One** hard problem, **many** minds
- Parallel council (default 4): Analyst, Skeptic, Explorer, Implementer
- Cross-check rounds, leader synthesis
- Like a study group that argues before answering

### Agent Swarm (Kimi K3-style)

- **Wide** work split into independent units
- Map → parallel workers → reduce
- Research / build / mixed modes
- Depth-1 orchestrator only (Grok limit)

### Swarm Heavy

```
H1 council frame → S1 decompose → S2 fan-out → H2 verify council → Final
```

Maximum depth **and** width. Expensive — use for architecture + parallel build + review, not typos.

## What’s inside

```
skills/
  heavy/           Collaborative multi-agent protocol
  swarm/           K3-style swarm protocol
  swarm-heavy/     Hybrid pipeline
agents/
  heavy.md
  swarm.md
  swarm-heavy.md
  swarm-worker.md / swarm-researcher.md / swarm-reviewer.md
commands/
  heavy.md / swarm.md / swarm-heavy.md
scripts/ensure_swarm_effort.py   # effort menu + agent install
hooks/hooks.json
```

## Uninstall

```bash
grok plugin disable agent-swarm
grok plugin uninstall agent-swarm --confirm
rm -f ~/.grok/hooks/agent-swarm.json
rm -f ~/.grok/agents/{swarm,heavy,swarm-heavy}.md
# optional: remove managed effort block in ~/.grok/config.toml
```

## License

MIT
