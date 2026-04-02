from __future__ import annotations

import re

from pdf_reader import filter_words_in_region
from section_config import get_section_settings


def _segment_length(segment: dict) -> float:
    if segment.get("orientation") == "vertical":
        return float(segment.get("bottom", 0.0)) - float(segment.get("top", 0.0))
    return float(segment.get("x1", 0.0)) - float(segment.get("x0", 0.0))


def _spans_anchor_band_vertical(segment: dict, anchor_top: float, anchor_bottom: float) -> bool:
    seg_top = float(segment.get("top", 0.0))
    seg_bottom = float(segment.get("bottom", 0.0))
    return seg_top <= anchor_top + 2.0 and seg_bottom >= anchor_bottom - 2.0


def _normalize_text(value: str) -> str:
    raw = str(value).upper()
    stripped = re.sub(r"[^A-Z0-9\s]", " ", raw)
    return " ".join(stripped.split())


def _normalize_token(token: str) -> str:
    cleaned = re.sub(r"[^A-Z0-9]", "", str(token).upper())
    if cleaned.endswith("S") and len(cleaned) > 1:
        cleaned = cleaned[:-1]
    return cleaned


def _tokenize(value: str) -> list[str]:
    normalized = _normalize_text(value)
    if not normalized:
        return []
    return [tok for tok in (_normalize_token(part) for part in normalized.split()) if tok]


def _is_heading_match(candidate_text: str, target_text: str) -> bool:
    target_tokens = set(_tokenize(target_text))
    candidate_tokens = set(_tokenize(candidate_text))
    if not target_tokens or not candidate_tokens:
        return False
    return target_tokens.issubset(candidate_tokens)


def _build_line_phrases(words: list[dict]) -> list[dict]:
    words_by_top = sorted(words, key=lambda word: (float(word.get("top", 0.0)), float(word.get("x0", 0.0))))
    if not words_by_top:
        return []

    lines: list[list[dict]] = []
    for word in words_by_top:
        if not lines:
            lines.append([word])
            continue

        current_top = float(word.get("top", 0.0))
        last_line = lines[-1]
        avg_top = sum(float(item.get("top", 0.0)) for item in last_line) / len(last_line)
        if abs(current_top - avg_top) <= 8.0:
            last_line.append(word)
        else:
            lines.append([word])

    phrases: list[dict] = []
    for line in lines:
        ordered = sorted(line, key=lambda item: float(item.get("x0", 0.0)))
        for start in range(len(ordered)):
            phrase_words = [ordered[start]]
            for end in range(start, len(ordered)):
                if end > start:
                    gap = float(ordered[end].get("x0", 0.0)) - float(ordered[end - 1].get("x1", 0.0))
                    if gap > 140.0:
                        break
                    phrase_words.append(ordered[end])

                phrase_text = " ".join(str(item.get("text", "")) for item in phrase_words)
                phrases.append(
                    {
                        "text": phrase_text,
                        "x0": min(float(item.get("x0", 0.0)) for item in phrase_words),
                        "x1": max(float(item.get("x1", 0.0)) for item in phrase_words),
                        "top": min(float(item.get("top", 0.0)) for item in phrase_words),
                        "bottom": max(float(item.get("bottom", 0.0)) for item in phrase_words),
                    }
                )

    return phrases


def _build_heading_candidates(words: list[dict]) -> list[dict]:
    candidates: list[dict] = []

    for word in words:
        text = str(word.get("text", "")).strip()
        if not text:
            continue
        candidates.append(
            {
                "text": text,
                "x0": float(word.get("x0", 0.0)),
                "x1": float(word.get("x1", 0.0)),
                "top": float(word.get("top", 0.0)),
                "bottom": float(word.get("bottom", 0.0)),
            }
        )

    for phrase in _build_line_phrases(words):
        text = str(phrase.get("text", "")).strip()
        if not text:
            continue
        candidates.append(
            {
                "text": text,
                "x0": float(phrase.get("x0", 0.0)),
                "x1": float(phrase.get("x1", 0.0)),
                "top": float(phrase.get("top", 0.0)),
                "bottom": float(phrase.get("bottom", 0.0)),
            }
        )

    return candidates


