#!/usr/bin/env python3
"""Inject a bounded graph brief at session start when the project has kg/."""

from __future__ import annotations

import json
from pathlib import Path
import sys


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN_ROOT))

from lib.kg_bridge import GraphBridgeError, build_session_brief, find_project_root  # noqa: E402


def main():
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        payload = {}
    cwd = payload.get("cwd") if isinstance(payload, dict) else None
    try:
        root = find_project_root(cwd if isinstance(cwd, str) else None)
        print(build_session_brief(root))
    except GraphBridgeError:
        # Projects without a graph should start normally and receive no extra context.
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
