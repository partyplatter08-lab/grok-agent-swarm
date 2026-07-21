---
name: swarm-heavy
description: >
  Swarm Heavy mode: Grok Heavy collaborative multi-agent council plus Kimi K3-style
  Agent Swarm fan-out. First debate and plan with a council, then decompose and
  execute wide work with parallel subagents, then re-council to verify and
  synthesize. Use when the user runs /swarm-heavy, says "swarm heavy", "heavy swarm",
  or picks Swarm Heavy in the effort selector.
when-to-use: >
  /swarm-heavy, swarm heavy, heavy swarm, collaborative swarm, maximum multi-agent,
  council then fan-out
argument-hint: "<task> [--council N] [--concurrency N] [--dry-run]"
---

# Swarm Heavy Mode

You combine **two** systems:

1. **Heavy** — collaborative multi-agent council (same problem, many lenses, debate)
2. **Swarm** — K3-style map/reduce fan-out (wide independent units in parallel)

You are the **single orchestrator**. Depth limit is 1: only you spawn subagents.

Load full detail when needed:

- Heavy protocol: skill `heavy` (`skills/heavy/SKILL.md` in this plugin)
- Swarm protocol: skill `swarm` (`skills/swarm/SKILL.md` in this plugin)
- **Visuals (mandatory):** `skills/shared/visuals.md`

## Effort / mode switching

If effort changes mid-run: **never** abort healthy H1/S/H2 agents. Complete the
pipeline, unlock mode state, then adopt the new effort on the next user turn.

## Visual identity (mandatory)

1. Open with the `⬢ SWARM HEAVY` banner from visuals.md.
2. Tags by phase (tasks pane must not say “General”):
   - H1: `[SH/H1·Analyst]`, `[SH/H1·Skeptic]`, `[SH/H1·Explorer]`, `[SH/H1·Builder]`
   - S:  `[SH/S·u-N] <title>`
   - H2: `[SH/H2·Verifier]`, `[SH/H2·Skeptic]`
3. Phase rules before every spawn cluster:
   `── H1 council frame ──` / `── S2 fan-out  wave k ──` / `── H2 verify ──`
4. Live board between phases; close with SWARM HEAVY complete banner.
5. Final report: `# ⬢ SWARM HEAVY RESULT · <goal>`

---

## Invocation

```
/swarm-heavy <task> [--council N] [--concurrency N] [--dry-run]
```

| Flag | Default | Meaning |
|------|---------|---------|
| `--council N` | `4` | Heavy council size (3–6). |
| `--concurrency N` | `8` | Max parallel swarm workers (1–24). |
| `--dry-run` | off | Plan only. |

---

## Pipeline

```
Phase H1  Heavy council — frame problem, surface approaches, risks
    ↓
Phase S1  Swarm decompose — independent units from council plan
    ↓
Phase S2  Swarm fan-out — parallel workers (background: true)
    ↓
Phase H2  Heavy re-council — verify results, attack weak claims
    ↓
Phase F   Final synthesis — one deliverable
```

Skip S-phases only if the task is pure judgment with no parallelizable width.  
Skip H1 only if the user already provided a locked plan and wants pure fan-out (prefer `/swarm` then).

---

## Phase H1 — Council frame

Run Heavy Phase 0–1 with `--agents` = council N (default 4: Analyst, Skeptic, Explorer, Builder).
Use tags `[SH/H1·Analyst]` etc. Print `── H1 council frame ──` then spawn.

Council must return:

- Shared problem framing
- Recommended approach (or top 2 options with trade-offs)
- What can be parallelized (swarm units)
- What must stay sequential
- Risks / non-goals

You (leader) produce a **Execution Brief**:

```markdown
## Execution Brief
- Goal:
- Approach:
- Parallel units: [list]
- Sequential gates:
- Constraints:
- Success criteria:
```

If `--dry-run`, stop after the brief.

---

## Phase S1 — Decompose

Using the Execution Brief, build a swarm unit plan (see swarm skill + `references/decomposition.md`):

- Independent units, skill-matched (`explore` / `general-purpose` / `plan`)
- Disjoint path ownership for writers
- Waves by dependency level
- Concurrency cap = `--concurrency`

Write todos for units + phases.

---

## Phase S2 — Fan-out

Execute swarm waves exactly as `/swarm` Phase 3–5:

- `background: true` for all wave workers
- Description tags: `"[SH/S·u-<n>] <title>"`
- Phase rule `── S2 fan-out  wave k · launching N ──` then spawn
- Required worker return contract (Status / Summary / Evidence / Artifacts / Handoff)
- Retry failed units once; do not serial-collapse independent work
- Live board while waiting

---

## Phase H2 — Verify council

After swarm results are in, run a **short** Heavy re-council (2–4 agents is enough):

Roles: Skeptic + Verifier (+ Analyst if needed). Tags: `[SH/H2·Skeptic]`, `[SH/H2·Verifier]`.
Print `── H2 verify council ──` then spawn.

Give them:

- Execution Brief
- Compact unit ledger + key evidence (not full dumps)
- Any conflicts you already spotted

They must:

- Challenge weak or contradictory claims
- Flag missing coverage
- Approve or request a targeted swarm retry (specific unit ids)

If they demand a retry, spawn only the named units, then re-check once more (cap one verify loop unless user asks for more).

---

## Phase F — Final synthesis

One voice. Structure:

```markdown
# ⬢ SWARM HEAVY RESULT · <goal>

## Deliverable
<the answer / artifact>

## Method
- Council: N agents, R rounds
- Swarm: U units, W waves, concurrency C

## Board (final)
| id / role | status | notes |

## Council consensus
- ...

## Conflicts & gaps
- ...

## Confidence
high | medium | low
```

---

## Hard rules

1. **You alone spawn.** No nested orchestrators.
2. **Heavy = same problem, many lenses.** Swarm = many units, one lens each.
3. **Do not skip evidence** when H2 and S2 disagree — flag it.
4. **Tool-call discipline** — real `spawn_subagent` calls when you claim launches.
5. **Cost honesty** — Swarm Heavy is expensive; for tiny tasks refuse and suggest single-agent or plain Heavy/Swarm.

---

## Quick fit check

| Task | Mode |
|------|------|
| “Is this design sound?” | Heavy |
| “Scrape 40 sources into a table” | Swarm |
| “Design the architecture, then build all packages in parallel, then review” | **Swarm Heavy** |
| Typo fix | Single agent |