def find_section_anchor_record(words, section_key: str, target_label: str):
    """
    Find heading anchor coordinates for a section title and return a full section record.
    """
    if not words:
        return None

    target_tokens = set(_tokenize(target_label))
    if not target_tokens:
        return None

    best_match: dict | None = None
    best_score: tuple[float, float, float] | None = None

    for candidate in _build_heading_candidates(words):
        candidate_text = str(candidate.get("text", ""))
        if not _is_heading_match(candidate_text, target_label):
            continue

        candidate_tokens = set(_tokenize(candidate_text))
        extra_tokens = len(candidate_tokens - target_tokens)
        width = float(candidate.get("x1", 0.0)) - float(candidate.get("x0", 0.0))
        top = float(candidate.get("top", 0.0))
        score = (float(extra_tokens), width, top)

        if best_score is None or score < best_score:
            best_match = candidate
            best_score = score

    if best_match is None:
        return None

    anchor = {
        "x0": float(best_match["x0"]),
        "top": float(best_match["top"]),
        "x1": float(best_match["x1"]),
        "bottom": float(best_match["bottom"]),
    }

    return {
        "section_key": section_key,
        "target_label": target_label,
        "matched_text": str(best_match.get("text", "")),
        "anchor": anchor,
    }


def find_section_anchor(words, target_text):
    """Backward-compatible anchor finder returning only anchor bbox."""
    record = find_section_anchor_record(words, target_text, target_text)
    if record is None:
        return None
    return record.get("anchor")


def filter_words_between_xbounds(words, x0, x1, top=None, bottom=None):
    """Keep words that fit inside table x-bounds and optional y-bounds."""
    return filter_words_in_region(words, x0=x0, x1=x1, top=top, bottom=bottom)


def _find_nearby_table_lines(anchor, line_segments, page_width, page_height, section_name: str):
    settings = get_section_settings(section_name)
    padding = settings["anchor_padding"]

    anchor_x0 = float(anchor["x0"])
    anchor_x1 = float(anchor["x1"])
    anchor_top = float(anchor["top"])
    anchor_bottom = float(anchor["bottom"])

    local_x0 = max(0.0, anchor_x0 - padding["left"])
    local_x1 = min(float(page_width), anchor_x1 + padding["right"])
    local_top = max(0.0, anchor_top - padding["top"])
    local_bottom = min(float(page_height), anchor_bottom + padding["bottom"])

    local_segments = []
    for seg in line_segments:
        sx0 = float(seg.get("x0", 0.0))
        sx1 = float(seg.get("x1", 0.0))
        stop = float(seg.get("top", 0.0))
        sbottom = float(seg.get("bottom", 0.0))

        overlaps_local = not (
            sx1 < local_x0 or sx0 > local_x1 or sbottom < local_top or stop > local_bottom
        )
        if overlaps_local:
            local_segments.append(seg)

    verticals = [
        seg
        for seg in local_segments
        if seg.get("orientation") == "vertical" and _segment_length(seg) >= 30.0
    ]
    horizontals = [
        seg
        for seg in local_segments
        if seg.get("orientation") == "horizontal" and _segment_length(seg) >= 40.0
    ]

    verticals_near_anchor_band = [
        seg
        for seg in verticals
        if _spans_anchor_band_vertical(seg, anchor_top - 6.0, anchor_bottom + 6.0)
    ]
    vertical_pool = verticals_near_anchor_band or verticals

    left_candidates = [seg for seg in vertical_pool if float(seg.get("x0", 0.0)) <= anchor_x0 - 2.0]
    right_candidates = [seg for seg in vertical_pool if float(seg.get("x0", 0.0)) >= anchor_x1 + 2.0]

    left_border = max(left_candidates, key=lambda seg: float(seg.get("x0", 0.0)), default=None)
    right_border = min(right_candidates, key=lambda seg: float(seg.get("x0", 0.0)), default=None)

    return {
        "local_window": {"x0": local_x0, "x1": local_x1, "top": local_top, "bottom": local_bottom},
        "nearby_segments": local_segments,
        "horizontals": horizontals,
        "left_border": left_border,
        "right_border": right_border,
    }


