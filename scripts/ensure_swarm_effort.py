#!/usr/bin/env python3
"""Seamless multi-agent efforts: menu + deferred mode switch + modes agent.

Effort selector (top → bottom):
  Swarm Heavy  → wire xhigh   → mode swarm-heavy
  Agent Swarm  → wire none    → mode swarm
  Heavy        → wire minimal → mode heavy
  High/Med/Low → stock        → mode normal

Effort changes behave like normal effort:
  - desired mode updates immediately
  - active mode switches after the current multi-agent pipeline unlocks
    (workers finish; orchestrator completes; next user turn / Stop promote)

Installs:
  - effort menu + [agent] name = modes
  - agents: modes, heavy, swarm, swarm-heavy
  - hooks: SessionStart, UserPromptSubmit (inject_mode), Stop (promote)
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

MARKER_BEGIN = "# --- agent-swarm effort (managed) ---"
MARKER_END = "# --- agent-swarm effort end ---"
AGENT_MARKER_BEGIN = "# --- agent-swarm agent (managed) ---"
AGENT_MARKER_END = "# --- agent-swarm agent end ---"
MODEL_MARKER_BEGIN = "# --- agent-swarm model (managed) ---"
MODEL_MARKER_END = "# --- agent-swarm model end ---"

# Unique wire values so inject_mode can detect which menu item was selected.
# xhigh = max reasoning (Swarm Heavy). minimal/none are API-valid and distinct;
# multi-agent structure compensates for lower sampling effort on those modes.
EFFORTS = [
    {
        "id": "swarm-heavy",
        "value": "xhigh",
        "label": "Swarm Heavy",
        "description": (
            "Full Swarm Heavy mode: collaborative council + K3-style parallel "
            "fan-out + verify (same as /swarm-heavy)"
        ),
        "default": False,
    },
    {
        "id": "swarm",
        "value": "none",
        "label": "Agent Swarm",
        "description": (
            "Full Agent Swarm mode: decompose, parallel subagents, synthesize "
            "(same as /swarm)"
        ),
        "default": False,
    },
    {
        "id": "heavy",
        "value": "minimal",
        "label": "Heavy",
        "description": (
            "Full Heavy mode: collaborative multi-agent council + leader "
            "synthesis (same as /heavy)"
        ),
        "default": False,
    },
    {
        "id": "high",
        "value": "high",
        "label": "High Effort",
        "description": "Single-agent, high reasoning",
        "default": True,
    },
    {
        "id": "medium",
        "value": "medium",
        "label": "Medium Effort",
        "description": "Single-agent, balanced",
        "default": False,
    },
    {
        "id": "low",
        "value": "low",
        "label": "Low Effort",
        "description": "Single-agent, fast",
        "default": False,
    },
]

USER_AGENTS = ("modes", "swarm", "heavy", "swarm-heavy")


def grok_home() -> Path:
    return Path(os.environ.get("GROK_HOME", Path.home() / ".grok"))


def plugin_root() -> Path:
    env = os.environ.get("GROK_PLUGIN_ROOT") or os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env:
        return Path(env)
    return Path(__file__).resolve().parent.parent


def detect_default_model(cfg_text: str) -> str:
    m = re.search(r'(?m)^\s*default\s*=\s*"([^"]+)"\s*$', cfg_text)
    if m and m.group(1).strip():
        return m.group(1).strip()
    cache = grok_home() / "models_cache.json"
    if cache.is_file():
        try:
            data = json.loads(cache.read_text())
            models = data.get("models") or {}
            if "grok-4.5" in models:
                return "grok-4.5"
            if models:
                return next(iter(models.keys()))
        except Exception:
            pass
    return "grok-4.5"


def model_table_key(model_id: str) -> str:
    return f'model."{model_id}"'


def effort_block(model_id: str) -> str:
    key = model_table_key(model_id)
    lines = [
        MARKER_BEGIN,
        "# Injected by agent-swarm plugin. Do not hand-edit between markers.",
        "# Order: Swarm Heavy → Agent Swarm → Heavy → High → Medium → Low",
        "# Wires: xhigh | none | minimal | high | medium | low (unique for mode detect)",
        f"[{key}]",
        "supports_reasoning_effort = true",
        "",
    ]
    for e in EFFORTS:
        lines.append(f"[[{key}.reasoning_efforts]]")
        lines.append(f'id = "{e["id"]}"')
        lines.append(f'value = "{e["value"]}"')
        lines.append(f'label = "{e["label"]}"')
        lines.append(f'description = "{e["description"]}"')
        lines.append(f'default = {"true" if e["default"] else "false"}')
        lines.append("")
    lines.append(MARKER_END)
    return "\n".join(lines) + "\n"


def agent_block() -> str:
    return "\n".join(
        [
            AGENT_MARKER_BEGIN,
            '# Default agent is mode-aware: effort picker activates full /heavy|/swarm|/swarm-heavy protocols.',
            "[agent]",
            'name = "modes"',
            AGENT_MARKER_END,
            "",
        ]
    )


def strip_between(text: str, begin: str, end: str) -> str:
    return re.sub(
        rf"\n?{re.escape(begin)}.*?{re.escape(end)}\n?",
        "\n",
        text,
        flags=re.S,
    )


def strip_orphaned_model_effort_blocks(text: str, model_id: str) -> str:
    key = re.escape(model_table_key(model_id))
    text = re.sub(
        rf"\n*\[\[{key}\.reasoning_efforts\]\][^\[]*",
        "\n",
        text,
        flags=re.S,
    )
    text = re.sub(
        rf"\n*\[{key}\]\n(?:supports_reasoning_effort\s*=\s*true\n)?(?:\n)*",
        "\n",
        text,
    )
    text = re.sub(
        r"\n# --- swarm effort test start ---.*?# --- swarm effort test end ---\n?",
        "\n",
        text,
        flags=re.S,
    )
    text = strip_between(text, MODEL_MARKER_BEGIN, MODEL_MARKER_END)
    return text


def install_user_agents() -> dict[str, str]:
    results: dict[str, str] = {}
    dest_dir = grok_home() / "agents"
    dest_dir.mkdir(parents=True, exist_ok=True)
    root = plugin_root()
    for name in USER_AGENTS:
        src = root / "agents" / f"{name}.md"
        if not src.is_file():
            results[name] = "missing"
            continue
        dest = dest_dir / f"{name}.md"
        body = src.read_text()
        if dest.is_file() and dest.read_text() == body:
            results[name] = "unchanged"
        else:
            dest.write_text(body)
            results[name] = "updated"
    return results


def install_global_hooks() -> str:
    root = plugin_root().resolve()
    ensure = root / "scripts" / "ensure_swarm_effort.py"
    inject = root / "scripts" / "inject_mode.py"
    on_stop = root / "scripts" / "on_stop.py"
    if not ensure.is_file() or not inject.is_file() or not on_stop.is_file():
        return "hooks_skipped"

    hooks_dir = grok_home() / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path = hooks_dir / "agent-swarm.json"

    # Point GROK_PLUGIN_ROOT at the *installed* copy when possible so reloads
    # don't depend on a dev checkout path.
    payload = {
        "description": "Agent Swarm: seamless effort→mode with deferred switch",
        "hooks": {
            "SessionStart": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": (
                                f'env AGENT_SWARM_ENSURING=1 GROK_PLUGIN_ROOT="{root}" '
                                f'python3 "{ensure}"'
                            ),
                            "timeout": 15,
                        }
                    ]
                }
            ],
            "UserPromptSubmit": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": (
                                f'env GROK_PLUGIN_ROOT="{root}" '
                                f'python3 "{inject}"'
                            ),
                            "timeout": 10,
                        }
                    ]
                }
            ],
            "Stop": [
                {
                    "hooks": [
                        {
                            "type": "command",
                            "command": (
                                f'env GROK_PLUGIN_ROOT="{root}" '
                                f'python3 "{on_stop}"'
                            ),
                            "timeout": 10,
                        }
                    ]
                }
            ],
        },
    }
    new = json.dumps(payload, indent=2) + "\n"
    old = hook_path.read_text() if hook_path.is_file() else None
    if old != new:
        hook_path.write_text(new)
        return "hooks_updated"
    return "hooks_unchanged"


def main() -> int:
    cfg_path = grok_home() / "config.toml"
    if not cfg_path.exists():
        cfg_path.write_text(
            '[models]\ndefault = "grok-4.5"\ndefault_reasoning_effort = "high"\n\n'
        )

    original = cfg_path.read_text()
    model_id = detect_default_model(original)
    cleaned = strip_between(original, MARKER_BEGIN, MARKER_END)
    cleaned = strip_between(cleaned, AGENT_MARKER_BEGIN, AGENT_MARKER_END)
    cleaned = strip_orphaned_model_effort_blocks(cleaned, model_id)
    # Remove any prior unmanaged [agent] name = modes we own
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).rstrip() + "\n"

    new_text = cleaned + "\n" + effort_block(model_id) + "\n" + agent_block()
    cfg_status = "unchanged"
    if new_text != original:
        cfg_path.write_text(new_text)
        cfg_status = "updated"

    agent_status = install_user_agents()
    hooks_status = (
        "skipped_nested"
        if os.environ.get("AGENT_SWARM_ENSURING") == "1"
        else install_global_hooks()
    )

    print(
        json.dumps(
            {
                "config": cfg_status,
                "agents": agent_status,
                "hooks": hooks_status,
                "model": model_id,
                "effort_order": [e["id"] for e in EFFORTS],
                "default_agent": "modes",
                "config_path": str(cfg_path),
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
