---
description: Run a Kimi-style Agent Swarm — decompose a wide task, fan out parallel subagents, synthesize one deliverable
argument-hint: "<task> [--concurrency N] [--mode research|build|mixed] [--dry-run]"
---

# /swarm

Load and follow the **agent-swarm** skill (`skills/swarm/SKILL.md` in this plugin).

User task and flags:

$ARGUMENTS

Treat the arguments as the swarm goal. If empty, ask the user what wide, parallelizable task they want the swarm to tackle.
