from __future__ import annotations

from typing import Any


def group_words_into_rows(words: list[dict[str, Any]], y_tolerance: float = 5) -> list[list[dict[str, Any]]]:
    """Group words into horizontal rows based on their top position."""
    if not words:
        return []

    words_by_top = sorted(words, key=lambda word: float(word.get("top", 0)))
    rows: list[list[dict[str, Any]]] = []
    current_row: list[dict[str, Any]] = []
    current_top: float | None = None

    for word in words_by_top:
        word_top = float(word.get("top", 0))

        if current_top is None:
            current_row = [word]
            current_top = word_top
            continue

        if abs(word_top - current_top) <= y_tolerance:
            current_row.append(word)
            current_top = (current_top + word_top) / 2
        else:
            rows.append(current_row)
            current_row = [word]
            current_top = word_top

    if current_row:
        rows.append(current_row)

    return rows


def sort_row_words(row: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort words left to right in a row."""
    return sorted(row, key=lambda word: float(word.get("x0", 0)))


def split_row_into_columns(
    row: list[dict[str, Any]], split_x: float
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split a row into left and right columns using a vertical split line."""
    left_words: list[dict[str, Any]] = []
    right_words: list[dict[str, Any]] = []

    for word in row:
        word_mid_x = (float(word.get("x0", 0)) + float(word.get("x1", 0))) / 2
        if word_mid_x < split_x:
            left_words.append(word)
        else:
            right_words.append(word)

    return left_words, right_words


def build_row_text(words: list[dict[str, Any]]) -> str:
    """Build a clean row string from ordered words."""
    return " ".join(str(word.get("text", "")).strip() for word in words if str(word.get("text", "")).strip()).strip()


def parse_fixture_rows(
    words: list[dict[str, Any]], section_bbox: tuple[float, float, float, float]
) -> list[dict[str, str]]:
    """Parse fixture words into simple left/right structured rows."""
    rows = group_words_into_rows(words)
    split_x = (section_bbox[0] + section_bbox[2]) / 2

    parsed_rows: list[dict[str, str]] = []

    for row in rows:
        sorted_row = sort_row_words(row)
        full_row_text = build_row_text(sorted_row)
        if not full_row_text:
            continue

        normalized = full_row_text.upper()
        if "FIXTURE" in normalized and "SYMBOL" in normalized:
            continue

        left_words, right_words = split_row_into_columns(sorted_row, split_x)
        left_text = build_row_text(left_words)
        right_text = build_row_text(right_words)

        if left_text:
            parsed_rows.append({"side": "left", "text": left_text})
        if right_text:
            parsed_rows.append({"side": "right", "text": right_text})

    return parsed_rows
