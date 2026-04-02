from __future__ import annotations


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


def build_fixture_symbols_bbox(anchor, page_width, page_height):
    """Build a dynamic crop bbox around the fixture symbols heading."""
    if anchor is None:
        return None

    x0 = max(0, anchor["x0"] - 40)
    top = max(0, anchor["top"] - 20)
    x1 = min(page_width, anchor["x1"] + 260)
    bottom = min(page_height, anchor["bottom"] + (page_height * 0.35))

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
