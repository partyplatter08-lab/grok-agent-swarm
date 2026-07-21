#!/usr/bin/env python3
"""UserPromptSubmit: map effort → desired mode; promote when idle.

Seamless effort semantics:
  - Reading the effort picker updates *desired* mode every user message.
  - *active* mode only changes when no multi-agent lock is held (pipeline idle).
  - In-flight swarm/heavy workers keep the mode that started them until unlock.

Also honors /swarm-heavy, /swarm, /heavy in the prompt (sets desired; same promote rules).
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

# Allow running as installed plugin script
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import mode_state as ms  # noqa: E402


def mode_from_prompt(prompt: str) -> str | None:
    p = (prompt or "").lower()
    if re.search(r"/swarm-heavy\b|swarm\s*heavy|heavy\s*swarm", p):
        return "swarm-heavy"
    if re.search(r"/swarm\b|agent\s*swarm", p):
        return "swarm"
    if re.search(r"/heavy\b|heavy\s*mode|grok\s*heavy", p):
        return "heavy"
    # Explicit back to normal
    if re.search(r"/effort\s+(high|medium|low)\b", p):
        return "normal"
    return None


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
    if not session_id:
        print("{}")
        return 0

    ms.set_current_session(session_id)
    prompt = event.get("prompt") or ""

    # Promote any deferred switch if previous pipeline finished without unlock
    ms.promote_if_idle(session_id)

    prompt_mode = mode_from_prompt(prompt)
    effort = ms.session_effort(session_id)
    if prompt_mode:
        desired = prompt_mode
    else:
        desired = ms.mode_from_wire(effort)

    state = ms.set_desired(session_id, desired, effort=effort or "")

    # Agent reads ~/.grok/agent-swarm-mode (active) + optional pending file
    # Nothing else to inject (Grok ignores additionalContext on this hook).
    _ = state
    print("{}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
