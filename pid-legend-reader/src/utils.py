from __future__ import annotations

from pathlib import Path


def ensure_directory(path: str) -> None:
    """Create a directory if it does not exist."""
    Path(path).mkdir(parents=True, exist_ok=True)


def log_step(message: str) -> None:
    """Print a clear step message for debugging."""
    print(f"[STEP] {message}")
