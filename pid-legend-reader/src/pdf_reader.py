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
