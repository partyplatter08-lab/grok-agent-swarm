# Decomposition guide

How the orchestrator should split a task into swarm units.

## Goal

Maximize **independent parallel width** without creating merge hell.

## Algorithm

1. **List the natural units of work** as nouns the user already used (sources, modules, competitors, files, personas, platforms).
2. **Cluster** micro-items into chunks of similar size (e.g. 5–15 sources per research worker, not 1 and not 80).
3. **Draw edges** only when B truly needs A's output (not “nice to have”).
4. **Assign waves** from the dependency DAG.
5. **Assign skills**:
   - Map / discover / read-only → `explore`, `capability_mode: read-only`, `isolation: none`
   - Plan-only architecture → `plan`, read-only tools
   - Implement / write files → `general-purpose`, `isolation: worktree`, disjoint owned paths
   - Critic / review of another unit's artifacts → `general-purpose` or `explore`, often `cwd` to a prior worktree, no overlapping writes
6. **Write success criteria** that are checkable (“return a table with columns X”, “create files A,B”, “list CVEs with links”).

## Good vs bad splits

| Bad | Good |
|-----|------|
| One unit: “build the whole app” | Units per package/module with owned paths |
| 100 units: one per line of a doc | 8–12 thematic clusters |
| Research + write same files same wave | Research wave → implement wave |
| “Also improve performance” bolted onto every unit | Separate verify/review units or a later wave |
| Units that all edit `package.json` | One integration unit owns shared manifests |

## Path ownership (build mode)

Before spawning writers, produce an ownership map:

```
u-1: apps/web/**
u-2: apps/api/**
u-3: packages/ui/**
u-4: packages/config/**   # plus root package.json if needed — only one owner
```

If two units need the same file, either:

- merge them into one unit, or
- put shared-file edits in a later integration unit.

## Heterogeneous skill profiles (Kimi-style)

Kimi routes by skill profile rather than cloning identical agents. Mirror that:

| Task flavor | subagent_type | capability | isolation |
|-------------|---------------|------------|-----------|
| Web / doc survey | explore or general-purpose | read-only | none |
| Codebase archaeology | explore | read-only or execute | none |
| Greenfield module | general-purpose | all | worktree |
| Architecture options | plan | read-only | none |
| Adversarial review | general-purpose | read-only | none or cwd |

## Sizing heuristic

```
ideal_units ≈ min(
  concurrency * 1.5,
  natural_item_count / items_per_worker,
  24
)
```

If you only have 2 natural units, run 2 — do not invent fake units for the optics of a swarm.

## Dependency patterns

**Map-reduce (most common)**

```
wave0: map units (independent)
wave1: optional reduce/verify
orchestrator: final synthesis
```

**Pipeline fan-out**

```
wave0: shared discovery (1–2 explore agents)
wave1: parallel specialists using discovery handoff
wave2: integration / review
```

**Multi-perspective**

```
wave0: security, performance, UX, reliability in parallel on the same target
orchestrator: ranked combined findings (dedupe)
```
