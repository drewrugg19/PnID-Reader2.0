from __future__ import annotations

from pathlib import Path


def log(message: str) -> None:
    """Simple logging wrapper."""
    print(f"[pid-legend-reader] {message}")


def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent


def input_path(filename: str) -> Path:
    """Build a path to a file in data/input."""
    return project_root() / "data" / "input" / filename
