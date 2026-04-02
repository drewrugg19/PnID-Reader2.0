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
    """Find words likely belonging to the Fixture Symbols section below the heading."""
    if anchor is None:
        return []

    horizontal_margin = max(160.0, page_width * 0.2)
    search_x0 = max(0.0, float(anchor["x0"]) - horizontal_margin)
    search_x1 = min(float(page_width), float(anchor["x1"]) + horizontal_margin)

    search_top = min(float(page_height), float(anchor["bottom"]) + 5.0)
    vertical_depth = max(180.0, page_height * 0.35)
    search_bottom = min(float(page_height), search_top + vertical_depth)

    return filter_words_in_region(
        words,
        x0=search_x0,
        x1=search_x1,
        top=search_top,
        bottom=search_bottom,
    )


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
    """Build a dynamic bbox around Fixture Symbols using detected section words."""
    section_words = find_fixture_section_words(words, anchor, page_width, page_height)
    section_bbox = build_bbox_from_words(section_words, page_width, page_height, padding=20)
    if section_bbox is None:
        return None

    section_x0, section_top, section_x1, section_bottom = section_bbox

    x0 = min(section_x0, float(anchor["x0"]))
    top = min(section_top, float(anchor["top"]))
    x1 = max(section_x1, float(anchor["x1"]))
    bottom = max(section_bottom, float(anchor["bottom"]))

    extra_padding = 10.0
    x0 = max(0.0, x0 - extra_padding)
    top = max(0.0, top - extra_padding)
    x1 = min(float(page_width), x1 + extra_padding)
    bottom = min(float(page_height), bottom + extra_padding)

    return (x0, top, x1, bottom)


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
