---
name: swarm
description: >
  Kimi-style Agent Swarm for Grok Build. One orchestrator decomposes a wide task into
  independent subtasks, fans out parallel subagents (research / build / mixed), waits
  for results, resolves conflicts, and synthesizes a single deliverable. Use when the
  user runs /swarm, says "agent swarm", "swarm this", "parallel agents", "fan out",
  or wants multi-agent parallel work on a broad task (multi-source research, batch
  analysis, multi-file scaffolding, multi-perspective review).
when-to-use: >
  /swarm, agent swarm, swarm this, parallel agents, fan out subagents, multi-agent
  research, batch parallel work, Kimi swarm style
argument-hint: "<task> [--concurrency N] [--mode research|build|mixed] [--dry-run] [--max-waves N]"
---

# Agent Swarm (Kimi-style)

You are the **orchestrator**. You do **not** do the bulk of the work yourself. You decompose, spawn, wait, reconcile, and synthesize — the same shape as Kimi K3 Agent Swarm (orchestrator + parallel sub-agents + merge).

Grok Build hard limits you must respect:

- **Subagent depth is 1.** Only *you* (the parent session) may call `spawn_subagent`. Workers cannot spawn workers. Never instruct a worker to spawn children.
- Parallelism = many `spawn_subagent` calls with `background: true` in the **same** turn (or a tight ready-queue loop).
- Collect results with `get_command_or_subagent_output`.
- Prefer `isolation: "worktree"` for any worker that edits files; `isolation: "none"` for pure research/read-only workers.

References (read when needed):

- `references/decomposition.md` — how to split tasks
- `references/synthesis.md` — how to merge worker outputs without hallucination amplification

---

## Invocation

```
/swarm <task> [--concurrency N] [--mode research|build|mixed] [--dry-run] [--max-waves N]
```

| Flag | Default | Meaning |
|------|---------|---------|
| `<task>` | required | The goal. Wide tasks win; deep sequential tasks should refuse or fall back to single-agent. |
| `--concurrency N` | `8` | Max simultaneous workers (clamp 1–24). Higher = more cost and merge risk. |
| `--mode` | auto | `research` (read-only explore/general), `build` (write via worktrees), `mixed` (skill-match both). Auto-detect from the task. |
| `--dry-run` | false | Decompose and print the swarm plan only; do not spawn. |
| `--max-waves` | `4` | Max sequential fan-out waves (dependency levels / revise loops). |

Parse flags with natural language understanding. If the user ran `/swarm` with no task, ask once for the goal.

---

## Phase 0 — Swarm fit check (do this first)

Decide if the task is **swarm-shaped**.

**Swarm wins (proceed):**

- Broad search / multi-source survey
- Batch work over many independent items (N products, N files, N APIs)
- Multi-perspective analysis of one question (security / UX / perf / DX in parallel)
- Multi-module scaffolding where modules do not share mutable state mid-build

**Swarm loses (refuse or single-agent fallback):**

- Deep sequential reasoning (each step depends on the last)
- Single-file surgical fix
- Heavy shared-state refactors where workers will collide on the same files
- Tiny tasks where spawn overhead exceeds benefit

If the task is not swarm-shaped:

1. Tell the user why in 2–4 sentences.
2. Offer: (a) proceed as single-agent, or (b) reframe the task to a wider parallel slice.
3. Only continue as swarm if the user insists after the warning.

If it *is* swarm-shaped, announce:

```
Agent Swarm: <short goal>
mode=<mode> concurrency=<N> max-waves=<W>
```

---

## Phase 1 — Decompose

Build a **swarm plan**: independent units of work, not a giant todo list for yourself.

For each unit create:

```
SwarmUnit {
  id: "u-1" | "u-2" | ...
  title: short label
  goal: 1–3 sentence worker brief
  kind: research | implement | review | verify
  inputs: what context the worker needs (paths, URLs, constraints)
  outputs: what the worker must return (summary shape, files, artifacts)
  dependencies: [] of unit ids   // empty = wave 0
  isolation: none | worktree
  subagent_type: explore | general-purpose | plan
  capability_mode: read-only | read-write | execute | all | omit
  success_criteria: how you will judge the unit done
}
```

Rules of good decomposition (see `references/decomposition.md`):

1. **Independence first.** Units that share mutable files should not run in the same wave unless each owns a disjoint path set.
2. **Heterogeneous skill-match.** Route research to `explore` + `read-only`, implementation to `general-purpose` + worktree, architecture to `plan`.
3. **Sized right.** Prefer 4–16 units over 1 giant unit or 100 micro-units. Cap planned concurrent spawns at `--concurrency`.
4. **Explicit outputs.** Every worker prompt ends with a required return contract so synthesis is mechanical, not guessy.
5. **No nested swarms.** Workers execute; only you orchestrate.

