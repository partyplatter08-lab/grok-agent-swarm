# Visual language — Heavy / Swarm / Swarm Heavy

Grok’s TUI cannot load custom themes per mode. What we **can** control:

1. **Subagent row labels** via `description` bracket tags (`format_subagent_label`)
2. **Scrollback lifecycle text** (what the parent prints when launching / finishing)
3. **Agent `color` frontmatter** on primary agents (red|green|yellow|purple|orange)
4. **Todo titles** in the todo pane

Use this language in every skill and agent so a swarm run never looks like a generic “Subagent running: General”.

---

## Brand marks (ASCII — works everywhere)

| Mode | Mark | Accent name |
|------|------|-------------|
| Heavy | `◈ HEAVY` | purple |
| Agent Swarm | `⬡ SWARM` | orange |
| Swarm Heavy | `⬢ SH` | red |
| Normal | (none) | — |

---

## Banner templates (print to user — exact shapes)

### Mode open

```
┌──────────────────────────────────────────────┐
│  ⬡ SWARM   parallel map → reduce             │
│  goal   <short goal>                         │
│  units  N   waves  W   concurrency  C        │
└──────────────────────────────────────────────┘
```

```
┌──────────────────────────────────────────────┐
│  ◈ HEAVY   collaborative council             │
│  goal     <short goal>                       │
│  council  N   rounds  R                      │
└──────────────────────────────────────────────┘
```

```
┌──────────────────────────────────────────────┐
│  ⬢ SWARM HEAVY   council → fan-out → verify  │
│  goal       <short goal>                     │
│  council  N   swarm  U units · concurrency C │
└──────────────────────────────────────────────┘
```

### Phase / wave

```
── H1 council frame ───────────────────────────
── S2 fan-out  wave 0/2 · 6 agents ────────────
── H2 verify council ──────────────────────────
── synthesize ─────────────────────────────────
```

### Live board (after launch or between waits)

```
 board
 ├─ ●  Council/Analyst     running
 ├─ ●  Council/Skeptic     running
 ├─ ○  Council/Explorer    pending
 └─ ✓  Council/Builder     done · 42s
```

Status glyphs: `●` running · `○` pending · `✓` done · `✗` failed · `◐` partial

### Mode close

```
┌──────────────────────────────────────────────┐
│  ⬡ SWARM complete · 6/6 units · 2 waves      │
│  conflicts  0   gaps  1                      │
└──────────────────────────────────────────────┘
```

Keep banners monospaced. Do **not** use HTML or markdown tables for the live board (plain preformatted text).

---

## Subagent `description` tags (tasks pane labels)

The pager takes the **first** `[tag]` in `description` as the row label and strips it from the shown description.

### Rules

1. Tag is short, Title-Case or slash form, **no spaces inside the tag**.
2. After the tag: a human title (can have spaces).
3. Same tag on `resume_from` follow-ups so the row label stays stable.
4. Never use bare `general-purpose` looks — always a mode tag.

### Heavy council

| Role | `description` |
|------|----------------|
| Analyst | `[Council/Analyst] frame constraints` |
| Skeptic | `[Council/Skeptic] attack assumptions` |
| Explorer | `[Council/Explorer] alternate paths` |
| Builder | `[Council/Builder] feasibility` |
| Verifier | `[Council/Verifier] fact-check` |

Leader never spawns itself as a worker.

### Agent Swarm units

| Kind | `description` |
|------|----------------|
| research unit | `[Swarm/u-3] pricing scrape niche=devtools` |
| implement unit | `[Swarm/u-1] apps/web scaffold` |
| review unit | `[Swarm/review] cross-check claims` |
| verify unit | `[Swarm/verify] evidence pass` |

Always include the unit id (`u-N`) in the tag or title so the board is scannable.

### Swarm Heavy

Prefix phase so the board reads as a pipeline:

| Phase | Tag examples |
|-------|----------------|
| H1 council | `[SH/H1·Analyst]`, `[SH/H1·Skeptic]`, … |
| S fan-out | `[SH/S·u-1]`, `[SH/S·u-2]`, … |
| H2 verify | `[SH/H2·Verifier]`, `[SH/H2·Skeptic]` |

---

## Todo pane titles

Mirror the board:

```
mode:swarm-heavy
H1:council
S1:decompose
S2:fan-out
H2:verify
F:synthesize
u-1:apps/web
u-2:apps/api
```

---

## Narration discipline

**Do:**

```
── S2 fan-out  wave 0 · launching 4 ───────────
```

then emit the `spawn_subagent` tool calls in the **same** turn.

**Don't:**

- “Launching agents…” with no tool calls
- Generic `description: "worker 1"`
- Dumping full worker transcripts mid-run (ledger + final synthesis only)

---

## Color map (primary agent frontmatter)

| Agent | `color` |
|-------|---------|
| heavy | `purple` |
| swarm | `orange` |
| swarm-heavy | `red` |
| modes | `yellow` |

Worker subagents inherit model color; labels carry the identity.

---

## Final report chrome

```
# ⬡ SWARM RESULT · <goal>

## Deliverable
...

## Board (final)
| unit | role | status | notes |
...
```

Same pattern with `◈ HEAVY RESULT` / `⬢ SWARM HEAVY RESULT`.
