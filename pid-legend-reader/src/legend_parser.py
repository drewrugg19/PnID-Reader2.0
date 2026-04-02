from __future__ import annotations

import re
from typing import Any


TAG_BLACKLIST = {
    "WALL",
    "MOUNTED",
    "KITCHEN",
    "DOUBLE",
    "FIXTURE",
    "SYMBOLS",
    "WATER",
    "CLOSET",
    "LAVATORY",
}


def normalize_space(text: str) -> str:
    return " ".join(text.split()).strip()


def build_row_text(words: list[dict[str, Any]]) -> str:
    """Build a clean row string from ordered words."""
    return normalize_space(
        " ".join(
            str(word.get("text", "")).strip()
            for word in words
            if str(word.get("text", "")).strip()
        )
    )


def group_words_into_rows(words: list[dict[str, Any]], y_tolerance: float = 5) -> list[list[dict[str, Any]]]:
    """Group words into horizontal rows by similar top values."""
    if not words:
        return []

    words_by_top = sorted(words, key=lambda word: float(word.get("top", 0)))
    grouped_rows: list[list[dict[str, Any]]] = []
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
            grouped_rows.append(sorted(current_row, key=lambda w: float(w.get("x0", 0))))
            current_row = [word]
            current_top = word_top

    if current_row:
        grouped_rows.append(sorted(current_row, key=lambda w: float(w.get("x0", 0))))

    grouped_rows.sort(key=lambda row: min(float(word.get("top", 0)) for word in row))
    return grouped_rows


def split_words_by_side(words: list[dict[str, Any]], split_x: float) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Split word objects into left and right lists using split_x."""
    left_words: list[dict[str, Any]] = []
    right_words: list[dict[str, Any]] = []

    for word in words:
        word_mid_x = (float(word.get("x0", 0)) + float(word.get("x1", 0))) / 2
        if word_mid_x < split_x:
            left_words.append(word)
        else:
            right_words.append(word)

    left_words.sort(key=lambda w: float(w.get("x0", 0)))
    right_words.sort(key=lambda w: float(w.get("x0", 0)))
    return left_words, right_words


def build_side_row_objects(
    grouped_rows: list[list[dict[str, Any]]], split_x: float, header_cutoff: float = 40
) -> list[dict[str, Any]]:
    """Build structured side row objects from grouped rows."""
    side_rows: list[dict[str, Any]] = []

    for row in grouped_rows:
        if not row:
            continue

        row_top = min(float(word.get("top", 0)) for word in row)
        if row_top <= header_cutoff:
            continue

        left_words, right_words = split_words_by_side(row, split_x)

        for side, side_words in (("left", left_words), ("right", right_words)):
            if not side_words:
                continue

            text = build_row_text(side_words)
            if not text:
                continue

            normalized = text.upper()
            if "FIXTURE" in normalized and "SYMBOL" in normalized:
                continue

            side_rows.append(
                {
                    "side": side,
                    "top": row_top,
                    "words": side_words,
                    "text": text,
                }
            )

    side_rows.sort(key=lambda item: float(item.get("top", 0)))
    return side_rows


def is_probable_tag(text: str) -> bool:
    """Return True when text looks like a fixture code/tag."""
    cleaned = normalize_space(text)
    if not cleaned:
        return False

    if " " in cleaned or "," in cleaned:
        return False

    if len(cleaned) < 2 or len(cleaned) > 8:
        return False

    if cleaned.upper() in TAG_BLACKLIST:
        return False

    if sum(1 for char in cleaned if char.islower()) / len(cleaned) > 0.7:
        return False

    if cleaned != cleaned.upper():
        return False

    if not re.fullmatch(r"[A-Z0-9.-]+", cleaned):
        return False

    letter_count = sum(1 for char in cleaned if char.isalpha())
    if letter_count == 0:
        return False

    if letter_count / len(cleaned) < 0.6:
        return False

    return True


def split_tag_and_description(words: list[dict[str, Any]]) -> dict[str, str | None]:
    """Detect the first probable tag in a side row and split description text."""
    if not words:
        return {"tag": None, "description": ""}

    ordered = sorted(words, key=lambda w: float(w.get("x0", 0)))
    texts = [normalize_space(str(word.get("text", ""))) for word in ordered]

    tag_index: int | None = None
    tag_value: str | None = None

    for index, token in enumerate(texts):
        if is_probable_tag(token):
            tag_index = index
            tag_value = token
            break

    if tag_index is None:
        return {
            "tag": None,
            "description": normalize_space(" ".join(text for text in texts if text)),
        }

    description = normalize_space(" ".join(text for text in texts[tag_index + 1 :] if text))
    return {
        "tag": tag_value,
        "description": description,
    }


def merge_continuation_rows(side_rows: list[dict[str, Any]]) -> list[dict[str, str | None]]:
    """Merge rows for one side, appending untagged rows as continuation text."""
    records: list[dict[str, str | None]] = []
    current_record: dict[str, str | None] | None = None

    sorted_rows = sorted(side_rows, key=lambda item: float(item.get("top", 0)))

    for row in sorted_rows:
        row_side = str(row.get("side", "")).lower()
        row_words = row.get("words", [])
        parsed = split_tag_and_description(row_words)
        tag = parsed.get("tag")
        description = normalize_space(str(parsed.get("description") or ""))

        if tag:
            if current_record:
                current_record["description"] = normalize_space(str(current_record.get("description") or ""))
                records.append(current_record)

            current_record = {
                "side": row_side,
                "tag": str(tag),
                "description": description,
            }
            continue

        if current_record and description:
            current_description = normalize_space(str(current_record.get("description") or ""))
            current_record["description"] = normalize_space(f"{current_description} {description}")

    if current_record:
        current_record["description"] = normalize_space(str(current_record.get("description") or ""))
        records.append(current_record)

    return records


def parse_fixture_records(
    words: list[dict[str, Any]], section_bbox: tuple[float, float, float, float]
) -> list[dict[str, str | None]]:
    """Parse fixture words into final side/tag/description records."""
    grouped_rows = group_words_into_rows(words)
    split_x = (section_bbox[0] + section_bbox[2]) / 2

    side_rows = build_side_row_objects(grouped_rows, split_x)
    left_rows = [row for row in side_rows if row.get("side") == "left"]
    right_rows = [row for row in side_rows if row.get("side") == "right"]

    fixture_records = merge_continuation_rows(left_rows)
    fixture_records.extend(merge_continuation_rows(right_rows))
    return fixture_records
