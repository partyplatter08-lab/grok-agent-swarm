#!/usr/bin/env python3
"""UserPromptSubmit hook: activate Agent Swarm when effort is Agent Swarm.

The effort menu option id=swarm is wired to reasoning_effort value=xhigh
(see ensure_swarm_effort.py). When the session is on that effort, inject
orchestrator instructions so every turn runs in swarm mode — no /swarm needed.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def grok_home() -> Path:
    return Path(os.environ.get("GROK_HOME", Path.home() / ".grok"))


def plugin_root() -> Path:
    env = os.environ.get("GROK_PLUGIN_ROOT") or os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env:
        return Path(env)
    # Fallback: this file lives in <plugin>/scripts/
    return Path(__file__).resolve().parent.parent


def find_summary(session_id: str) -> Path | None:
    if not session_id:
        return None
    root = grok_home() / "sessions"
    if not root.is_dir():
        return None
    # sessions/<urlencoded-cwd>/<session-id>/summary.json
    for path in root.rglob("summary.json"):
        if path.parent.name == session_id:
            return path
    return None


def session_effort(session_id: str) -> str | None:
    summary = find_summary(session_id)
    if not summary:
        return None
    try:
        data = json.loads(summary.read_text())
    except Exception:
        return None
    return data.get("reasoning_effort")


def is_swarm_mode(effort: str | None, prompt: str) -> bool:
    if effort in {"xhigh", "max"}:
        # xhigh is the dedicated wire value for the Agent Swarm menu option
        return True
    # Also activate if the user explicitly invoked the skill/command this turn
    p = (prompt or "").lower()
    if "/swarm" in p or "agent swarm" in p:
        return True
    return False


def build_context(skill_path: Path) -> str:
    return f"""# AGENT SWARM MODE (ACTIVE)

You are running in **Agent Swarm** mode (selected via the effort picker: Agent Swarm).

This is not ordinary high-effort single-agent work. You are the **orchestrator**.

## Mandatory behavior

1. **Read and follow** the full protocol at:
   `{skill_path}`
2. **Decompose** the user's task into independent parallel units when it is wide enough.
3. **Fan out** with `spawn_subagent` (`background: true`) — never serial-collapse independent work.
4. **Workers must not spawn subagents** (depth limit is 1). Only you orchestrate.
5. **Synthesize** one coherent deliverable; do not dump raw worker transcripts.
6. If the task is deep/sequential (not swarm-shaped), say so briefly and fall back to normal single-agent work.

## Defaults

- concurrency: 8 (max 24)
- research → explore / read-only; build → general-purpose + worktree with disjoint paths
- Write a short wave plan, then spawn the first wave in one turn

Start by classifying swarm-fit, then either swarm or single-agent as the skill dictates.
"""


def main() -> int:
    raw = sys.stdin.read()
    try:
        event = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        event = {}

    session_id = (
        event.get("sessionId")
        or event.get("session_id")
        or os.environ.get("GROK_SESSION_ID")
        or ""
    )
    prompt = event.get("prompt") or ""
    effort = session_effort(session_id)

    if not is_swarm_mode(effort, prompt):
        # No injection
        print("{}")
        return 0

    skill = plugin_root() / "skills" / "swarm" / "SKILL.md"
    # Prefer absolute real path
    skill_path = skill.resolve() if skill.exists() else skill

    context = build_context(skill_path)
    # Escape for JSON string
    out = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        }
    }
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
