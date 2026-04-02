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
    "COOLER",
    "SINK",
    "ELECTRIC",
    "FLOOR",
    "RECEPTOR",
    "EYEWASH",
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
        row_bottom = max(float(word.get("bottom", word.get("top", 0))) for word in row)
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

            parsed = split_tag_and_description(side_words)
            side_rows.append(
                {
                    "side": side,
                    "top": row_top,
                    "bottom": row_bottom,
                    "text": text,
                    "words": side_words,
                    "tag": parsed.get("tag"),
                    "description": parsed.get("description"),
                    "description_words": parsed.get("description_words") or [],
                    "tag_x0": parsed.get("tag_x0"),
                    "desc_x0": parsed.get("desc_x0"),
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


def split_tag_and_description(words: list[dict[str, Any]]) -> dict[str, Any]:
    """Detect the first probable tag in a side row and split description text."""
    if not words:
        return {"tag": None, "description": "", "description_words": [], "tag_x0": None, "desc_x0": None}

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
        all_text = normalize_space(" ".join(text for text in texts if text))
        desc_x0 = min(float(word.get("x0", 0)) for word in ordered)
        return {
            "tag": None,
            "description": all_text,
            "description_words": ordered,
            "tag_x0": None,
            "desc_x0": desc_x0,
        }

    tag_word = ordered[tag_index]
    description_words = ordered[tag_index + 1 :]
    description = normalize_space(" ".join(text for text in texts[tag_index + 1 :] if text))
    desc_x0: float | None = None
    if description_words:
        desc_x0 = float(description_words[0].get("x0", 0))

    return {
        "tag": tag_value,
        "description": description,
        "description_words": description_words,
        "tag_x0": float(tag_word.get("x0", 0)),
        "desc_x0": desc_x0,
    }


def sort_description_words(words: list[dict[str, Any]], line_tolerance: float = 5) -> list[dict[str, Any]]:
    """Sort words in natural reading order using line grouping, then left-to-right."""
    if not words:
        return []

    words_by_top = sorted(words, key=lambda word: float(word.get("top", 0)))
    lines: list[list[dict[str, Any]]] = []

    for word in words_by_top:
        word_top = float(word.get("top", 0))
        assigned = False

        for line in lines:
            line_avg_top = sum(float(item.get("top", 0)) for item in line) / len(line)
            if abs(word_top - line_avg_top) < line_tolerance:
                line.append(word)
                assigned = True
                break

        if not assigned:
            lines.append([word])

    lines.sort(key=lambda line: sum(float(item.get("top", 0)) for item in line) / len(line))

    ordered_words: list[dict[str, Any]] = []
    for line in lines:
        ordered_words.extend(sorted(line, key=lambda word: float(word.get("x0", 0))))

    return ordered_words


def build_description_from_words(words: list[dict[str, Any]]) -> str:
    """Build normalized description text from ordered word objects."""
    return normalize_space(
        " ".join(
            str(word.get("text", "")).strip()
            for word in words
            if str(word.get("text", "")).strip()
        )
    )


def is_continuation_row(
    previous_record: dict[str, str | float | None] | None,
    current_row: dict[str, Any],
    max_vertical_gap: float = 22,
    max_desc_x_delta: float = 35,
) -> bool:
    """Return True when current_row appears to continue previous_record description."""
    if current_row.get("tag") is not None:
        return False

    if previous_record is None:
        return False

    row_top = float(current_row.get("top", 0))
    previous_bottom = previous_record.get("last_bottom")
    if previous_bottom is None:
        return False

    vertical_gap = row_top - float(previous_bottom)
    if vertical_gap > max_vertical_gap:
        return False

    row_desc_x0 = current_row.get("desc_x0")
    previous_desc_x0 = previous_record.get("desc_x0")
    if row_desc_x0 is None or previous_desc_x0 is None:
        return False

    return abs(float(row_desc_x0) - float(previous_desc_x0)) <= max_desc_x_delta


def merge_continuation_rows(side_rows: list[dict[str, Any]]) -> list[dict[str, str | None]]:
    """Merge rows for one side, appending only validated continuation rows."""
    records: list[dict[str, str | None]] = []
    current_record: dict[str, str | float | None] | None = None

    sorted_rows = sorted(side_rows, key=lambda item: float(item.get("top", 0)))

    for row in sorted_rows:
        tag = row.get("tag")
        description = normalize_space(str(row.get("description") or ""))

        if tag:
            if current_record:
                ordered_words = sort_description_words(list(current_record.get("description_words") or []))
                if ordered_words:
                    current_record["description"] = build_description_from_words(ordered_words)
                else:
                    current_record["description"] = normalize_space(str(current_record.get("description") or ""))
                records.append(
                    {
                        "side": str(current_record.get("side") or ""),
                        "tag": str(current_record.get("tag") or ""),
                        "description": str(current_record.get("description") or ""),
                    }
                )

            current_record = {
                "side": str(row.get("side") or ""),
                "tag": str(tag),
                "description": description,
                "description_words": list(row.get("description_words") or []),
                "desc_x0": row.get("desc_x0"),
                "last_bottom": float(row.get("bottom", row.get("top", 0))),
            }
            continue

        if is_continuation_row(current_record, row):
            assert current_record is not None
            description_words = list(current_record.get("description_words") or [])
            description_words.extend(list(row.get("description_words") or []))
            current_record["description_words"] = description_words
            ordered_words = sort_description_words(description_words)
            current_record["description"] = build_description_from_words(ordered_words)
            current_record["last_bottom"] = float(row.get("bottom", row.get("top", 0)))

    if current_record:
        ordered_words = sort_description_words(list(current_record.get("description_words") or []))
        if ordered_words:
            current_record["description"] = build_description_from_words(ordered_words)
        else:
            current_record["description"] = normalize_space(str(current_record.get("description") or ""))
        records.append(
            {
                "side": str(current_record.get("side") or ""),
                "tag": str(current_record.get("tag") or ""),
                "description": str(current_record.get("description") or ""),
            }
        )

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
