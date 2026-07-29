"""Resolve the locally cached QuantEcon lecture source."""

from __future__ import annotations

import os
from pathlib import Path


def default_repo_root() -> Path:
    override = os.environ.get("QUANTITATIVE_TRADING_QUANTECON_ROOT")
    if override:
        return Path(override).expanduser()
    cache_home = os.environ.get("XDG_CACHE_HOME")
    base = Path(cache_home).expanduser() if cache_home else Path.home() / ".cache"
    return base / "quantitative-trading" / "lecture-python.myst"
