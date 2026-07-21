#!/usr/bin/env python3
"""Shared state for seamless effort → mode switching.

Per-session files under ~/.grok/agent-swarm/sessions/<session_id>/:

  active     — mode the orchestrator is currently running under
  desired    — mode implied by the latest effort selection
  lock       — present while a multi-agent pipeline is in flight
  effort     — last seen wire effort value
  meta.json  — timestamps + last transition notes

Rules (normal effort semantics):
  - Changing effort updates *desired* immediately.
  - *active* switches on the next clean boundary:
      * no lock, and
      * start of a user turn (UserPromptSubmit) OR end of turn (Stop) with no lock
  - While lock is held (swarm/heavy agents working), active stays put so
    in-flight workers finish under the mode that started them.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

MODES = frozenset({"normal", "heavy", "swarm", "swarm-heavy"})

WIRE_TO_MODE = {
    "xhigh": "swarm-heavy",
    "max": "swarm-heavy",
    "minimal": "heavy",
    "none": "swarm",
    "high": "normal",
    "medium": "normal",
    "low": "normal",
}


def grok_home() -> Path:
    return Path(os.environ.get("GROK_HOME", Path.home() / ".grok"))


def root() -> Path:
    return grok_home() / "agent-swarm"


def sessions_dir() -> Path:
    return root() / "sessions"


def session_dir(session_id: str) -> Path:
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in (session_id or "unknown"))
    d = sessions_dir() / safe
    d.mkdir(parents=True, exist_ok=True)
    return d


def set_current_session(session_id: str) -> None:
    root().mkdir(parents=True, exist_ok=True)
    (root() / "current-session").write_text((session_id or "").strip() + "\n")


def current_session_id() -> str:
    p = root() / "current-session"
    if p.is_file():
        return p.read_text().strip()
    return ""


def _read_text(path: Path, default: str = "") -> str:
    try:
        return path.read_text().strip()
    except Exception:
        return default


def _write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.strip() + "\n")


def load(session_id: str) -> dict[str, Any]:
    d = session_dir(session_id)
    active = _read_text(d / "active", "normal") or "normal"
    desired = _read_text(d / "desired", active) or active
    if active not in MODES:
        active = "normal"
    if desired not in MODES:
        desired = active
    lock = (d / "lock").is_file()
    effort = _read_text(d / "effort", "")
    meta: dict[str, Any] = {}
    mp = d / "meta.json"
    if mp.is_file():
        try:
            meta = json.loads(mp.read_text())
        except Exception:
            meta = {}
    return {
        "session_id": session_id,
        "active": active,
        "desired": desired,
        "in_progress": lock,
        "effort": effort,
        "meta": meta,
        "dir": str(d),
    }


def _save_meta(session_id: str, **fields: Any) -> None:
    d = session_dir(session_id)
    mp = d / "meta.json"
    meta: dict[str, Any] = {}
    if mp.is_file():
        try:
            meta = json.loads(mp.read_text())
        except Exception:
            meta = {}
    meta.update(fields)
    meta["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    mp.write_text(json.dumps(meta, indent=2) + "\n")


def set_desired(session_id: str, mode: str, effort: str | None = None) -> dict[str, Any]:
    if mode not in MODES:
        mode = "normal"
    d = session_dir(session_id)
    _write_text(d / "desired", mode)
    if effort is not None:
        _write_text(d / "effort", effort)
    state = load(session_id)
    # Promote immediately if nothing in flight
    if not state["in_progress"]:
        _write_text(d / "active", mode)
        _save_meta(session_id, last_promote="immediate", active=mode, desired=mode)
    else:
        _save_meta(
            session_id,
            last_promote="deferred",
            active=state["active"],
            desired=mode,
            note="multi-agent pipeline in progress; keep active until unlock",
        )
    # Compat symlink-style single file for simple cat in agents
    _write_compat_active(session_id)
    return load(session_id)


def promote_if_idle(session_id: str) -> dict[str, Any]:
    """If no lock, set active = desired. Call on Stop / UserPromptSubmit."""
    state = load(session_id)
    d = session_dir(session_id)
    if not state["in_progress"] and state["active"] != state["desired"]:
        _write_text(d / "active", state["desired"])
        _save_meta(
            session_id,
            last_promote="boundary",
            active=state["desired"],
            desired=state["desired"],
        )
    _write_compat_active(session_id)
    return load(session_id)


def lock(session_id: str, mode: str | None = None) -> None:
    d = session_dir(session_id)
    if mode and mode in MODES:
        _write_text(d / "active", mode)
    (d / "lock").write_text(
        json.dumps(
            {
                "mode": mode or _read_text(d / "active", "normal"),
                "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )
        + "\n"
    )
    _save_meta(session_id, locked=True)
    _write_compat_active(session_id)


def unlock(session_id: str, promote: bool = True) -> dict[str, Any]:
    d = session_dir(session_id)
    lock_path = d / "lock"
    if lock_path.is_file():
        lock_path.unlink()
    _save_meta(session_id, locked=False)
    if promote:
        return promote_if_idle(session_id)
    _write_compat_active(session_id)
    return load(session_id)


def _write_compat_active(session_id: str) -> None:
    """Write ~/.grok/agent-swarm-mode for one-line cat in agent prompts."""
    state = load(session_id)
    # Show active mode; if deferred switch pending, still active (not desired)
    path = grok_home() / "agent-swarm-mode"
    path.write_text(state["active"] + "\n")
    # Also write pending marker for agent awareness
    pending = grok_home() / "agent-swarm-mode-pending"
    if state["desired"] != state["active"]:
        pending.write_text(state["desired"] + "\n")
    elif pending.is_file():
        pending.unlink()


def find_summary(session_id: str) -> Path | None:
    if not session_id:
        return None
    root_sess = grok_home() / "sessions"
    if not root_sess.is_dir():
        return None
    for path in root_sess.rglob("summary.json"):
        if path.parent.name == session_id:
            return path
    return None


def session_effort(session_id: str, retries: int = 8) -> str | None:
    for _ in range(retries):
        summary = find_summary(session_id)
        if summary and summary.is_file():
            try:
                data = json.loads(summary.read_text())
                effort = data.get("reasoning_effort")
                if effort is not None and str(effort) != "":
                    return str(effort)
            except Exception:
                pass
        time.sleep(0.05)
    return None


def mode_from_wire(effort: str | None) -> str:
    return WIRE_TO_MODE.get(effort or "", "normal")


if __name__ == "__main__":
    # tiny CLI for agents: python3 mode_state.py [status|lock|unlock] [session]
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    sid = sys.argv[2] if len(sys.argv) > 2 else current_session_id()
    if cmd == "status":
        print(json.dumps(load(sid), indent=2))
    elif cmd == "lock":
        mode = sys.argv[3] if len(sys.argv) > 3 else None
        lock(sid, mode)
        print(json.dumps(load(sid), indent=2))
    elif cmd == "unlock":
        print(json.dumps(unlock(sid), indent=2))
    elif cmd == "promote":
        print(json.dumps(promote_if_idle(sid), indent=2))
    else:
        print("usage: mode_state.py status|lock|unlock|promote [session_id] [mode]", file=sys.stderr)
        sys.exit(2)