def _select_horizontal_line(
    horiz_segments: list[dict],
    target_y: float,
    min_y: float | None,
    max_y: float | None,
    preferred_x0: float,
    preferred_x1: float,
    page_width: float,
):
    candidates: list[tuple[float, float, dict]] = []

    for seg in horiz_segments:
        y = float(seg.get("top", 0.0))
        if min_y is not None and y < min_y:
            continue
        if max_y is not None and y > max_y:
            continue

        sx0 = float(seg.get("x0", 0.0))
        sx1 = float(seg.get("x1", 0.0))
        overlap = max(0.0, min(sx1, preferred_x1) - max(sx0, preferred_x0))
        preferred_width = max(1.0, preferred_x1 - preferred_x0)
        coverage = overlap / preferred_width

        fullish_span_bonus = 0.0
        if sx0 <= preferred_x0 + 12.0 and sx1 >= preferred_x1 - 12.0:
            fullish_span_bonus = 0.75
        elif sx0 <= 8.0 and sx1 >= page_width - 8.0:
            fullish_span_bonus = 0.75

        score = abs(y - target_y) - (coverage * 25.0) - fullish_span_bonus
        candidates.append((score, abs(y - target_y), seg))

    if not candidates:
        return None

    _, _, best = min(candidates, key=lambda item: (item[0], item[1]))
    return best


def find_section_top_line(anchor, line_segments, page_width):
    anchor_top = float(anchor["top"])
    preferred_x0 = max(0.0, float(anchor["x0"]) - 260.0)
    preferred_x1 = min(float(page_width), float(anchor["x1"]) + 260.0)

    horizontals = [
        seg
        for seg in line_segments
        if seg.get("orientation") == "horizontal" and _segment_length(seg) >= 40.0
    ]

    best = _select_horizontal_line(
        horizontals,
        target_y=anchor_top,
        min_y=max(0.0, anchor_top - 60.0),
        max_y=anchor_top + 4.0,
        preferred_x0=preferred_x0,
        preferred_x1=preferred_x1,
        page_width=float(page_width),
    )

    if best is None:
        return None
    return float(best.get("top", 0.0))


def find_section_bottom_line(current_anchor, next_anchor, line_segments, page_width):
    if next_anchor is None:
        return None

    next_top = float(next_anchor["top"])
    preferred_x0 = max(0.0, float(next_anchor["x0"]) - 260.0)
    preferred_x1 = min(float(page_width), float(next_anchor["x1"]) + 260.0)

    horizontals = [
        seg
        for seg in line_segments
        if seg.get("orientation") == "horizontal" and _segment_length(seg) >= 40.0
    ]

    best = _select_horizontal_line(
        horizontals,
        target_y=next_top,
        min_y=max(0.0, float(current_anchor["bottom"]) - 5.0),
        max_y=next_top + 4.0,
        preferred_x0=preferred_x0,
        preferred_x1=preferred_x1,
        page_width=float(page_width),
    )

    if best is None:
        return None
    return float(best.get("top", 0.0))


def find_section_words(words, anchor, page_width, page_height, section_name, x0=None, x1=None):
    """Find section words for bottom estimation, constrained to section bounds when present."""
    if anchor is None:
        return []

    settings = get_section_settings(section_name)
    padding = settings["word_padding"]

    search_x0 = max(0.0, float(anchor["x0"]) - padding["left"]) if x0 is None else max(0.0, float(x0))
    search_x1 = (
        min(float(page_width), float(anchor["x1"]) + padding["right"])
        if x1 is None
        else min(float(page_width), float(x1))
    )
    search_top = max(0.0, float(anchor["top"]) - padding["top"])
    search_bottom = min(float(page_height), float(anchor["bottom"]) + padding["bottom"])

    return filter_words_between_xbounds(
        words,
        x0=search_x0,
        x1=search_x1,
        top=search_top,
        bottom=search_bottom,
    )