Write the plan into a todo list via `todo_write`:

- One top-level todo per unit: `u-<n>: <title>`
- Plus phase todos: `wave-plan`, `synthesize`, `final-report`

If `--dry-run`, print the full plan (units, waves, dependency graph) and **stop**.

---

## Phase 2 — Wave planning

Assign waves by dependency level:

```
wave(unit) = 0                                              if dependencies empty
wave(unit) = max(wave(dep) for dep in dependencies) + 1     otherwise
```

Units in the same wave run in parallel (subject to concurrency).

Present a short wave table to the user before spawning wave 0 (unless the task is tiny and the user already approved via `/swarm`):

```
Wave 0 (parallel, K units): u-1, u-2, u-3
Wave 1 (after 0): u-4, u-5
Wave 2: synthesize
```

Do not wait for user confirmation between waves unless a wave failed hard or produced contradictory facts.

---

## Phase 3 — Spawn (fan-out)

### Tool-call discipline

- Emit real `spawn_subagent` tool calls in the same turn as any “launching…” narration.
- Prefer launching an entire wave in **one** assistant turn (multiple tool calls in parallel).
- Never claim a worker finished without a tool result that says so.

### Spawn parameters

For each unit in the ready set (up to concurrency):

| Field | Guidance |
|-------|----------|
| `prompt` | Full self-contained brief (workers have no parent chat). Include goal, inputs, constraints, and **exact return contract**. |
| `description` | `"[swarm:<kind>] u-<n>: <title>"` — bracket tag labels the tasks pane |
| `subagent_type` | From the unit plan |
| `background` | **always `true`** for wave workers |
| `capability_mode` | From the unit plan when set |
| `isolation` | `worktree` if the unit may edit files; else omit / `none` |
| `cwd` | Only when a later unit must run inside an earlier unit's worktree |

### Worker prompt template

```
You are a swarm worker (unit <id>). You do NOT spawn subagents. Execute only this unit.

## Goal
<title>
<goal>

## Inputs
<inputs>

## Constraints
- Stay inside the assigned scope. Do not expand into other units' work.
- If you discover a blocker that requires another unit, report it; do not take it over.
- Prefer evidence (paths, URLs, quotes) over assertion.
- If editing: touch only the paths listed under Outputs/owned paths.

## Success criteria
<success_criteria>

## Required return format
When done, your final message MUST include:

### Unit <id> Result
- **Status**: success | partial | blocked
- **Summary**: 5–15 lines of what you found/did
- **Evidence**: bullet list of file paths, URLs, or key facts (with sources)
- **Artifacts**: files created/modified (absolute or repo-relative paths)
- **Open questions**: anything the orchestrator must resolve
- **Handoff**: data the next wave needs (structured if possible)

Be concrete. No filler. Incomplete returns will force a respawn.
```

Track for each unit: `subagent_id`, `status` (`pending|running|done|failed`), `result_excerpt`, `worktree_path` if any.

Update todos as units start.

### Concurrency

If a wave has more units than `--concurrency`, run a ready-queue:

1. Spawn up to N units.
2. `get_command_or_subagent_output` with the running ids (wait for completion / poll).
3. Process finished units; spawn next pending units until the wave is empty.

Default wait strategy: pass all in-flight ids and a generous `timeout_ms` (e.g. 600000). If one unit hangs far past the others, kill it with `kill_command_or_subagent`, mark `failed`, and continue.

---

## Phase 4 — Collect & validate

For each finished worker:

1. Read its final message (and any declared artifact files).
2. Score against `success_criteria`.
3. Classify: `success` | `partial` | `failed` | `conflict-risk`.

**Conflict-risk** examples:

- Two workers assert opposite facts about the same entity
- Two workers edited overlapping paths (should be rare if decomposition was clean)
- Critical evidence missing for a high-stakes claim

On `partial`/`failed`:

- Prefer **one** targeted respawn of that unit with a sharper prompt (feed what was missing).
- Do not respawn endlessly: max **2** attempts per unit (initial + 1 retry), then mark failed and continue if the swarm can still deliver value.

On hard multi-unit conflict:

- Do **not** silently average contradictions.
- Either spawn a single `verify` unit with both sides' evidence, or escalate the contradiction to the user before synthesis.

Persist a compact in-memory (or scratch-file) ledger:

```
scratch: ${TMPDIR:-/tmp}/grok-$(id -u)/swarm-<SWARM_ID>.md
```

Create `SWARM_ID` once:

```bash
python3 -c "import uuid; print(uuid.uuid4().hex[:8])"
```

And scratch dir:

