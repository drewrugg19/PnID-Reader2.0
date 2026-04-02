from __future__ import annotations

from pathlib import Path

import pdfplumber


def open_pdf(path: str):
    """Open and return a PDF document."""
    return pdfplumber.open(str(Path(path)))


def get_page(pdf, index: int):
    """Return a page by index from an open PDF."""
    return pdf.pages[index]


def extract_text(page) -> str:
    """Extract text from a PDF page."""
    return page.extract_text() or ""


def extract_words(page) -> list[dict]:
    """Extract word-level entries from a PDF page."""
    return page.extract_words() or []


def extract_lines(page) -> list[dict]:
    """Extract line objects from a PDF page."""
    return page.lines or []


def extract_rects(page) -> list[dict]:
    """Extract rectangle objects from a PDF page."""
    return page.rects or []


def _normalize_segment(x0: float, x1: float, top: float, bottom: float) -> dict | None:
    width = abs(float(x1) - float(x0))
    height = abs(float(bottom) - float(top))

    if width < 0.01 and height < 0.01:
        return None

    orientation = "horizontal" if width >= height else "vertical"
    return {
        "x0": min(float(x0), float(x1)),
        "x1": max(float(x0), float(x1)),
        "top": min(float(top), float(bottom)),
        "bottom": max(float(top), float(bottom)),
        "orientation": orientation,
    }


def combine_line_like_objects(page) -> list[dict]:
    """Combine page lines and rectangle edges into normalized line-like segments."""
    segments: list[dict] = []

    for line in extract_lines(page):
        segment = _normalize_segment(
            line.get("x0", 0.0),
            line.get("x1", 0.0),
            line.get("top", 0.0),
            line.get("bottom", 0.0),
        )
        if segment is not None:
            segments.append(segment)

    for rect in extract_rects(page):
        x0 = float(rect.get("x0", 0.0))
        x1 = float(rect.get("x1", 0.0))
        top = float(rect.get("top", 0.0))
        bottom = float(rect.get("bottom", 0.0))

        rect_edges = [
            _normalize_segment(x0, x1, top, top),
            _normalize_segment(x0, x1, bottom, bottom),
            _normalize_segment(x0, x0, top, bottom),
            _normalize_segment(x1, x1, top, bottom),
        ]

        for edge in rect_edges:
            if edge is not None:
                segments.append(edge)

    return segments


def filter_words_in_region(
    words: list[dict],
    x0: float | None = None,
    x1: float | None = None,
    top: float | None = None,
    bottom: float | None = None,
) -> list[dict]:
    """Return words whose bounds are fully inside the provided region limits."""
    filtered: list[dict] = []

    for word in words:
        wx0 = float(word.get("x0", 0.0))
        wx1 = float(word.get("x1", 0.0))
        wtop = float(word.get("top", 0.0))
        wbottom = float(word.get("bottom", 0.0))

        if x0 is not None and wx0 < x0:
            continue
        if x1 is not None and wx1 > x1:
            continue
        if top is not None and wtop < top:
            continue
        if bottom is not None and wbottom > bottom:
            continue

        filtered.append(word)

    return filtered


def find_heading_words(words: list[dict], target_text: str) -> list[dict]:
    """
    Find words matching a target heading case-insensitively.

    Supports matching the exact combined phrase and individual target words.
    """
    target = target_text.strip().upper()
    target_parts = {part for part in target.split() if part}

    matches: list[dict] = []
    for word in words:
        text = str(word.get("text", "")).strip()
        if not text:
            continue

        upper_text = text.upper()
        if upper_text == target or upper_text in target_parts:
            matches.append(word)

    return matches


def save_page_image(page, output_path: str, resolution: int = 150):
    """Render and save a page image to disk."""
    page_image = page.to_image(resolution=resolution)
    page_image.save(output_path)
