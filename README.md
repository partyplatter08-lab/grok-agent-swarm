# Agent Swarm for Grok Build

Kimi K3–style **Agent Swarm** as a drop-in [Grok Build](https://x.ai) plugin.

One orchestrator (your main session) decomposes a **wide** task, fans out parallel subagents, waits for results, resolves conflicts, and synthesizes a single deliverable.

```
                 ┌──────────────────┐
                 │   Orchestrator   │  ← you / /swarm skill
                 │  decompose+merge │
                 └────────┬─────────┘
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
     ┌─────────┐    ┌─────────┐    ┌─────────┐
     │ worker  │    │ worker  │    │ worker  │  ← background subagents
     └─────────┘    └─────────┘    └─────────┘
```

This is **not** Moonshot’s PARL-trained model weights. It is the same *workflow shape* (orchestrator → parallel sub-agents → synthesize) implemented with Grok Build’s real primitives: skills, `spawn_subagent`, worktrees, and a depth-1 agent tree.

## Install (any Grok Build machine)

### From GitHub (recommended)

```bash
grok plugin install partyplatter08-lab/grok-agent-swarm --trust
grok plugin enable agent-swarm
```

Pin a version/commit if you want:

```bash
grok plugin install partyplatter08-lab/grok-agent-swarm@v1.0.0 --trust
```

### From a local clone

```bash
git clone https://github.com/partyplatter08-lab/grok-agent-swarm.git
grok plugin install ./grok-agent-swarm --trust
grok plugin enable agent-swarm
```

### Verify

```bash
grok plugin list
grok inspect          # should show skill "swarm" from plugin: agent-swarm
```

In a session:

```
/swarm
/plugins              # confirm agent-swarm is enabled
```

## Usage

```text
/swarm <task> [--concurrency N] [--mode research|build|mixed] [--dry-run] [--max-waves N]
```

| Flag | Default | Purpose |
|------|---------|---------|
| `--concurrency N` | `8` | Max simultaneous workers (1–24) |
| `--mode` | auto | `research`, `build`, or `mixed` |
| `--dry-run` | off | Plan only — no spawns |
| `--max-waves` | `4` | Max dependency / revise waves |

### Examples

```text
/swarm Survey 12 competitor pricing pages and return a comparison table. --mode research --concurrency 12

/swarm Scaffold apps/web, apps/api, packages/ui with disjoint path ownership. --mode build --concurrency 3

/swarm Security, performance, and DX audit of this repo in parallel, then a ranked fix list. --mode mixed

/swarm Compare agent frameworks for tool use --dry-run
```

Natural language also works once the plugin is enabled:

> “Swarm this: pull structured notes from every markdown file under docs/ and build one FAQ.”

## When to use a swarm

**Good fit**

- Multi-source research / batch extraction
- Multi-module scaffolding with clear path ownership
- Multi-perspective reviews (security ∥ perf ∥ UX)
- Anything that is *wide* more than *deep*

**Bad fit**

- Single-file fixes
- Long sequential refactors with shared mutable state
- Tasks where each step depends on the previous answer

The skill will warn and offer single-agent fallback when the task is not swarm-shaped.

## What’s inside

```
grok-agent-swarm/
├── plugin.json
├── .claude-plugin/plugin.json   # marketplace-compatible manifest
├── commands/swarm.md            # /swarm slash entry
├── skills/swarm/
│   ├── SKILL.md                 # orchestrator protocol
│   └── references/
│       ├── decomposition.md
│       └── synthesis.md
├── agents/
│   ├── swarm-worker.md
│   ├── swarm-researcher.md
│   └── swarm-reviewer.md
├── LICENSE
└── README.md
```

| Piece | Role |
|-------|------|
| `skills/swarm` | Main protocol — orchestrator behavior, waves, spawn rules, synthesis |
| `commands/swarm` | Slash-command entry that loads the skill |
| `agents/*` | Optional specialized worker definitions |

## Design notes (vs Kimi K3 Swarm Max)

| Kimi K3 Swarm | This plugin on Grok Build |
|---------------|---------------------------|
| Learned PARL orchestrator policy | Prompted skill protocol |
| Up to ~300 sub-agents | Practical default 8 (cap 24) |
| Nested coordination budget ~4k steps | Flat tree: parent only spawns (depth 1) |
| Dedicated Swarm Max model | Your current Grok model + subagents |

Higher concurrency is available via `--concurrency`, but quality usually peaks well below marketing ceilings. Prefer a second **verify** wave over dozens of shallow workers.

## Uninstall

```bash
grok plugin disable agent-swarm
grok plugin uninstall agent-swarm --confirm
```

## License

MIT
