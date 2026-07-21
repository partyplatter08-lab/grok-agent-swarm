#!/usr/bin/env python3
"""Stop hook: after a turn finishes, promote desired→active if pipeline unlocked.

If the orchestrator forgot to unlock, we still only promote when no lock file
exists — we never kill subagents and never clear a lock here (only the agent
clears the lock when its multi-agent task is done).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import mode_state as ms  # noqa: E402


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
        or ms.current_session_id()
    )
    if session_id:
        ms.set_current_session(session_id)
        ms.promote_if_idle(session_id)
    print("{}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
