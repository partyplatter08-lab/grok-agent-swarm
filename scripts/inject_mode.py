#!/usr/bin/env python3
"""UserPromptSubmit: set active multi-agent mode from effort (seamless).

Effort menu wire values (unique so we can detect which mode was selected):

  swarm-heavy → xhigh
  heavy       → minimal   (detectable; multi-agent structure carries the load)
  swarm       → none      (detectable; parallelism carries the load)
  high/medium/low → normal

Also honors explicit slash/mentions in the prompt: /swarm-heavy, /swarm, /heavy.

Writes: ~/.grok/agent-swarm-mode
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path


MODE_FILE = Path.home() / ".grok" / "agent-swarm-mode"

# Wire value → mode (see ensure_swarm_effort.py EFFORTS)
WIRE_TO_MODE = {
    "xhigh": "swarm-heavy",
    "max": "swarm-heavy",  # if ever accepted
    "minimal": "heavy",
    "none": "swarm",
    "high": "normal",
    "medium": "normal",
    "low": "normal",
}


def grok_home() -> Path:
    return Path(os.environ.get("GROK_HOME", Path.home() / ".grok"))


def find_summary(session_id: str) -> Path | None:
    if not session_id:
        return None
    root = grok_home() / "sessions"
    if not root.is_dir():
        return None
    for path in root.rglob("summary.json"):
        if path.parent.name == session_id:
            return path
    return None


def session_effort(session_id: str) -> str | None:
    for _ in range(8):
        summary = find_summary(session_id)
        if summary and summary.is_file():
            try:
                data = json.loads(summary.read_text())
                effort = data.get("reasoning_effort")
                if effort is not None and effort != "":
                    return str(effort)
            except Exception:
                pass
        time.sleep(0.05)
    return None


def mode_from_prompt(prompt: str) -> str | None:
    p = (prompt or "").lower()
    # Order matters: swarm-heavy before swarm/heavy
    if re.search(r"/swarm-heavy\b|swarm\s*heavy|heavy\s*swarm", p):
        return "swarm-heavy"
    if re.search(r"/swarm\b|agent\s*swarm", p):
        return "swarm"
    if re.search(r"/heavy\b|heavy\s*mode|grok\s*heavy", p):
        return "heavy"
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
    prompt = event.get("prompt") or ""

    mode = mode_from_prompt(prompt)
    if not mode:
        effort = session_effort(session_id)
        mode = WIRE_TO_MODE.get(effort or "", "normal")

    MODE_FILE.parent.mkdir(parents=True, exist_ok=True)
    MODE_FILE.write_text(mode + "\n")

    # No additionalContext (Grok ignores it). Mode file + modes agent is the path.
    print("{}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