def build_section_bbox_from_lines(
    anchor,
    next_anchor,
    section_name,
    line_segments,
    words,
    page_width,
    page_height,
):
    """Build section bbox using divider lines and neighboring section anchors."""
    settings = get_section_settings(section_name)
    nearby = _find_nearby_table_lines(anchor, line_segments, page_width, page_height, section_name)

    left_border = nearby.get("left_border")
    right_border = nearby.get("right_border")

    left = float(left_border["x0"]) if left_border else max(0.0, float(anchor["x0"]) - 20.0)
    right = (
        float(right_border["x0"])
        if right_border
        else min(float(page_width), left + float(settings["fallback_width"]))
    )

    if right <= left:
        right = min(float(page_width), left + float(settings["fallback_width"]))

    top_line = find_section_top_line(anchor, line_segments, page_width)
    top = top_line if top_line is not None else max(0.0, float(anchor["top"]) - 12.0)

    bottom_line = find_section_bottom_line(anchor, next_anchor, line_segments, page_width)
    used_word_bottom = False
    if bottom_line is not None:
        bottom = bottom_line
    else:
        section_words = find_section_words(
            words,
            anchor,
            page_width,
            page_height,
            section_name,
            x0=left,
            x1=right,
        )

        words_below_heading = [w for w in section_words if float(w.get("top", 0.0)) >= float(anchor["bottom"]) - 2.0]
        words_for_bottom = words_below_heading if words_below_heading else section_words

        if words_for_bottom:
            content_bottom = max(float(w.get("bottom", 0.0)) for w in words_for_bottom)
            bottom = min(float(page_height), content_bottom + float(settings["bottom_padding"]))
            used_word_bottom = True
        else:
            bottom = min(float(page_height), float(anchor["bottom"]) + float(settings["fallback_bottom"]))
            used_word_bottom = True

    if bottom <= top:
        bottom = min(float(page_height), top + 120.0)

    bbox = (
        max(0.0, left),
        max(0.0, top),
        min(float(page_width), right),
        min(float(page_height), bottom),
    )

    debug_info = {
        "section_name": section_name,
        "nearby_line_segments_count": len(nearby.get("nearby_segments", [])),
        "local_window": nearby.get("local_window"),
        "chosen_boundaries": {
            "left": bbox[0],
            "right": bbox[2],
            "top": bbox[1],
            "bottom": bbox[3],
        },
        "left_border": left_border,
        "right_border": right_border,
        "top_line": top_line,
        "bottom_line": bottom_line,
        "used_word_bottom": used_word_bottom,
    }

    return bbox, debug_info


def crop_region(page, bbox):
    """Crop and return a page region using bbox=(x0, top, x1, bottom)."""
    return page.crop(bbox)


def save_cropped_image(cropped_page, output_path: str, resolution: int = 150):
    """Render and save a cropped page image to disk."""
    cropped_image = cropped_page.to_image(resolution=resolution)
    cropped_image.save(output_path)


def extract_crop_text(cropped_page) -> str:
    """Extract and safely normalize text from a cropped region."""
    text = cropped_page.extract_text()
    if text is None:
        return ""
    return text.strip()


# Backward-compatible wrappers for existing fixture flow.
def find_fixture_symbols_anchor(words):
    return find_section_anchor(words, "FIXTURE SYMBOLS")


def find_fixture_section_words(words, anchor, page_width, page_height, x0=None, x1=None):
    return find_section_words(words, anchor, page_width, page_height, "FIXTURE SYMBOLS", x0=x0, x1=x1)


def build_fixture_symbols_bbox_from_lines(anchor, line_segments, words, page_width, page_height):
    return build_section_bbox_from_lines(
        anchor,
        None,
        "FIXTURE SYMBOLS",
        line_segments,
        words,
        page_width,
        page_height,
    )
