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
    return normalize_space(
        " ".join(
            str(word.get("text", "")).strip()
            for word in words
            if str(word.get("text", "")).strip()
        )
    )


def group_words_into_rows(words: list[dict[str, Any]], y_tolerance: float = 5) -> list[list[dict[str, Any]]]:
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


def is_probable_tag(text: str) -> bool:
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


def group_description_words_into_lines(words: list[dict[str, Any]], y_tolerance: float = 5) -> list[list[dict[str, Any]]]:
    if not words:
        return []

    words_by_top = sorted(words, key=lambda word: float(word.get("top", 0)))
    lines: list[list[dict[str, Any]]] = []

    for word in words_by_top:
        word_top = float(word.get("top", 0))
        assigned = False

        for line in lines:
            line_avg_top = sum(float(item.get("top", 0)) for item in line) / len(line)
            if abs(word_top - line_avg_top) <= y_tolerance:
                line.append(word)
                assigned = True
                break

        if not assigned:
            lines.append([word])

    lines.sort(key=lambda line: sum(float(item.get("top", 0)) for item in line) / len(line))
    for line in lines:
        line.sort(key=lambda word: float(word.get("x0", 0)))

    return lines


def build_description_from_words(words: list[dict[str, Any]]) -> str:
    lines = group_description_words_into_lines(words)
    line_texts: list[str] = []

    for line in lines:
        text = normalize_space(
            " ".join(
                str(word.get("text", "")).strip()
                for word in line
                if str(word.get("text", "")).strip()
            )
        )
        if text:
            line_texts.append(text)

    return normalize_space(" ".join(line_texts))


