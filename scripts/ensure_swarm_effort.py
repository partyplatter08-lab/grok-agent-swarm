#!/usr/bin/env python3
"""Register effort-selector modes + install primary agents.

Menu order (top → bottom):
  1. Swarm Heavy  — collaborative council + K3-style swarm fan-out
  2. Agent Swarm  — K3-style parallel map/reduce
  3. Heavy        — Grok Heavy-style collaborative multi-agent debate
  4. High Effort  — stock default
  5. Medium Effort
  6. Low Effort

Also installs ~/.grok/agents/{swarm,heavy,swarm-heavy}.md and a SessionStart
hook that re-runs this script so the menu stays healthy.

Idempotent.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

MARKER_BEGIN = "# --- agent-swarm effort (managed) ---"
MARKER_END = "# --- agent-swarm effort end ---"
MODEL_MARKER_BEGIN = "# --- agent-swarm model (managed) ---"
MODEL_MARKER_END = "# --- agent-swarm model end ---"

# Display order = list order. Special modes first (above High).
# Wire values must be API-valid: low|medium|high|xhigh|max (max≡xhigh).
# Special modes share xhigh so they get maximum reasoning; differentiation
# is via the matching primary agent (/agents or --agent).
EFFORTS = [
    {
        "id": "swarm-heavy",
        "value": "xhigh",
        "label": "Swarm Heavy",
        "description": (
            "Collaborative multi-agent council + K3-style parallel swarm "
            "fan-out — maximum depth and width"
        ),
        "default": False,
    },
    {
        "id": "swarm",
        "value": "xhigh",
        "label": "Agent Swarm",
        "description": (
            "K3-style parallel orchestration: decompose wide work, fan out "
            "subagents, synthesize one deliverable"
        ),
        "default": False,
    },
    {
        "id": "heavy",
        "value": "xhigh",
        "label": "Heavy",
        "description": (
            "Grok Heavy-style collaborative multi-agent debate: parallel "
            "hypotheses, cross-check, leader synthesis"
        ),
        "default": False,
    },
    {
        "id": "high",
        "value": "high",
        "label": "High Effort",
        "description": "Highest single-agent implementation quality with extensive reasoning",
        "default": True,
    },
    {
        "id": "medium",
        "value": "medium",
        "label": "Medium Effort",
        "description": "Balanced effort with standard implementation and testing",
        "default": False,
    },
    {
        "id": "low",
        "value": "low",
        "label": "Low Effort",
        "description": "Quick, fast implementations",
        "default": False,
    },
]

USER_AGENTS = ("swarm", "heavy", "swarm-heavy")


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
    text = re.sub(
        r"\n# --- swarm model test ---.*?# --- swarm model test end ---\n?",
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
    if not ensure.is_file():
        return "hooks_skipped"

    hooks_dir = grok_home() / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    hook_path = hooks_dir / "agent-swarm.json"

    payload = {
        "description": "Agent Swarm: keep effort-picker modes registered",
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
            ]
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
    cleaned = strip_orphaned_model_effort_blocks(cleaned, model_id)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).rstrip() + "\n"

    new_text = cleaned + "\n" + effort_block(model_id)
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
                "config_path": str(cfg_path),
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