```bash
scratch_dir="${TMPDIR:-/tmp}/grok-$(id -u)"; mkdir -p "$scratch_dir" && chmod 700 "$scratch_dir" && echo "$scratch_dir"
```

Write the ledger after each wave so a long run survives compaction better than chat memory alone.

---

## Phase 5 — Multi-wave progression

After wave W completes:

1. Inject successful handoffs into dependent units' prompts for wave W+1.
2. Drop or rewrite dependents of totally failed units; note gaps in the final report.
3. Stop when:
   - all units are terminal, or
   - `--max-waves` is exhausted, or
   - remaining work is pure synthesis.

Optional final wave (if needed and budget remains): a single `verify` worker that fact-checks the merged draft against evidence — still spawned by you, not nested.

---

## Phase 6 — Synthesize (you, the orchestrator)

You produce the **one** user-facing deliverable. Workers never talk to the user as the final voice.

Synthesis rules (see `references/synthesis.md`):

1. **Evidence-backed only.** Prefer claims that appear in worker Evidence sections with sources.
2. **No silent invention** to fill gaps — list gaps under Open Issues.
3. **Resolve structure**, not just concatenate. Tables, ranked lists, unified code, or a single doc — whatever the original task asked for.
4. **Attribute** major findings to unit ids when useful (`[u-3]`).
5. If build mode produced worktrees, either:
   - merge/apply changes carefully yourself after review, or
   - present worktree paths and a clear integration plan — never leave the user with N unintegrated worktrees and no next step.

### Final report shape

```markdown
# Swarm Result: <goal>

## Deliverable
<the actual answer / artifact / code summary>

## Swarm stats
- Units: N (success / partial / failed)
- Waves: W
- Concurrency: C
- Mode: ...

## Unit ledger
| id | title | status | notes |
|----|-------|--------|-------|

## Conflicts & gaps
- ...

## How to go deeper
- Suggested single-agent follow-ups or a second /swarm on a narrower slice
```

---

## Mode cheatsheet

### research (default for surveys, comparisons, multi-source digs)

- Workers: mostly `explore` or `general-purpose` with `capability_mode: "read-only"`
- `isolation: "none"`
- Tools workers should lean on: search, read, web_search, open_page, grep
- You synthesize the brief / table / memo

### build (multi-module implement, batch file generation)

- Workers: `general-purpose`, `isolation: "worktree"` when editing
- Disjoint path ownership per unit is mandatory
- You integrate after workers return (or instruct a final integration unit that receives prior commit SHAs / worktree paths via `cwd` where appropriate)

### mixed

- Wave 0 research/explore → Wave 1 implement → Wave 2 review/verify
- Classic research-judge-execute, but the research and review slices fan out

---

## Anti-patterns (never do these)

1. **Serial collapse** — spawning one worker, waiting, then the next, when they were independent. Always fan out a wave.
2. **Fake parallelism** — saying you launched workers without `spawn_subagent` tool calls.
3. **Nested orchestration** — telling a worker to “spawn more agents.”
4. **Overlapping write scopes** — two worktrees editing the same files in one wave.
5. **Swarm-as-default** — using a swarm for a 2-minute single-path fix.
6. **Concat-only merge** — pasting worker dumps without reconciling structure and conflicts.
7. **Unbounded concurrency** — ignore user machine/API cost; stay within `--concurrency` (max 24).

---

## Cost & honesty knobs

Kimi's marketing ceiling is hundreds of agents; on Grok Build the useful range is usually **4–16** concurrent workers. More than that rarely improves quality and often amplifies conflicting hallucinations. Prefer a second wave of verification over a first wave of 40 shallow agents.

When the user asks for “max swarm” or “like Kimi 300 agents”:

- Explain the Grok depth/cost reality briefly.
- Offer concurrency 16–24 with careful decomposition.
- Do not simulate 300 fake agents.

---

## Quick start examples

**Research swarm**

```
/swarm Compare the top 10 open-source agent frameworks for tool-use and multi-agent support. Table + recommendation. --concurrency 10 --mode research
```

**Build swarm**

```
/swarm Scaffold a monorepo with apps/web, apps/api, packages/ui, packages/config — each package owned by a separate worker. --mode build --concurrency 4
```

**Mixed**

```
/swarm Audit this repo for security, performance, and DX issues in parallel, then propose a prioritized fix list. --mode mixed
```

---

## Resume / crash behavior

If the session compacts or the user re-invokes mid-swarm:

1. Look for the scratch ledger under `${TMPDIR:-/tmp}/grok-$(id -u)/swarm-*.md`.
2. Rebuild todos from the ledger.
3. Skip `success` units; retry `failed`/`partial`; continue the next incomplete wave.

If no ledger exists, re-decompose from the original task (ask the user to paste the goal if missing).
