# Agent Swarm for Grok Build

Kimi K3–style **Agent Swarm** as a drop-in [Grok Build](https://x.ai) plugin — including a first-class option in the **effort selector**.

```
  Effort picker                    Session behavior
  ┌─────────────────┐              ┌──────────────────────────┐
  │ High Effort     │              │ single agent             │
  │ Medium Effort   │              │ single agent             │
  │ Low Effort      │              │ single agent             │
  │ Agent Swarm  ◄──┼── select ──► │ orchestrator + subagents │
  └─────────────────┘              └──────────────────────────┘
```

## Install (any Grok Build machine)

```bash
grok plugin install partyplatter08-lab/grok-agent-swarm --trust
grok plugin enable agent-swarm
```

Pin a release:

```bash
grok plugin install partyplatter08-lab/grok-agent-swarm@v1.1.0 --trust
```

Then **start a new session** (or reload hooks). On `SessionStart` the plugin writes the effort-menu entry into `~/.grok/config.toml`.

### Verify

```bash
grok plugin list
# Agent Swarm should be listed among effort options:
grok -p "ping" --effort swarm   # accepted; remaps wire value to xhigh
```

In the TUI: open the model/effort picker → choose **Agent Swarm**.

## Seamless usage

| How | What happens |
|-----|----------------|
| **Effort selector → Agent Swarm** | Every prompt runs in orchestrator mode (hook injects the swarm protocol). |
| `/effort swarm` | Same as the picker. |
| `grok --effort swarm ...` | Same in headless. |
| `/swarm <task>` | Explicit skill entry (still available). |
| `/agents` → **swarm** | Optional primary agent with the same protocol. |

You should not need to type `/swarm` after selecting **Agent Swarm** in the effort menu. Just give the task.

### Examples

```text
# After selecting Agent Swarm in the effort picker:
Survey 12 competitor pricing pages into a comparison table.

Scaffold apps/web, apps/api, packages/ui with disjoint path ownership.

Security, performance, and DX audit in parallel, then a ranked fix list.
```

Or explicitly:

```text
/swarm Compare the top open-source agent frameworks. --concurrency 10 --mode research
```

## How the effort option works

Plugins cannot invent new API reasoning levels. This plugin:

1. **SessionStart** — ensures your default model’s effort menu includes:

   | Menu id | Label | Wire value |
   |---------|-------|------------|
   | `high` / `medium` / `low` | stock | same |
   | **`swarm`** | **Agent Swarm** | **`xhigh`** |

2. **UserPromptSubmit** — if the session’s `reasoning_effort` is `xhigh` (the swarm wire value), injects orchestrator instructions so the model loads the swarm skill and fans out subagents.

`xhigh` is reserved for this menu entry so swarm is distinguishable from ordinary **High Effort** (`high`). Stock low/medium/high stay unchanged.

Managed config lives between markers in `~/.grok/config.toml`:

```toml
# --- agent-swarm effort (managed) ---
...
# --- agent-swarm effort end ---
```

Uninstalling the plugin stops injection; remove the managed block manually if you want the stock effort list only.

## When to use a swarm

**Good fit:** multi-source research, batch extraction, multi-module scaffolds with clear path ownership, multi-perspective reviews.

**Bad fit:** single-file fixes, long sequential refactors with shared mutable state. The orchestrator will warn and fall back to single-agent when the task is not swarm-shaped.

## What’s inside

```
grok-agent-swarm/
├── plugin.json
├── hooks/hooks.json              # SessionStart + UserPromptSubmit
├── scripts/
│   ├── ensure_swarm_effort.py    # register effort-picker option
│   └── inject_swarm_mode.py      # activate protocol when swarm selected
├── commands/swarm.md
├── skills/swarm/
│   ├── SKILL.md
│   └── references/
├── agents/
│   ├── swarm.md                  # primary orchestrator agent
│   ├── swarm-worker.md
│   ├── swarm-researcher.md
│   └── swarm-reviewer.md
└── README.md
```

## Design notes (vs Kimi K3 Swarm Max)

| Kimi K3 Swarm | This plugin |
|---------------|-------------|
| Learned PARL orchestrator | Prompted skill + effort-mode injection |
| ~300 sub-agents | Default 8, cap 24 |
| Nested coordination | Flat tree (Grok depth 1) |
| Dedicated Swarm Max model | Effort picker option on your Grok model |

## Uninstall

```bash
grok plugin disable agent-swarm
grok plugin uninstall agent-swarm --confirm
# optional: delete the managed block in ~/.grok/config.toml
```

## License

MIT