def split_row_by_cluster_gap(
    row_words: list[dict[str, Any]],
    min_gap: float = 14,
    relative_gap_factor: float = 1.6,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    ordered = sorted(row_words, key=lambda word: float(word.get("x0", 0)))
    if len(ordered) <= 1:
        return ordered, []

    gaps: list[float] = []
    for i in range(len(ordered) - 1):
        left = ordered[i]
        right = ordered[i + 1]
        gap = float(right.get("x0", 0)) - float(left.get("x1", left.get("x0", 0)))
        gaps.append(max(0.0, gap))

    positive_gaps = [gap for gap in gaps if gap > 0]
    typical_gap = (sum(positive_gaps) / len(positive_gaps)) if positive_gaps else 0.0

    best_index = -1
    best_gap = -1.0
    threshold = max(min_gap, typical_gap * relative_gap_factor)
    for index, gap in enumerate(gaps):
        if gap >= threshold and gap > best_gap:
            best_gap = gap
            best_index = index

    if best_index == -1:
        return ordered, []

    left_words = ordered[: best_index + 1]
    right_words = ordered[best_index + 1 :]
    return left_words, right_words


def build_section_row_objects(
    words: list[dict[str, Any]],
    section_bbox: tuple[float, float, float, float] | None,
    section_type: str,
    header_cutoff: float = 40,
) -> list[dict[str, Any]]:
    section = normalize_space(section_type).lower()
    grouped_rows = group_words_into_rows(words)
    row_objects: list[dict[str, Any]] = []

    for row in grouped_rows:
        if not row:
            continue

        ordered_row = sorted(row, key=lambda w: float(w.get("x0", 0)))
        row_top = min(float(word.get("top", 0)) for word in ordered_row)
        row_bottom = max(float(word.get("bottom", word.get("top", 0))) for word in ordered_row)

        if row_top <= header_cutoff:
            continue

        row_text_upper = build_row_text(ordered_row).upper()
        if "FIXTURE" in row_text_upper and "SYMBOL" in row_text_upper:
            continue

        left_words, right_words = split_row_by_cluster_gap(ordered_row)

        left_text = normalize_space(build_row_text(left_words))
        right_text = normalize_space(build_row_text(right_words))

        left_x0 = min((float(word.get("x0", 0)) for word in left_words), default=None)
        right_x0 = min((float(word.get("x0", 0)) for word in right_words), default=None)

        if not left_text and not right_text:
            continue

        row_objects.append(
            {
                "section": section,
                "top": row_top,
                "bottom": row_bottom,
                "left_words": left_words,
                "right_words": right_words,
                "left_text": left_text,
                "right_text": right_text,
                "left_x0": left_x0,
                "right_x0": right_x0,
                "bbox": section_bbox,
            }
        )

    row_objects.sort(key=lambda item: float(item.get("top", 0)))
    return row_objects


def merge_section_continuations(
    row_objects: list[dict[str, Any]], max_vertical_gap: float = 20, max_x_delta: float = 35
) -> list[dict[str, str]]:
    records: list[dict[str, str]] = []
    current: dict[str, Any] | None = None

    for row in sorted(row_objects, key=lambda item: float(item.get("top", 0))):
        left_text = normalize_space(str(row.get("left_text") or ""))
        right_text = normalize_space(str(row.get("right_text") or ""))

        if left_text and right_text:
            if current and current.get("left") and current.get("right"):
                records.append(
                    {
                        "left": normalize_space(str(current.get("left") or "")),
                        "right": normalize_space(str(current.get("right") or "")),
                    }
                )

            current = {
                "left": left_text,
                "right": right_text,
                "bottom": float(row.get("bottom", row.get("top", 0))),
                "right_x0": row.get("right_x0"),
            }
            continue

        is_right_only = bool(right_text) and not left_text
        if not is_right_only or current is None:
            continue

        prev_bottom = float(current.get("bottom", 0))
        row_top = float(row.get("top", 0))
        vertical_gap = row_top - prev_bottom
        if vertical_gap > max_vertical_gap:
            continue

        row_right_x0 = row.get("right_x0")
        prev_right_x0 = current.get("right_x0")
        if row_right_x0 is None or prev_right_x0 is None:
            continue

        if abs(float(row_right_x0) - float(prev_right_x0)) > max_x_delta:
            continue

        current["right"] = normalize_space(f"{current.get('right', '')} {right_text}")
        current["bottom"] = float(row.get("bottom", row.get("top", 0)))

    if current and current.get("left") and current.get("right"):
        records.append(
            {
                "left": normalize_space(str(current.get("left") or "")),
                "right": normalize_space(str(current.get("right") or "")),
            }
        )

    return [record for record in records if record["left"] and record["right"]]


def parse_section(
    words: list[dict[str, Any]],
    section_type: str,
    section_bbox: tuple[float, float, float, float] | None = None,
) -> list[dict[str, str]]:
    normalized_section = normalize_space(section_type).lower()
    if normalized_section not in {"fixture", "piping", "valve"}:
        return []

    row_objects = build_section_row_objects(words, section_bbox, normalized_section)

    if normalized_section in {"piping", "valve"}:
        print(f"\n--- {normalized_section.upper()} ROW OBJECTS ---\n")
        for row in row_objects:
            print(f'LEFT: "{row.get("left_text", "")}"')
            print(f'RIGHT: "{row.get("right_text", "")}"')
        if not row_objects:
            print("(no row objects)")

    records = merge_section_continuations(row_objects)

    return [{"left": record["left"], "right": record["right"], "section": normalized_section} for record in records]


def parse_fixture_records(
    words: list[dict[str, Any]], section_bbox: tuple[float, float, float, float]
) -> list[dict[str, str | None]]:
    row_objects = build_section_row_objects(words, section_bbox, "fixture")
    records = merge_section_continuations(row_objects)

    fixture_records: list[dict[str, str | None]] = []
    for record in records:
        parsed = split_tag_and_description(
            [{"text": token, "x0": i} for i, token in enumerate(record["left"].split())]
        )
        tag = parsed.get("tag") or record["left"]
        desc = record["right"]
        fixture_records.append({"side": "left", "tag": normalize_space(str(tag)), "description": normalize_space(desc)})

    return fixture_records
