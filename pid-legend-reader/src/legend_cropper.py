from __future__ import annotations

from pdf_reader import filter_words_in_region


def find_fixture_symbols_anchor(words):
    """
    Find heading anchor coordinates for 'FIXTURE SYMBOLS'.

    Supports:
    - single-word entry equal to 'FIXTURE SYMBOLS'
    - two nearby words: 'FIXTURE' followed by 'SYMBOLS'
    """
    if not words:
        return None

    for word in words:
        text = str(word.get("text", "")).strip().upper()
        if text == "FIXTURE SYMBOLS":
            return {
                "x0": float(word["x0"]),
                "top": float(word["top"]),
                "x1": float(word["x1"]),
                "bottom": float(word["bottom"]),
            }

    fixtures = [
        word for word in words if str(word.get("text", "")).strip().upper() == "FIXTURE"
    ]
    symbols = [
        word for word in words if str(word.get("text", "")).strip().upper() == "SYMBOLS"
    ]

    for fixture in fixtures:
        fx0 = float(fixture["x0"])
        ftop = float(fixture["top"])
        fx1 = float(fixture["x1"])
        fbottom = float(fixture["bottom"])

        for symbol in symbols:
            sx0 = float(symbol["x0"])
            stop = float(symbol["top"])
            sx1 = float(symbol["x1"])
            sbottom = float(symbol["bottom"])

            vertical_overlap = not (sbottom < ftop or stop > fbottom)
            horizontal_gap = sx0 - fx1

            if vertical_overlap and 0 <= horizontal_gap <= 200:
                return {
                    "x0": min(fx0, sx0),
                    "top": min(ftop, stop),
                    "x1": max(fx1, sx1),
                    "bottom": max(fbottom, sbottom),
                }

    return None


def find_fixture_section_words(words, anchor, page_width, page_height):
    """Find words in a tight local window around the Fixture Symbols heading anchor."""
    if anchor is None:
        return []

    search_x0 = max(0.0, float(anchor["x0"]) - 450.0)
    search_x1 = min(float(page_width), float(anchor["x1"]) + 550.0)
    search_top = max(0.0, float(anchor["top"]) - 40.0)
    search_bottom = min(float(page_height), float(anchor["bottom"]) + 700.0)

    return filter_words_in_region(
        words,
        x0=search_x0,
        x1=search_x1,
        top=search_top,
        bottom=search_bottom,
    )


def filter_out_heading_words(section_words, anchor):
    """Remove words that overlap the heading area to avoid double-counting heading text."""
    if not section_words or anchor is None:
        return section_words

    heading_top = float(anchor["top"]) - 2.0
    heading_bottom = float(anchor["bottom"]) + 2.0

    filtered = []
    for word in section_words:
        word_top = float(word["top"])
        word_bottom = float(word["bottom"])

        overlaps_heading_band = not (word_bottom < heading_top or word_top > heading_bottom)
        if not overlaps_heading_band:
            filtered.append(word)

    return filtered


def build_bbox_from_words(section_words, page_width, page_height, padding=20):
    """Build a padded bbox from the provided section words."""
    if not section_words:
        return None

    min_x0 = min(float(word["x0"]) for word in section_words)
    max_x1 = max(float(word["x1"]) for word in section_words)
    min_top = min(float(word["top"]) for word in section_words)
    max_bottom = max(float(word["bottom"]) for word in section_words)

    x0 = max(0.0, min_x0 - padding)
    top = max(0.0, min_top - padding)
    x1 = min(float(page_width), max_x1 + padding)
    bottom = min(float(page_height), max_bottom + padding)

    return (x0, top, x1, bottom)


def build_fixture_symbols_bbox(anchor, words, page_width, page_height):
    """Build a dynamic bbox around Fixture Symbols from local anchor-based words."""
    local_words = find_fixture_section_words(words, anchor, page_width, page_height)
    content_words = filter_out_heading_words(local_words, anchor)

    words_for_bbox = content_words if content_words else local_words
    section_bbox = build_bbox_from_words(words_for_bbox, page_width, page_height, padding=12)

    if section_bbox is None:
        heading_only_bbox = build_bbox_from_words([anchor], page_width, page_height, padding=8)
        return heading_only_bbox, []

    section_x0, section_top, section_x1, section_bottom = section_bbox

    x0 = min(section_x0, float(anchor["x0"]))
    top = min(section_top, float(anchor["top"]))
    x1 = max(section_x1, float(anchor["x1"]))
    bottom = max(section_bottom, float(anchor["bottom"]))

    modest_padding = 8.0
    x0 = max(0.0, x0 - modest_padding)
    top = max(0.0, top - modest_padding)
    x1 = min(float(page_width), x1 + modest_padding)
    bottom = min(float(page_height), bottom + modest_padding)

    return (x0, top, x1, bottom), words_for_bbox


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
