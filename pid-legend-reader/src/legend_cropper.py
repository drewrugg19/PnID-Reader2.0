from __future__ import annotations

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


def _match_heading_from_tokens(words: list[dict], target_tokens: list[str]) -> dict | None:
    words_by_top = sorted(words, key=lambda word: (float(word.get("top", 0.0)), float(word.get("x0", 0.0))))

    for index in range(len(words_by_top) - len(target_tokens) + 1):
        group = words_by_top[index : index + len(target_tokens)]
        group_tokens = [str(item.get("text", "")).strip().upper() for item in group]

        if group_tokens != target_tokens:
            continue

        top_values = [float(item.get("top", 0.0)) for item in group]
        bottom_values = [float(item.get("bottom", 0.0)) for item in group]
        x0_values = [float(item.get("x0", 0.0)) for item in group]
        x1_values = [float(item.get("x1", 0.0)) for item in group]

        if max(top_values) - min(top_values) > 8.0:
            continue

        if any(
            float(group[idx + 1].get("x0", 0.0)) - float(group[idx].get("x1", 0.0)) > 240.0
            for idx in range(len(group) - 1)
        ):
            continue

        return {
            "x0": min(x0_values),
            "x1": max(x1_values),
            "top": min(top_values),
            "bottom": max(bottom_values),
        }

    return None


def find_section_anchor(words, target_text):
    """
    Find heading anchor coordinates for a section title.

    Supports:
    - full phrase in one word entry
    - nearby separate words forming the phrase
    """
    if not words:
        return None

    target = " ".join(target_text.strip().upper().split())
    if not target:
        return None

    for word in words:
        text = " ".join(str(word.get("text", "")).strip().upper().split())
        if text == target:
            return {
                "x0": float(word["x0"]),
                "top": float(word["top"]),
                "x1": float(word["x1"]),
                "bottom": float(word["bottom"]),
            }

    tokens = [part for part in target.split() if part]
    if not tokens:
        return None

    return _match_heading_from_tokens(words, tokens)


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

    top_candidates = [
        seg
        for seg in horizontals
        if float(seg.get("top", 0.0)) <= anchor_top + 2.0
        and float(seg.get("x0", 0.0)) <= anchor_x0 + 15.0
        and float(seg.get("x1", 0.0)) >= anchor_x1 - 15.0
    ]

    top_border = max(top_candidates, key=lambda seg: float(seg.get("top", 0.0)), default=None)

    return {
        "local_window": {"x0": local_x0, "x1": local_x1, "top": local_top, "bottom": local_bottom},
        "nearby_segments": local_segments,
        "left_border": left_border,
        "right_border": right_border,
        "top_border": top_border,
    }


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


def build_section_bbox_from_lines(anchor, section_name, line_segments, words, page_width, page_height):
    """Build section bbox using nearby table lines + local words for bottom estimation."""
    settings = get_section_settings(section_name)
    nearby = _find_nearby_table_lines(anchor, line_segments, page_width, page_height, section_name)

    left_border = nearby.get("left_border")
    right_border = nearby.get("right_border")
    top_border = nearby.get("top_border")

    left = float(left_border["x0"]) if left_border else max(0.0, float(anchor["x0"]) - 20.0)
    right = (
        float(right_border["x0"])
        if right_border
        else min(float(page_width), left + float(settings["fallback_width"]))
    )
    top = float(top_border["top"]) if top_border else max(0.0, float(anchor["top"]) - 12.0)

    if right <= left:
        right = min(float(page_width), left + float(settings["fallback_width"]))

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
    else:
        bottom = min(float(page_height), float(anchor["bottom"]) + float(settings["fallback_bottom"]))

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
        "top_border": top_border,
        "section_words_for_bottom_count": len(words_for_bottom),
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
        "FIXTURE SYMBOLS",
        line_segments,
        words,
        page_width,
        page_height,
    )
