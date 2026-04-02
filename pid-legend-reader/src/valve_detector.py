from __future__ import annotations


def detect_candidate_valve_regions(page) -> list[dict]:
    """
    Return candidate valve regions for future automated valve detection.

    Current phase behavior:
    - Returns an empty list by default.
    - Supports manual candidate regions via page metadata for testing.
    """
    manual_regions = getattr(page, "manual_valve_regions", None)
    if isinstance(manual_regions, list):
        return manual_regions

    return []


def classify_valve_type(region: dict) -> str | None:
    """
    Classify a candidate valve region.

    Current phase behavior:
    - Reads a manual `type` value when provided.
    - Supports only BALL VALVE and BUTTERFLY VALVE.
    """
    raw_type = str(region.get("type", "")).strip().upper()
    if raw_type in {"BALL VALVE", "BUTTERFLY VALVE"}:
        return raw_type

    return None
