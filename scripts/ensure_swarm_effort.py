#!/usr/bin/env python3
"""Ensure the active Grok model exposes Agent Swarm in the effort selector.

Adds a menu option:
  id=swarm, label=Agent Swarm, wire value=xhigh

Wire value is xhigh so session state can distinguish swarm mode from ordinary
high effort (the stock menu is low/medium/high). Safe to re-run; idempotent.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

MARKER_BEGIN = "# --- agent-swarm effort (managed) ---"
MARKER_END = "# --- agent-swarm effort end ---"

SWARM_EFFORT = {
    "id": "swarm",
    "value": "xhigh",
    "label": "Agent Swarm",
    "description": (
        "Parallel multi-agent orchestration: decompose wide work, fan out "
        "subagents, synthesize one deliverable"
    ),
    "default": False,
}

STOCK = [
    {
        "id": "high",
        "value": "high",
        "label": "High Effort",
        "description": "Highest implementation quality with extensive reasoning",
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


def grok_home() -> Path:
    return Path(os.environ.get("GROK_HOME", Path.home() / ".grok"))


def detect_default_model(cfg_text: str) -> str:
    m = re.search(r'(?m)^\s*default\s*=\s*"([^"]+)"\s*$', cfg_text)
    if m and m.group(1).strip():
        return m.group(1).strip()
    # Prefer live catalog if present
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
    # Quote always so dotted ids (grok-4.5) parse as a single key.
    return f'model."{model_id}"'


def effort_block(model_id: str) -> str:
    key = model_table_key(model_id)
    lines = [
        MARKER_BEGIN,
        f"# Injected by agent-swarm plugin. Do not hand-edit between markers.",
        f"[{key}]",
        "supports_reasoning_effort = true",
        "",
    ]
    for e in STOCK + [SWARM_EFFORT]:
        lines.append(f"[[{key}.reasoning_efforts]]")
        lines.append(f'id = "{e["id"]}"')
        lines.append(f'value = "{e["value"]}"')
        lines.append(f'label = "{e["label"]}"')
        lines.append(f'description = "{e["description"]}"')
        lines.append(f'default = {"true" if e["default"] else "false"}')
        lines.append("")
    lines.append(MARKER_END)
    return "\n".join(lines) + "\n"


def strip_managed(text: str) -> str:
    return re.sub(
        rf"\n?{re.escape(MARKER_BEGIN)}.*?{re.escape(MARKER_END)}\n?",
        "\n",
        text,
        flags=re.S,
    )


def already_has_swarm_for_model(text: str, model_id: str) -> bool:
    # Detect our managed block for this model
    if MARKER_BEGIN in text and f'model."{model_id}"' in text and 'id = "swarm"' in text:
        return True
    return False


def main() -> int:
    cfg_path = grok_home() / "config.toml"
    if not cfg_path.exists():
        cfg_path.write_text(
            f'[models]\ndefault = "grok-4.5"\ndefault_reasoning_effort = "high"\n\n'
        )

    original = cfg_path.read_text()
    # Drop legacy test markers from earlier installs
    cleaned = re.sub(
        r"\n# --- swarm effort test start ---.*?# --- swarm effort test end ---\n?",
        "\n",
        original,
        flags=re.S,
    )
    cleaned = strip_managed(cleaned)
    model_id = detect_default_model(cleaned)

    # If user already has a non-managed swarm entry, leave alone
    if already_has_swarm_for_model(original, model_id) and MARKER_BEGIN in original:
        # Still rewrite managed block to keep it current
        pass

    new_text = cleaned.rstrip() + "\n\n" + effort_block(model_id)
    if new_text != original:
        cfg_path.write_text(new_text)
        status = "updated"
    else:
        status = "unchanged"

    # Machine-readable one-liner for logs; human-friendly on stderr
    print(
        json.dumps(
            {
                "status": status,
                "model": model_id,
                "effort_id": "swarm",
                "wire_value": "xhigh",
                "config": str(cfg_path),
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
