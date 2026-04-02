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


def save_page_image(page, output_path: str, resolution: int = 150):
    """Render and save a page image to disk."""
    page_image = page.to_image(resolution=resolution)
    page_image.save(output_path)
